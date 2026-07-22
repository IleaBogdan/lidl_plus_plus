const url = "localhost:6969";

export const fetchMapData = async () => {
  // Random function that returns nothing
};

export const submitProduct = async (productName, mapId) => {
  try {
    const formData = new FormData();
    // Appending the product as a form field since the backend expects request.form
    formData.append('product', productName);
    formData.append('mapId', mapId);

    const response = await fetch(`http://${url}/submit`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Product submitted successfully:', data);
    return data;
  } catch (error) {
    console.error('Error submitting product:', error);
    throw error;
  }
};
