// formalwearManager.js
import { saveFormalwear } from "./saveFormalwear.js"; // Adjust the path as needed
import { fetchFormalwearProducts } from "./fetchFormalwear.js"; // Adjust the path as needed

/**
 * Updates the price, deposit, type, and size in the current row based on the selected formalwear.
 */
function updatePrice(event) {
    const dropdown = event.target;
    const row = dropdown.closest("tr");
    // Use the server-side class names.
    const rentalPriceCell = row.querySelector(".rental-price");
    const depositAmountCell = row.querySelector(".deposit-amount");
    const typeCell = row.querySelector(".rental-type");
    const sizeCell = row.querySelector(".size");

    const selectedOption = dropdown.options[dropdown.selectedIndex];

    const rentalPrice = selectedOption.getAttribute("data-rental-price") || "0.00";
    const depositAmount = selectedOption.getAttribute("data-deposit") || "0.00";
    const type = selectedOption.getAttribute("data-type") || "-";
    const size = selectedOption.getAttribute("data-size") || "-";

    rentalPriceCell.innerText = `$${parseFloat(rentalPrice).toFixed(2)}`;
    depositAmountCell.innerText = `$${parseFloat(depositAmount).toFixed(2)}`;
    typeCell.innerText = type;
    sizeCell.innerText = size;
}

/**
 * Updates the display details for a formalwear row based on the selected product and quantity.
 *
 * @param {HTMLElement} newRow - The table row containing the formalwear form elements.
 * @param {number} formIndex - The index of the current form row.
 */
function updateFormalwearDetails(newRow, formIndex) {
    const selectFormalwear = newRow.querySelector(`select[name="form-${formIndex}-formalwear_product"]`);
    const inputQuantity = newRow.querySelector(`input[name="form-${formIndex}-quantity"]`);
    // Use the same class names as in the template.
    const rentalTypeDisplay = newRow.querySelector('.rental-type');
    const sizeDisplay = newRow.querySelector('.size');
    const rentalPriceDisplay = newRow.querySelector('.rental-price');
    const depositDisplay = newRow.querySelector('.deposit-amount');

    const selectedProductId = selectFormalwear.value;
    const selectedProduct = window.globalFormalwearProducts.find(
        product => product.id.toString() === selectedProductId
    );

    if (selectedProduct) {
        rentalTypeDisplay.textContent = selectedProduct.rental_type || '-';
        sizeDisplay.textContent = selectedProduct.size || '-';

        const rentalPrice = parseFloat(selectedProduct.rental_price) || 0;
        const depositAmount = parseFloat(selectedProduct.deposit_amount) || 0;
        const quantity = parseInt(inputQuantity.value, 10) || 1;
        const totalRentalPrice = rentalPrice * quantity;
        rentalPriceDisplay.textContent = '$' + totalRentalPrice.toFixed(2);
        depositDisplay.textContent = '$' + depositAmount.toFixed(2);
    } else {
        rentalTypeDisplay.textContent = '-';
        sizeDisplay.textContent = '-';
        rentalPriceDisplay.textContent = '$0.00';
        depositDisplay.textContent = '$0.00';
    }
}

function ensureManagementForm() {
    // Try to find the TOTAL_FORMS input.
    let totalForms = document.getElementById("id_form-TOTAL_FORMS");
    if (!totalForms) {
        // Create the hidden input for TOTAL_FORMS.
        totalForms = document.createElement("input");
        totalForms.type = "hidden";
        totalForms.id = "id_form-TOTAL_FORMS";
        totalForms.name = "form-TOTAL_FORMS";
        totalForms.value = "0"; // Start with 0 forms.

        // Append it to the form that contains your formset.
        const form = document.getElementById("formalwear-form");
        if (form) {
            form.appendChild(totalForms);
            console.log("Management form TOTAL_FORMS element created dynamically.");
        } else {
            console.error("Cannot find the form with id 'formalwear-form'");
        }
    }
}


/**
 * Adds a new formalwear row to the table.
 */
window.addFormalwear = function() {
    // Ensure the management form exists.
    ensureManagementForm();

    const formalwearTable = document.getElementById('formalwear-table');
    if (!formalwearTable) {
        console.error("Formalwear table not found");
        return;
    }
    const formalwearTableBody = formalwearTable.getElementsByTagName('tbody')[0];
    if (!formalwearTableBody) {
        console.error("Formalwear table body not found");
        return;
    }

    const totalForms = document.getElementById('id_form-TOTAL_FORMS');
    if (!totalForms) {
        console.error("Management form TOTAL_FORMS element not found");
        return;
    }
    let formIndex = parseInt(totalForms.value, 10);

    // Create a new row in the formalwear table.
    const newRow = formalwearTableBody.insertRow();
    // Add a common class for all rows.
    newRow.classList.add('formalwear-row');

    // --- Column 0: Formalwear Product Selection ---
    const cell0 = newRow.insertCell(0);
    const selectFormalwear = document.createElement('select');
    selectFormalwear.name = `form-${formIndex}-formalwear_product`;
    selectFormalwear.classList.add('formalwear-dropdown');
    // Add a default option.
    const defaultOption = document.createElement('option');
    defaultOption.value = "";
    defaultOption.textContent = "Select Formalwear";
    selectFormalwear.appendChild(defaultOption);
    // Populate with options from the global formalwear products array.
    if (window.globalFormalwearProducts && Array.isArray(window.globalFormalwearProducts)) {
        window.globalFormalwearProducts.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.setAttribute("data-rental-price", product.rental_price);
            option.setAttribute("data-deposit", product.deposit_amount);
            option.setAttribute("data-type", product.rental_type);
            option.setAttribute("data-size", product.size);
            option.textContent = `${product.name} - $${product.rental_price}`;
            selectFormalwear.appendChild(option);
        });
    }
    cell0.appendChild(selectFormalwear);

    // --- Column 1: Rental Type (Display Only) ---
    const cell1 = newRow.insertCell(1);
    const rentalTypeSpan = document.createElement('span');
    rentalTypeSpan.classList.add('rental-type');
    rentalTypeSpan.textContent = '-';
    cell1.appendChild(rentalTypeSpan);

    // --- Column 2: Size (Display Only) ---
    const cell2 = newRow.insertCell(2);
    const sizeSpan = document.createElement('span');
    sizeSpan.classList.add('size');
    sizeSpan.textContent = '-';
    cell2.appendChild(sizeSpan);

    // --- Column 3: Quantity Input ---
    const cell3 = newRow.insertCell(3);
    const inputQuantity = document.createElement('input');
    inputQuantity.type = 'number';
    inputQuantity.name = `form-${formIndex}-quantity`;
    inputQuantity.value = "1";      // Default value set to "1"
    inputQuantity.min = "1";        // Minimum value is 1
    inputQuantity.step = "1";       // Allow only whole numbers
    inputQuantity.classList.add('form-control', 'quantity-input', 'text-center');
    inputQuantity.style.width = '70px';
    cell3.appendChild(inputQuantity);

    // --- Column 4: Rental Price (Display Only) ---
    const cell4 = newRow.insertCell(4);
    const rentalPriceSpan = document.createElement('span');
    rentalPriceSpan.classList.add('rental-price');
    rentalPriceSpan.textContent = '$0.00';
    cell4.appendChild(rentalPriceSpan);

    // --- Column 5: Deposit (Display Only) ---
    const cell5 = newRow.insertCell(5);
    const depositSpan = document.createElement('span');
    depositSpan.classList.add('deposit-amount');
    depositSpan.textContent = '$0.00';
    cell5.appendChild(depositSpan);

    // --- Column 6: Rental Return Date Input ---
    const cell6 = newRow.insertCell(6);
    const inputReturnDate = document.createElement('input');
    inputReturnDate.type = 'date';
    inputReturnDate.name = `form-${formIndex}-rental_return_date`;
    inputReturnDate.classList.add('form-control');
    inputReturnDate.style.maxWidth = '150px';
    cell6.appendChild(inputReturnDate);

    // --- Column 7: Added On (Display Only) ---
    const cell7 = newRow.insertCell(7);
    const addedOnSpan = document.createElement('span');
    addedOnSpan.classList.add('added-on');
    addedOnSpan.textContent = 'Not yet added';
    cell7.appendChild(addedOnSpan);

    // --- Column 8: Remove Checkbox ---
    const cell8 = newRow.insertCell(8);
    const inputDelete = document.createElement('input');
    inputDelete.type = 'checkbox';
    inputDelete.name = `form-${formIndex}-DELETE`;
    cell8.appendChild(inputDelete);

    // Increment the TOTAL_FORMS count for Django formset processing.
    totalForms.value = formIndex + 1;

    // Attach event listeners to update the row's display details.
    selectFormalwear.addEventListener('change', function() {
        updateFormalwearDetails(newRow, formIndex);
    });
    inputQuantity.addEventListener('input', function() {
        updateFormalwearDetails(newRow, formIndex);
    });
};


/* ----- Initialize on DOMContentLoaded ----- */
document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded - initializing formalwearManager");

    // Ensure that all delete checkboxes are unchecked on page load.
    document.querySelectorAll("input[type='checkbox'][name*='DELETE']").forEach(checkbox => {
        checkbox.checked = false;
    });

    // First, fetch the formalwear products.
    fetchFormalwearProducts().then(() => {
        console.log("Formalwear products fetched and stored in window.globalFormalwearProducts");

        // Now attach change event to all existing formalwear dropdowns.
        document.querySelectorAll("select[name*='formalwear_product']").forEach(dropdown => {
            dropdown.addEventListener("change", updatePrice);
        });

        // Attach event listener to the Add Formalwear button.
        const addButton = document.getElementById("add-formalwear-btn");
        if (addButton) {
            addButton.addEventListener("click", addFormalwear);
        } else {
            console.warn("Element with id 'add-formalwear-btn' not found.");
        }

        // Attach click event to the Save Formalwear button.
        const saveButton = document.getElementById('save-formalwear-btn');
        if (saveButton) {
            saveButton.addEventListener('click', function (event) {
                event.preventDefault(); // Prevent default form submission.

                const formalwearItems = [];
                // Loop through each formalwear row.
                document.querySelectorAll('.formalwear-row').forEach(row => {
                    // Read the hidden id input (if present)
                    const idInput = row.querySelector("input[name*='-id']");
                    const itemId = idInput ? idInput.value : "";

                    const deleteCheckbox = row.querySelector("input[type='checkbox'][name*='DELETE']");
                    if (deleteCheckbox && deleteCheckbox.checked) {
                        // Optionally, you could include the id here to explicitly mark it for deletion.
                        // For example: formalwearItems.push({ id: itemId, delete: true });
                        return; // Skip rows marked for deletion.
                    }

                    const selectElement = row.querySelector("select[name*='formalwear_product']");
                    const quantityInput = row.querySelector("input[name*='quantity']");
                    const rentalReturnDateInput = row.querySelector("input[name*='rental_return_date']");

                    if (selectElement && selectElement.value) {
                        const payloadItem = {
                            id: itemId,  // This will be an empty string for new items.
                            product_id: selectElement.value,
                            quantity: quantityInput ? quantityInput.value : 1,
                            rental_return_date: rentalReturnDateInput ? rentalReturnDateInput.value : null
                        };
                        formalwearItems.push(payloadItem);
                    }
                });

                const contractIdElement = document.getElementById('contract-id');
                if (!contractIdElement) {
                    console.error("Element with id 'contract-id' not found.");
                    return;
                }
                const contractId = contractIdElement.value;

                saveFormalwear(contractId, formalwearItems)
                    .then(data => {
                        console.log('Server-side formalwear updated successfully:', data);
                        window.location.reload();
                    })
                    .catch(error => {
                        console.error('Error updating server-side formalwear:', error);
                    });
            });
        } else {
            console.warn("Element with id 'save-formalwear-btn' not found.");
        }
    });
});
