import React, { useState, useEffect, useCallback } from 'react';
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
  const [zoom, setZoom] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);

  const zoomIn = () => setZoom(z => Math.min(z + 0.25, 5));
  const zoomOut = () => setZoom(z => Math.max(z - 0.25, 0.25));

  const handleKeyDown = useCallback((e) => {
    const step = 40;
    switch (e.key) {
      case 'w': case 'W': case 'ArrowUp':    setPanY(p => p + step); break;
      case 's': case 'S': case 'ArrowDown':  setPanY(p => p - step); break;
      case 'a': case 'A': case 'ArrowLeft':  setPanX(p => p + step); break;
      case 'd': case 'D': case 'ArrowRight': setPanX(p => p - step); break;
    }
  }, []);

  useEffect(() => {
    if (screen !== 'result') return;
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [screen, handleKeyDown]);

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
    const handleWheel = (e) => {
      e.preventDefault();
      setZoom(z => {
        const delta = e.deltaY > 0 ? -0.25 : 0.25;
        return Math.min(Math.max(z + delta, 0.25), 5);
      });
    };

    const resetView = () => {
      setZoom(1);
      setPanX(0);
      setPanY(0);
    };

    return (
      <div className="app-container">
        <header className="header">
          <h1>Lidl++</h1>
          <p>Optimal aisle arrangement</p>
        </header>

        <main className="main-content">
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', width: '100%' }}>
            <button className="back-btn" onClick={() => setScreen('select')}>
              &larr; Back
            </button>
            <div className="zoom-controls">
              <button className="zoom-btn" onClick={zoomOut} title="Zoom out">−</button>
              <span className="zoom-label">{Math.round(zoom * 100)}%</span>
              <button className="zoom-btn" onClick={zoomIn} title="Zoom in">+</button>
              <button className="zoom-btn zoom-reset" onClick={resetView} title="Reset view">⟲</button>
            </div>
          </div>

          <div className="map-container" onWheel={handleWheel}>
            {mapBase64 ? (
              <div className="map-scroll">
                <img
                  src={`data:image/png;base64,${mapBase64}`}
                  alt="Store Map"
                  className="map-image"
                  style={{ transform: `translate(${panX}px, ${panY}px) scale(${zoom})` }}
                />
              </div>
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
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', justifyContent: 'center' }}>
            <button 
              type="button" 
              className="action-btn" 
              style={{ background: 'var(--card-bg)', color: 'var(--text-color)', border: '1px solid var(--border-color)', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer', flex: 1, maxWidth: '150px' }}
              onClick={() => setSelectedProducts([...PRODUCTS])}
            >
              Select All
            </button>
            <button 
              type="button" 
              className="action-btn" 
              style={{ background: 'var(--card-bg)', color: 'var(--text-color)', border: '1px solid var(--border-color)', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer', flex: 1, maxWidth: '150px' }}
              onClick={() => setSelectedProducts([])}
            >
              Clear All
            </button>
          </div>
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
