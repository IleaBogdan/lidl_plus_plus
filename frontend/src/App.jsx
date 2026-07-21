import React, { useState, useEffect } from 'react';
import { fetchMapData, submitProduct } from './api';

function App() {
  const [product, setProduct] = useState('');
  const [loading, setLoading] = useState(false);
  const [mapUrl, setMapUrl] = useState(null);

  useEffect(() => {
    // Optionally load an initial map from API call if needed later
    // fetchMapData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!product.trim()) return;

    setLoading(true);
    try {
      const data = await submitProduct(product);
      // Expecting the backend to return the map image URL or base64 data in `map_url`
      if (data && data.map_url) {
        // The backend returns raw base64, so we need to add the data URI prefix
        // so the browser knows it's an image and doesn't try to fetch it as a URL
        const imageSrc = data.map_url.startsWith('data:image') 
          ? data.map_url 
          : `data:image/png;base64,${data.map_url}`;
        setMapUrl(imageSrc);
      }
    } catch (error) {
      console.error("Failed to submit product", error);
    }
    
    setLoading(false);
    setProduct('');
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Store Explorer</h1>
        <p>Find products across the store map</p>
      </header>

      <main className="main-content">
        <form className="search-form" onSubmit={handleSubmit}>
          <div className="input-group">
            <input
              type="text"
              placeholder="Type a product name..."
              value={product}
              onChange={(e) => setProduct(e.target.value)}
              className="search-input"
            />
            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Submitting...' : 'Find Product'}
            </button>
          </div>
        </form>

        <div className="map-container">
          {mapUrl ? (
             <img 
               src={mapUrl} 
               alt="Store map with product location" 
               style={{ width: '100%', height: '100%', objectFit: 'contain', zIndex: 1 }} 
             />
          ) : (
            <div className="map-placeholder">
              <div className="pulse-ring"></div>
              <p>Type a product to load the map...</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
