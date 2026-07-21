import React, { useState, useEffect } from 'react';
import { fetchMapData, submitProduct } from './api';

function App() {
  const [product, setProduct] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load map from API call
    fetchMapData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!product.trim()) return;
    
    setLoading(true);
    await submitProduct(product);
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
          <div className="map-placeholder">
            <div className="pulse-ring"></div>
            <p>Interactive Map Loading...</p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
