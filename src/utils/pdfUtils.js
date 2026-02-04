import * as pdfjsLib from 'pdfjs-dist';

// Configure PDF.js worker - using local copy served by Vite
pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

/**
 * Extract all text from a PDF file along with metadata
 * @param {File} file - The PDF file to extract text from
 * @returns {Promise<{text: string, title: string}>} - Text content and book title
 */
export async function extractTextFromPDF(file) {
    try {
        // Convert file to ArrayBuffer
        const arrayBuffer = await file.arrayBuffer();

        // Load the PDF document
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

        let fullText = '';
        let bookTitle = '';

        // Extract text from each page
        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
            const page = await pdf.getPage(pageNum);
            const textContent = await page.getTextContent();

            // Sort items by Y position (top to bottom) then X position (left to right)
            const items = textContent.items.sort((a, b) => {
                const yDiff = b.transform[5] - a.transform[5]; // Y position (inverted, higher Y = top)
                if (Math.abs(yDiff) > 1) return yDiff;
                return a.transform[4] - b.transform[4]; // X position
            });

            // Group items by line based on Y position
            const lines = [];
            let currentLine = [];
            let currentY = null;
            let lastY = null;

            for (const item of items) {
                const itemY = item.transform[5];
                const itemText = item.str || '';

                // Check if we're on a new line (Y position changed significantly)
                if (currentY === null || Math.abs(itemY - currentY) > 1) {
                    // Save previous line if it exists
                    if (currentLine.length > 0) {
                        const lineText = currentLine.join('').trim();
                        if (lineText) {
                            lines.push(lineText);
                        }
                    }

                    // Add empty lines for large gaps (paragraph breaks)
                    if (lastY !== null && Math.abs(itemY - lastY) > 15) {
                        lines.push(''); // Add blank line for paragraph spacing
                    }

                    currentLine = [];
                    lastY = currentY;
                    currentY = itemY;
                }

                // Add text to current line, preserving spaces
                if (itemText) {
                    // Check if we need to add a space before this item
                    if (currentLine.length > 0) {
                        const lastItem = currentLine[currentLine.length - 1];
                        const needsSpace = lastItem && !lastItem.endsWith(' ') && !itemText.startsWith(' ');
                        if (needsSpace && itemText.trim()) {
                            currentLine.push(' ');
                        }
                    }
                    currentLine.push(itemText);
                }
            }

            // Add last line
            if (currentLine.length > 0) {
                const lineText = currentLine.join('').trim();
                if (lineText) {
                    lines.push(lineText);
                }
            }

            // Join lines and add page separator
            const pageText = lines.join('\n');
            fullText += pageText + '\n\n';

            // Try to extract book title from first page
            if (pageNum === 1 && !bookTitle) {
                const firstLine = lines[0];
                if (firstLine && firstLine.length > 0 && firstLine.length < 100) {
                    bookTitle = firstLine.trim();
                }
            }
        }

        // If no title found, use filename
        if (!bookTitle) {
            bookTitle = file.name.replace('.pdf', '');
        }

        return { text: fullText.trim(), title: bookTitle };
    } catch (error) {
        console.error('Error extracting text from PDF:', error);
        throw new Error('Failed to extract text from PDF. Please try another file.');
    }
}

/**
 * Split text into pages with chapter detection
 * @param {string} text - The full text to split
 * @param {number} linesPerPage - Minimum lines per page (default: 10)
 * @returns {Array} - Array of page objects with text and chapter info
 */
export function splitTextIntoPages(text, linesPerPage = 20) {
    // Split text into lines (preserve all lines, including empty ones)
    let lines = text.split('\n');

    console.log('=== PDF TEXT PROCESSING ===');
    console.log('Total lines extracted:', lines.length);
    console.log('Lines per page setting:', linesPerPage);
    console.log('First 5 lines:', lines.slice(0, 5));
    console.log('Last 5 lines:', lines.slice(-5));

    const pages = [];
    let currentPage = [];
    let currentChapter = '';
    let hasFoundFirstChapter = false; // Track if we've found the first chapter/prologue

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        let trimmedLine = line.trim();

        // Check if line contains "CHAPTER" or "PROLOGUE" to mark start
        if (trimmedLine.match(/CHAPTER|PROLOGUE/i)) {
            const chapterMatch = trimmedLine.match(/(CHAPTER|PROLOGUE)(\s+.+)?/i);
            if (chapterMatch) {
                hasFoundFirstChapter = true;

                // Save current page before starting new chapter
                if (currentPage.length > 0) {
                    pages.push({
                        content: currentPage.join('\n'),
                        chapter: currentChapter
                    });
                    currentPage = [];
                }

                currentChapter = chapterMatch[0].trim();
                continue; // Skip the chapter line itself
            }
        }

        // Skip all content before the first chapter/prologue
        if (!hasFoundFirstChapter) {
            continue;
        }

        // Add ALL lines to current page (including empty ones for spacing)
        currentPage.push(line);

        // Create new page when we reach target lines
        if (currentPage.length >= linesPerPage) {
            pages.push({
                content: currentPage.join('\n'),
                chapter: currentChapter
            });
            currentPage = [];
        }
    }

    // Add remaining lines
    if (currentPage.length > 0) {
        pages.push({
            content: currentPage.join('\n'),
            chapter: currentChapter
        });
    }

    console.log('Total pages created:', pages.length);
    console.log('Total lines in all pages:', pages.reduce((sum, p) => sum + p.content.split('\n').length, 0));
    if (pages.length > 0) {
        console.log('First page:', {
            chapter: pages[0].chapter,
            lineCount: pages[0].content.split('\n').length,
            contentPreview: pages[0].content.substring(0, 200) + '...'
        });
        console.log('Last page:', {
            chapter: pages[pages.length - 1].chapter,
            lineCount: pages[pages.length - 1].content.split('\n').length,
            contentPreview: pages[pages.length - 1].content.substring(0, 200) + '...'
        });
    }

    return pages;
}

/**
 * Format text pages for the flip-book
 * Creates alternating text and image placeholder pages
 * @param {Array} textPages - Array of page objects with content and chapter
 * @returns {Array} - Array of page objects for the flip-book
 */
export function formatPagesForFlipBook(textPages) {
    const flipBookPages = [];
    let pageId = 1;

    for (const pageData of textPages) {
        // Add text page (left page)
        flipBookPages.push({
            id: pageId++,
            type: 'text',
            content: pageData.content,
            chapter: pageData.chapter
        });

        // Add image placeholder (right page)
        flipBookPages.push({
            id: pageId++,
            type: 'image',
            content: null,
            chapter: pageData.chapter
        });
    }

    return flipBookPages;
}

/**
 * Process a PDF file and return formatted pages for the flip-book
 * @param {File} pdfFile - The PDF file to process
 * @param {number} linesPerPage - Lines per page (default: 10)
 * @returns {Promise<{pages: Array, title: string}>} - Formatted pages and book title
 */
export async function processPDFForFlipBook(pdfFile, linesPerPage = 20) {
    // Extract text and title from PDF
    const { text: fullText, title } = await extractTextFromPDF(pdfFile);

    // Split into pages with chapter detection
    const textPages = splitTextIntoPages(fullText, linesPerPage);

    // Format for flip-book (alternating text/image)
    const flipBookPages = formatPagesForFlipBook(textPages);

    return { pages: flipBookPages, title };
}
