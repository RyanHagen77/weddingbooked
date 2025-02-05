// contractsHelpers.js

/**
 * Retrieves the CSRF token (or any cookie value) by name.
 * @param {string} name - The name of the cookie.
 * @returns {string|null} - The cookie value, or null if not found.
 */
export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}