import React, { useState } from 'react';
import { submitProducts } from './api';
import mapsIds from './maps_ids.json';
import { PRODUCTS } from './products';

function App() {
  const [screen, setScreen] = useState('select'); // 'select' | 'result'
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [selectedMapId, setSelectedMapId] = useState(mapsIds[0].id);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [aisleLengths, setAisleLengths] = useState([]);
  const [aisles, setAisles] = useState([]);

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
        setAisleLengths(data.aisle_lengths || []);
        setAisles(data.aisles || []);
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

          <div className="aisles-container">
            {aisleLengths.map((capacity, aisleIndex) => {
              const aisleProducts = aisles[aisleIndex] || [];
              return (
                <div className="aisle" key={aisleIndex}>
                  <div className="aisle-label">Aisle {aisleIndex + 1}</div>
                  <div className="aisle-blocks">
                    {Array.from({ length: capacity }).map((_, slotIndex) => {
                      const productName = aisleProducts[slotIndex];
                      return (
                        <div
                          key={slotIndex}
                          className={`aisle-block${productName ? '' : ' empty'}`}
                        >
                          {productName || ''}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
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
              >
                {name}
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
