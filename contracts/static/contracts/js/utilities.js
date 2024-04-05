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

