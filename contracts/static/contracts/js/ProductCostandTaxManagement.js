import { contractData } from '/static/contracts/js/utilities.js'; // Adjust the path as needed

// Initial console log and global variables
console.log("Product Cost and Tax Management.js loaded and executed!");

let globalAdditionalProducts = [];
let currentTaxRate = 0; // Variable to store the current tax rate



document.getElementById('products-table').addEventListener('click', function(event) {
        if (event.target.classList.contains('remove-product-btn')) {
            const row = event.target.closest('tr');
            row.remove();
            // Decrement the total forms count
            let totalForms = document.querySelector("#id_contract_products-TOTAL_FORMS");
            totalForms.value = parseInt(totalForms.value, 10) - 1;
            // Update total cost after removing the product
            updateTotalProductCostDisplay(); // Assuming this function recalculates and updates the total cost
        }

    });

function fetchTaxRate(locationId) {
    if (typeof locationId === 'undefined') {
        console.error('Error fetching tax rate: locationId is undefined');
        return;
    }

    const taxRateUrl = `/contracts/api/tax_rate/${locationId}/`;

    fetch(taxRateUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.tax_rate !== undefined) {
                currentTaxRate = data.tax_rate;
                displayTaxRate(); // Update the UI with the new tax rate
                calculateTax(); // Recalculate tax with the new rate
                updateTotalProductCostDisplay(); // Update the total cost display, including the tax
            } else {
                console.error('Tax rate not found for location:', locationId);
            }
        })
        .catch(error => {
            console.error('Error fetching tax rate for location:', locationId, error);
        });
}



// Function to add a new product selection and attach event listener
window.addProduct = function() {
    const productsTableBody = document.getElementById('products-table').getElementsByTagName('tbody')[0];
    if (!productsTableBody) {
        console.error("Products table body not found");
        return;
    }

    let totalForms = document.querySelector("#id_contract_products-TOTAL_FORMS");
    let formIndex = parseInt(totalForms.value, 10); // Current index for the new form

    const newRow = productsTableBody.insertRow();

    // For each cell, create and append the form element
    const fields = ['product', 'description', 'quantity', 'notes', 'special_notes', 'price'];
    fields.forEach((field, index) => {
        const cell = newRow.insertCell(index);
        const input = document.createElement(index === 0 ? 'select' : 'input');

        input.name = `contract_products-${formIndex}-${field}`;
        // Set attributes for each field based on its type
        switch (field) {
            case 'product':
                input.innerHTML = '<option value="">Select Product</option>';
                globalAdditionalProducts.forEach(product => {
                    const option = document.createElement('option');
                    option.value = product.id;
                    option.textContent = `${product.name} - $${product.price}`;
                    input.appendChild(option);
                });
                break;
            case 'quantity':
                input.type = 'number';
                input.min = '1';
                input.value = '1';
                break;
            case 'price':
                input.readOnly = true;
                break;
            default:
                input.type = 'text';
                break;
        }

        cell.appendChild(input);
    });

    // Adding the Remove Product button
const removeCell = newRow.insertCell(fields.length);
const removeButton = document.createElement('button');
removeButton.type = 'button';
removeButton.innerText = 'Remove Product';
removeButton.className = 'remove-product-btn'; // Add any additional classes if needed
removeButton.onclick = function() {
    // Functionality to remove the current row
    newRow.remove();
    // Decrement the total forms count
    totalForms.value = parseInt(totalForms.value, 10) - 1;

};
removeCell.appendChild(removeButton);



    // Increment the total forms count to reflect the new row
    totalForms.value = formIndex + 1;


    // Add event listeners to the new product selection and quantity fields
    newRow.querySelector(`[name="contract_products-${formIndex}-product"]`).addEventListener('change', function() {
        const inputDescription = newRow.querySelector(`[name="contract_products-${formIndex}-description"]`);
        const inputQuantity = newRow.querySelector(`[name="contract_products-${formIndex}-quantity"]`);
        const inputPrice = newRow.querySelector(`[name="contract_products-${formIndex}-price"]`);
        updateProductDetails(this, inputDescription, inputQuantity, inputPrice);
    });
    newRow.querySelector(`[name="contract_products-${formIndex}-quantity"]`).addEventListener('input', function() {
        const selectProduct = newRow.querySelector(`[name="contract_products-${formIndex}-product"]`);
        const inputDescription = newRow.querySelector(`[name="contract_products-${formIndex}-description"]`);
        const inputPrice = newRow.querySelector(`[name="contract_products-${formIndex}-price"]`);
        updateProductDetails(selectProduct, inputDescription, this, inputPrice);
    });
};

document.addEventListener('click', function(event) {
    if (event.target.matches('[data-formset-delete]')) {
        var row = event.target.closest('tr');
        var deleteField = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteField) {
            deleteField.checked = true;
            row.style.display = 'none'; // Hide the row
        }
    }
});

// Function to display the tax rate
function displayTaxRate() {
    const taxRateElement = document.getElementById('id_tax_rate');
    if (taxRateElement) {
        taxRateElement.value = currentTaxRate.toFixed(2); // Update the field with the tax rate
    }
}


// Function to fetch additional products
function fetchAdditionalProducts() {
    fetch('/contracts/api/additional_products/')
        .then(response => response.json())
        .then(data => globalAdditionalProducts = data)
        .catch(error => console.error('Error fetching additional products:', error));
}

function calculateAdditionalProductCosts() {
    let totalProductCost = 0;
    document.querySelectorAll('.product-price').forEach(function(priceCell) {
        var price = parseFloat(priceCell.textContent) || 0;
        totalProductCost += price;
    });
    return totalProductCost;
}



// Function to calculate the taxable amount
function calculateTaxableAmount() {
    let taxableAmount = 0;
    const productRows = document.getElementById('products-table').getElementsByTagName('tbody')[0].rows;

    for (let row of productRows) {
        const selectElement = row.cells[0].getElementsByTagName('select')[0];
        const quantityInput = row.cells[2].getElementsByTagName('input')[0];

        if (selectElement.value) {
            const selectedProductId = selectElement.value;
            const selectedProduct = globalAdditionalProducts.find(product => product.id.toString() === selectedProductId);

            if (selectedProduct && selectedProduct.is_taxable) {
                const quantity = parseInt(quantityInput.value) || 1;
                const price = parseFloat(selectedProduct.price);
                taxableAmount += price * quantity;
            }
        }
    }
    return taxableAmount;
}


// Function to calculate the total tax
function calculateTax() {
    const taxableAmount = calculateTaxableAmount();
    const taxRateDecimal = parseFloat(currentTaxRate) / 100;

    const calculatedTax = taxableAmount * taxRateDecimal;
    console.log(`Taxable Amount: ${taxableAmount}, Tax Rate: ${currentTaxRate}, Calculated Tax: ${calculatedTax}`);

    // Update the tax amount field
    updateTaxAmountField(calculatedTax);

    return calculatedTax;
}

function updateProductDetails(selectProduct, inputDescription, inputQuantity, inputPrice) {
    const selectedProductId = selectProduct.value;
    const selectedProduct = globalAdditionalProducts.find(product => product.id.toString() === selectedProductId);

    if (selectedProduct) {
        inputDescription.value = selectedProduct.description || '';
        const price = parseFloat(selectedProduct.price);
        const quantity = parseInt(inputQuantity.value) || 1;
        const totalPrice = price * quantity;
        inputPrice.textContent = totalPrice.toFixed(2); // Update the price text content

        // Update the shared data with the new product costs
        contractData.additionalProductCosts = calculateAdditionalProductCosts();

        // Update tax amount based on the new product costs
        contractData.taxAmount = calculateTax();

        // Update the total cost display
        updateTotalProductCostDisplay();


        // Update the tax amount field in the UI
        updateTaxAmountField(contractData.taxAmount);
    } else {
        inputDescription.value = '';
        inputPrice.textContent = ''; // Clear the price text content
    }
}


function updateTaxAmountField(taxAmount) {
    const taxAmountSpan = document.getElementById('tax_amount');
    if (taxAmountSpan) {
        taxAmountSpan.textContent = taxAmount.toFixed(2);
    }
}

function updateTotalProductCostDisplay() {
    let totalProductCost = calculateAdditionalProductCosts(); // Calculate the total product cost
    let taxAmount = calculateTax(); // Calculate the tax amount

    let totalCost = totalProductCost + taxAmount; // Include the tax in the total cost

    const totalCostElement = document.getElementById('total-product-cost'); // Assuming you have an element with this ID to display the total cost
    if (totalCostElement) {
        totalCostElement.textContent = totalCost.toFixed(2);
    }
}


// After calculating additional product costs
contractData.additionalProductCosts = calculateAdditionalProductCosts();

// After calculating tax
contractData.taxAmount = calculateTax();

document.addEventListener('DOMContentLoaded', function() {
    fetchAdditionalProducts();
    calculateTax();
    updateTaxAmountField(contractData.taxAmount);
    updateTotalProductCostDisplay()

    const locationId = document.getElementById('contract-location').getAttribute('data-location-id');
        if (locationId) {
            fetchTaxRate(locationId);
        }

    document.querySelectorAll('.quantity-input').forEach(function(quantityInput) {
        quantityInput.addEventListener('input', function() {
            var row = this.closest('tr');
            var basePrice = parseFloat(row.querySelector('.product-price').getAttribute('data-base-price'));
            var quantity = parseInt(this.value) || 0;
            var newPrice = basePrice * quantity;

            if (!isNaN(newPrice)) {
                row.querySelector('.product-price').textContent = newPrice.toFixed(2);
                updateTotalProductCostDisplay(); // Recalculate and update the total product cost
                calculateTax(); // Recalculate and update the tax
            } else {
                console.error('Invalid price calculation');
            }
        });
    });



    document.getElementById('products-table').addEventListener('click', function(event) {
        if (event.target.classList.contains('remove-product-btn')) {
            const row = event.target.closest('tr');
            row.remove();
            // Decrement the total forms count
            let totalForms = document.querySelector("#id_contract_products-TOTAL_FORMS");
            totalForms.value = parseInt(totalForms.value, 10) - 1;
            // Update total cost after removing the product
            updateTaxAmountField()
            updateTotalProductCostDisplay();
        }
    });
});




