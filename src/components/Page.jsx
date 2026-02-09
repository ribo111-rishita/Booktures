import React, { forwardRef } from 'react';
import './Page.css';

const Page = forwardRef(({ pageData, pageIndex, currentPage }, ref) => {
    const [imageUrl, setImageUrl] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    React.useEffect(() => {
        // Lazy load: only fetch if within 2 pages of current
        const isNear = Math.abs(pageIndex - currentPage) <= 2;

        if (pageData.type === 'image' && pageData.textForPrompt && !imageUrl && isNear) {
            const fetchImage = async () => {
                setLoading(true);
                setError(null);
                try {
                    const response = await fetch('http://localhost:8000/generate-image', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ prompt: pageData.textForPrompt }),
                    });

                    if (!response.ok) {
                        throw new Error('Failed to generate image');
                    }

                    const data = await response.json();
                    if (data.imageUrl) {
                        setImageUrl(data.imageUrl);
                    } else {
                        throw new Error('No image URL received');
                    }
                } catch (err) {
                    console.error('Error fetching image:', err);
                    setError(err.message || 'Failed to load image');
                } finally {
                    setLoading(false);
                }
            };

            fetchImage();
        }
    }, [pageData, pageIndex, currentPage]);

    return (
        <div className="page" ref={ref}>
            <div className="page-content">
                {pageData.type === 'text' ? (
                    <>
                        {pageData.chapter && (
                            <div className="chapter-header">
                                {pageData.chapter}
                            </div>
                        )}
                        <div className="page-text">
                            {pageData.content}
                        </div>
                    </>
                ) : (
                    <div className="page-image-container">
                        {loading && (
                            <div className="loading-state">
                                <div className="spinner"></div>
                                <p>Conjuring image...</p>
                            </div>
                        )}
                        {error && !loading && (
                            <div className="error-state">
                                <p>✨ Magic fizzled out</p>
                                <p style={{ fontSize: '10px', color: 'red', maxWidth: '100%', wordBreak: 'break-word', padding: '0 10px' }}>
                                    {error ? error.toString() : 'Unknown error'}
                                </p>
                                <button onClick={() => setImageUrl(null)} className="retry-btn">Try Again</button>
                            </div>
                        )}
                        {imageUrl && !loading && (
                            <>
                                <img
                                    src={imageUrl}
                                    alt="AI Generated visualization"
                                    className="generated-image"
                                    onError={(e) => {
                                        console.error("Image failed to load:", imageUrl);
                                        setError(`Image failed to load: ${imageUrl}`);
                                        setImageUrl(null);
                                    }}
                                    referrerPolicy="no-referrer"
                                />
                                <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, fontSize: '8px', color: '#ccc', background: 'rgba(0,0,0,0.5)', padding: '2px' }}>
                                    Debug URL: {imageUrl.substring(0, 50)}...
                                </div>
                            </>
                        )}
                        {!imageUrl && !loading && !error && (
                            <div className="placeholder-box">
                                <span className="placeholder-text">Image will appear here</span>
                            </div>
                        )}
                    </div>
                )}
            </div>
            <div className="page-number">{pageData.id}</div>
        </div>
    );
});

Page.displayName = 'Page';

export default Page;
