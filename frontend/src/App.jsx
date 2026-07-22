import React, { useState } from 'react';
import { submitProducts } from './api';
import mapsIds from './maps_ids.json';
import { PRODUCTS } from './products';
import { PRODUCT_ICONS } from './productIcons';

function App() {
  const [screen, setScreen] = useState('select'); // 'select' | 'result'
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [selectedMapId, setSelectedMapId] = useState(mapsIds[0].id);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mapBase64, setMapBase64] = useState(null);

  const toggleProduct = (name) => {
    setSelectedProducts((prev) =>
      prev.includes(name) ? prev.filter((p) => p !== name) : [...prev, name]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedProducts.length === 0) return;

    setLoading(true);
    setError(null);
    try {
      const data = await submitProducts(selectedProducts, selectedMapId);
      if (data.status === 'success') {
        setMapBase64(data.map_base64);
        setScreen('result');
      } else {
        setError(data.message || 'Submission failed');
      }
    } catch (err) {
      console.error('Failed to submit products', err);
      setError('Failed to reach the backend');
    }
    setLoading(false);
  };

  if (screen === 'result') {
    return (
      <div className="app-container">
        <header className="header">
          <h1>Lidl++</h1>
          <p>Optimal aisle arrangement</p>
        </header>

        <main className="main-content">
          <button className="back-btn" onClick={() => setScreen('select')}>
            &larr; Back
          </button>

          <div className="map-container" style={{ display: 'flex', justifyContent: 'center', marginTop: '2rem' }}>
            {mapBase64 ? (
              <img 
                src={`data:image/png;base64,${mapBase64}`} 
                alt="Store Map" 
                style={{ maxWidth: '100%', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }} 
              />
            ) : (
              <p>No map generated</p>
            )}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app-container" style={{ position: 'relative' }}>
      <div style={{ position: 'absolute', top: '2rem', right: '2rem', zIndex: 10 }}>
        <select
          className="search-input"
          style={{
            width: 'auto',
            minWidth: '120px',
            cursor: 'pointer',
            borderRadius: '999px',
            background: 'var(--card-bg)',
            border: '1px solid var(--border-color)',
            backdropFilter: 'blur(12px)',
            padding: '0.5rem 1rem'
          }}
          value={selectedMapId}
          onChange={(e) => setSelectedMapId(Number(e.target.value))}
        >
          {mapsIds.map((map) => (
            <option key={map.id} value={map.id} style={{ background: 'var(--bg-color)' }}>
              {map.name}
            </option>
          ))}
        </select>
      </div>

      <header className="header">
        <h1>Lidl++</h1>
        <p>Select the products for this order</p>
      </header>

      <main className="main-content">
        <form className="product-form" onSubmit={handleSubmit}>
          <div className="product-grid">
              {PRODUCTS.map((name) => (
              <button
                type="button"
                key={name}
                className={`product-chip${selectedProducts.includes(name) ? ' selected' : ''}`}
                onClick={() => toggleProduct(name)}
                title={name}
              >
                <span className="product-icon">{PRODUCT_ICONS[name]}</span>
                <span className="product-label">{name}</span>
              </button>
            ))}
          </div>

          {error && <p className="error-text">{error}</p>}

          <button
            type="submit"
            className="submit-btn"
            disabled={loading || selectedProducts.length === 0}
          >
            {loading
              ? 'Submitting...'
              : `Submit ${selectedProducts.length} product${selectedProducts.length === 1 ? '' : 's'}`}
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;
