// Initial console log
console.log("utilities.js loaded and executed!");

export function extractPrice(text) {
    const match = text.match(/\$(\d+(\.\d+)?)/);
    return match ? parseFloat(match[1]) : 0;
}

export var contractData = {
    additionalProductCosts: 0,
    taxAmount: 0,
    packageCost: 0,
    additionalStaffCost: 0,
    overtimeCost: 0,
    totalDiscount: 0,
    servicesTotalAfterDiscounts: 0, // Add this line
    totalContractAmount: 0, // Add this line
    paymentScheduleId: null, // Add this if needed for payment schedule
    // Add any other properties you need
};

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