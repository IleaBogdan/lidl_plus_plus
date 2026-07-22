const url = "localhost:6969";

export const submitProducts = async (products, mapId) => {
  try {
    const formData = new FormData();
    // Appending the products as a comma-separated form field since the backend expects request.form
    formData.append('product', products.join(','));
    formData.append('mapId', mapId);

    const response = await fetch(`http://${url}/submit`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Products submitted successfully:', data);
    return data;
  } catch (error) {
    console.error('Error submitting products:', error);
    throw error;
  }
};
