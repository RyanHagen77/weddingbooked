// formalwear/fetchFormalwear.js
export function fetchFormalwearProducts() {
  return fetch('/formalwear/api/formalwear_products/')
    .then(response => {
      if (!response.ok) {
        throw new Error("Network response was not ok " + response.statusText);
      }
      return response.json();
    })
    .then(data => {
      window.globalFormalwearProducts = data;
      console.log('Fetched formalwear products:', data);
      return data;
    })
    .catch(error => console.error('Error fetching formalwear products:', error));
}
