import React, { forwardRef } from 'react';
import './Page.css';

const Page = forwardRef(({ pageData }, ref) => {
    const [imageUrl, setImageUrl] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    React.useEffect(() => {
        if (pageData.type === 'image' && pageData.textForPrompt && !imageUrl) {
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
    }, [pageData]);

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
                                <button onClick={() => setImageUrl(null)} className="retry-btn">Try Again</button>
                            </div>
                        )}
                        {imageUrl && !loading && (
                            <img src={imageUrl} alt="AI Generated visualization" className="generated-image" />
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
