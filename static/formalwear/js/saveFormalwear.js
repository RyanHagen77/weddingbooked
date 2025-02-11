import { getCookie } from '../../utilities.js'; // Adjust the path as needed

export function saveFormalwear(contractId, formalwearItems) {
  const csrfToken = getCookie('csrftoken');  // Retrieve the CSRF token here
  return fetch(`/formalwear/${contractId}/save_formalwear/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
      formalwear_items: formalwearItems
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  })
  .then(data => {
      console.log('Server-side formalwear updated successfully:', data);
      // Use a full redirect with a cache-buster
      window.location.href = window.location.href.split('?')[0] + '?_=' + new Date().getTime();
      return data;
  })
  .catch(error => {
    console.error('Error updating server-side formalwear:', error);
    throw error;
  });
}
