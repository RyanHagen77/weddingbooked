import {extractPrice, contractData} from '/static/contracts/js/utilities.js';
// Make the function available globally

// Initial console log and global variables
console.log("costManagement.js loaded and executed!");

const eventDateElement = document.getElementById('id_event_date');
if (eventDateElement) {
    eventDateElement.addEventListener('change', updateTotalDiscountField);
}

// Global variable to store the event date
let eventDate = null;

// Function to get and update the event date
function updateEventDate() {
    const eventDateElement = document.getElementById('id_event_date');
    if (eventDateElement) {
        eventDate = new Date(eventDateElement.value);
    } else {
        console.error('Event date element not found.');
    }
}

// Call this function to initialize the event date when the script loads
updateEventDate();

function isSundayEvent(eventDate) {
    const date = moment(eventDate);
    return date.day() === 0; // 0 corresponds to Sunday
}

function calculatePackageDiscounts() {
    let selectedServices = [];
    let isPhotoboothSelected = false;
    const eventDate = document.getElementById('id_event_date').value;

    const packageDropdowns = {
        'photography': 'id_photography_package',
        'videography': 'id_videography_package',
        'dj': 'id_dj_package',
        'photobooth': 'id_photobooth_package'
    };

    // Check which packages are selected
    for (const type in packageDropdowns) {
        const selectElement = document.getElementById(packageDropdowns[type]);
        if (selectElement && selectElement.value) {
            if (type === 'photobooth') {
                isPhotoboothSelected = true;
            } else {
                selectedServices.push(type);
            }
        }
    }

    let discount = 0;

    // Apply Photobooth logic
    if (isPhotoboothSelected) {
        if (selectedServices.length >= 2) {
            // Apply $200 discount for each service including Photobooth
            discount += 200 * (selectedServices.length + 1);
        } else if (selectedServices.length === 1) {
            // Apply $200 discount only to the one other selected service
            discount += 200;
        }
    } else {
        // Apply $200 discount if at least two different types of non-Photobooth packages are selected
        if (selectedServices.length >= 2) {
            discount += 200 * selectedServices.length;
        }
    }

    // Apply Sunday discount
    if (isSundayEvent(eventDate)) {
        discount += 100 * (selectedServices.length + (isPhotoboothSelected ? 1 : 0));
    }

    return discount;
}
function updateTotalDiscountField() {
    // Make sure the event date is up-to-date
    updateEventDate();

    // Calculate package discount, assuming this function is defined and uses the eventDate variable
    let packageDiscount = calculatePackageDiscounts(); // This should use the eventDate

    // Calculate other discounts based on a selected option
    let otherDiscount = 0;
    const otherDiscountElement = document.getElementById('id_other_discounts');
    if (otherDiscountElement) {
        otherDiscount = getDiscountAmountFromOption(otherDiscountElement);
    }

    // Total discount is the sum of package discount and other discounts
    totalDiscount = packageDiscount + otherDiscount;

    // Update the hidden discount field value
    const discountField = document.getElementById('discount');
    if (discountField) {
        discountField.value = totalDiscount.toFixed(2);
    } else {
        console.error('Discount field not found.');
        // If the discount field is not found, log an error or handle accordingly
    }

    // Update contract data and total cost, assuming these functions are defined
    updateContractData();
    calculateAndUpdateTotalCost();
}

// Helper function to get the discount amount from a select option
function getDiscountAmountFromOption(selectElement) {
    if (!selectElement) return 0;

    const selectedOption = selectElement.options[selectElement.selectedIndex];
    if (!selectedOption || selectedOption.value === "") return 0;

    const matches = selectedOption.text.match(/\$([0-9]+(\.[0-9]+)?)/);
    return matches ? parseFloat(matches[1]) : 0;
}


// Attach event listeners once the DOM is fully loaded
document.addEventListener("DOMContentLoaded", () => {


    // Update total discount field on page load
    updateTotalDiscountField();
    updateTotalServiceCostDisplay(); // Assuming you want to update this as well


    // Attach event listener for the photography package dropdown
    const photographyPackageDropdown = document.getElementById('id_photography_package');
    if (photographyPackageDropdown) {
        photographyPackageDropdown.addEventListener('change', updatePhotographyPackagePriceDisplay);
    }

    // Attach event listeners to other elements to update the total discount field on change
    const elementsToUpdate = [
        'id_photography_package',
        'id_videography_package',
        'id_dj_package',
        'id_photobooth_package',
        'id_event_date',
        'id_other_discounts'
    ];

    elementsToUpdate.forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            element.addEventListener('change', updateTotalDiscountField);
        }
    });
});
// Ensure that updateContractData and calculateAndUpdateTotalCost functions are properly defined
// These functions should handle updating contract data and recalculating the total cost based on the new discount values



function updateContractData() {
    // Calculate overtime costs for each category
    let photographyOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('Photography');
    let videographyOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('Videography');
    let djOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('DJ');
    let photoboothOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('Photobooth');

    // Sum up all overtime costs
    let totalOvertimeCost = photographyOvertimeCost + videographyOvertimeCost + djOvertimeCost + photoboothOvertimeCost;

    contractData.packageCost = packageCost;
    contractData.additionalStaffCost = additionalStaffCost;
    contractData.engagementSessionCost = engagementSessionCost;
    contractData.overtimeCost = totalOvertimeCost; // Use the dynamically calculated total overtime cost
    contractData.totalDiscount = totalDiscount;
    // Other contract data updates...
}


// Setup event listeners for discount input fields
function setupDiscountInputListeners() {
    const discountInputs = ['id_package_discounts', 'id_sunday_discounts', 'id_other_discounts'];
    discountInputs.forEach(inputId => {
        const inputElement = document.getElementById(inputId);
        if (inputElement) {
            inputElement.addEventListener('change', () => {
                updateTotalDiscountField();
                calculateAndUpdateTotalCost(); // Ensure total cost is recalculated when discounts are changed
            });
        }
    });
}



// Function to calculate Videography cost
function calculateVideographyCost() {
    let videographyPackageCost = extractPriceFromSelectedOption('id_videography_package');
    let additionalVideographyCost = extractPriceFromSelectedOption('id_videography_additional');
    let videographyOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('Videography');

    return videographyPackageCost + additionalVideographyCost + videographyOvertimeCost;
}

// Function to update Videography cost display
function updateVideographyCostDisplay() {
    let videographyCost = calculateVideographyCost();
    document.getElementById('videography_cost').value = videographyCost.toFixed(2);
    updateTotalServiceCostDisplay(); // Update total service cost
}

// Function to calculate DJ cost
function calculateDJCost() {
    let djPackageCost = extractPriceFromSelectedOption('id_dj_package');
    let additionalDJCost = extractPriceFromSelectedOption('id_dj_additional');
    let djOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('DJ');

    return djPackageCost + additionalDJCost + djOvertimeCost;
}

// Function to update DJ cost display
function updateDJCostDisplay() {
    let djCost = calculateDJCost();
    document.getElementById('dj_cost').value = djCost.toFixed(2);
    updateTotalServiceCostDisplay(); // Update total service cost
}

function extractPriceFromSelectedOption(selectElementId) {
    const selectElement = document.getElementById(selectElementId);
    return selectElement ? extractPrice(selectElement.options[selectElement.selectedIndex].text) : 0;
}

function calculatePhotoboothCost() {
    let photoboothPackageCost = extractPriceFromSelectedOption('id_photobooth_package');
    let photoboothOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('PhotoBooth');

    return photoboothPackageCost + photoboothOvertimeCost;
}

function updatePhotoboothCostDisplay() {
    let photoboothCost = calculatePhotoboothCost();
    document.getElementById('photobooth_cost').value = photoboothCost.toFixed(2);
    updateTotalServiceCostDisplay(); // Update total service cost
}

function calculateTotalServiceCost() {
    let photographyCost = calculatePhotographyCost();
    let videographyCost = calculateVideographyCost();
    let djCost = calculateDJCost();
    let photoboothCost = calculatePhotoboothCost();

    return photographyCost + videographyCost + djCost + photoboothCost;
}

function updateTotalServiceCostDisplay() {
    let totalServiceCost = calculateTotalServiceCost();
    document.getElementById('total_service_cost').value = totalServiceCost.toFixed(2);
}



// Function to calculate and update the total cost
function calculateAndUpdateTotalCost() {
    // Dynamically calculate overtime costs for each category
    let photographyOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('Photography');
    let videographyOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('Videography');
    let djOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('DJ');
    let photoboothOvertimeCost = overtimeMgmt.calculateOvertimeCostForCategory('Photobooth');

    // Sum up all overtime costs
    let totalOvertimeCost = photographyOvertimeCost + videographyOvertimeCost + djOvertimeCost + photoboothOvertimeCost;

    // Calculate costs managed by this file
    let totalCost = packageCost + additionalStaffCost + engagementSessionCost + totalOvertimeCost - totalDiscount;

    // Add costs from contractData (if applicable)
    totalCost += (contractData.additionalProductCosts || 0) + (contractData.taxAmount || 0);

    // Update the hidden total cost field
    const totalCostField = document.getElementById('total_cost');
    if (totalCostField) {
        totalCostField.value = totalCost.toFixed(2);
    } else {
        console.error('Total cost field not found.');
    }

    // Update any UI elements or perform additional actions based on the new total cost
    updateTotalCostUI(totalCost);
}

// Helper function to update the UI based on the total cost
function updateTotalCostUI(totalCost) {
    // Update the total cost display in the finance tab, if it exists
    const displayTotalCost = document.getElementById('display_total_cost');
    if (displayTotalCost) {
        displayTotalCost.textContent = `$${totalCost.toFixed(2)}`;
    }

    // Additional UI updates or logic based on the new total cost
}


// Assumption: packageCost, additionalStaffCost, engagementSessionCost, overtimeCost, and totalDiscount
// are calculated and updated elsewhere in your script.
// contractData.additionalProductCosts and contractData.taxAmount are assumed to be defined
// and updated by ProductCostandTaxManagement.js.


// Function to handle package and engagement session selection changes
function onSelectionChange() {
    updateTotalDiscountField();
    calculateAndUpdateTotalCost(); // This will calculate and update the total cost based on current selections
}


