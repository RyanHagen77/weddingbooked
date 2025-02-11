import { contractData } from '../../utilities.js'; // Adjust the path as needed

console.log("Product Cost and Tax Management.js loaded and executed!");

let globalAdditionalProducts = [];
let currentTaxRate = 0; // Variable to store the current tax rate

function updateTotalProductCostDisplay() {
    let totalProductCost = calculateAdditionalProductCosts(); // Calculate the total product cost
    let taxAmount = calculateTax(); // Calculate the tax amount

    let totalCost = totalProductCost + taxAmount; // Include the tax in the total cost

    const totalCostElement = document.getElementById('total-product-cost'); // Assuming you have an element with this ID to display the total cost
    if (totalCostElement) {
        totalCostElement.textContent = '$' + totalCost.toFixed(2);
    }
}

function updateServerSideProducts(contractId) {
    const productRows = document.getElementById('products-table').getElementsByTagName('tbody')[0].rows;
    let products = [];

    for (let row of productRows) {
        const selectElement = row.cells[0].getElementsByTagName('select')[0];
        const quantityInput = row.cells[2].getElementsByTagName('input')[0];

        if (selectElement.value) {
            products.push({
                product_id: selectElement.value,
                quantity: quantityInput.value
            });
        }
    }

    console.log('Updating server-side products with:', products, 'and tax amount:', contractData.taxAmount); // Log data being sent

    fetch(`/contracts/${contractId}/save_products/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ products: products, tax_amount: contractData.taxAmount })
    })
    .then(response => {
        if (response.status === 302) {
            console.error('Redirection occurred. Check authentication and permissions.');
            return;
        }
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Server-side products updated successfully:', data);
        updateTaxAmountField(data.tax_amount);
    })
    .catch(error => {
        console.error('Error updating server-side products:', error);
    });
}

function calculateAdditionalProductCosts() {
    let totalProductCost = 0;
    document.querySelectorAll('.total-price').forEach(function(priceCell) {
        var price = parseFloat(priceCell.textContent.replace('$', '')) || 0;
        totalProductCost += price;
    });
    return totalProductCost;
}

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
        inputPrice.textContent = '$' + totalPrice.toFixed(2); // Update the price text content

        // Update the shared data with the new product costs
        contractData.additionalProductCosts = calculateAdditionalProductCosts();

        // Update tax amount based on the new product costs
        contractData.taxAmount = calculateTax();

        // Update the total cost display
        updateTotalProductCostDisplay();
    } else {
        inputDescription.value = '';
        inputPrice.textContent = ''; // Clear the price text content
    }
}

function updateTaxAmountField(taxAmount) {
    const taxAmountSpan = document.getElementById('tax_amount');
    if (taxAmountSpan) {
        taxAmountSpan.textContent = '$' + taxAmount.toFixed(2);
    }
}

function fetchTaxRate(locationId) {
    if (!locationId) {
        console.error('Location ID is undefined');
        return Promise.reject('Location ID is undefined');
    }

    const taxRateUrl = `/contracts/api/tax_rate/${locationId}/`;

    return fetch(taxRateUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.tax_rate !== undefined) {
                currentTaxRate = data.tax_rate;
                console.log('Fetched tax rate:', currentTaxRate); // Log fetched tax rate
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

function displayTaxRate() {
    const taxRateElement = document.getElementById('id_tax_rate');
    if (taxRateElement) {
        taxRateElement.value = currentTaxRate.toFixed(2); // Update the field with the tax rate
    }
}

function fetchAdditionalProducts() {
    fetch('/products/api/additional_products/')
        .then(response => response.json())
        .then(data => {
            globalAdditionalProducts = data;
            console.log('Fetched additional products:', globalAdditionalProducts); // Log fetched products
        })
        .catch(error => console.error('Error fetching additional products:', error));
}

window.addProduct = function() {
    const productsTableBody = document.getElementById('products-table').getElementsByTagName('tbody')[0];
    if (!productsTableBody) {
        console.error("Products table body not found");
        return;
    }

    let totalForms = document.querySelector("#id_contract_products-TOTAL_FORMS");
    let formIndex = parseInt(totalForms.value, 10); // Current index for the new form

    const newRow = productsTableBody.insertRow();

    const fields = ['product', 'description', 'quantity', 'special_notes', 'price'];
    fields.forEach((field, index) => {
        const cell = newRow.insertCell(index);
        const input = document.createElement(index === 0 ? 'select' : 'input');

        input.name = `contract_products-${formIndex}-${field}`;
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
                input.classList.add('quantity-input'); // Add a class for specific styling
                break;
            case 'special_notes':
                input.type = 'textarea';
                input.classList.add('special-notes-textarea'); // Add a class for specific styling
                break;
            case 'price':
                input.type = 'text';
                input.classList.add('total-price'); // Add a class for specific styling
                break;
            default:
                input.type = 'text';
                break;
        }

        cell.appendChild(input);
    });

    totalForms.value = formIndex + 1;

    // Attach event listeners to the new row's elements
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

    // Update total product cost and tax
    updateTotalProductCostDisplay();
    calculateTax();
};

contractData.additionalProductCosts = calculateAdditionalProductCosts();
contractData.taxAmount = calculateTax();

document.addEventListener('DOMContentLoaded', function() {
    fetchAdditionalProducts();
    calculateTax();
    updateTaxAmountField(contractData.taxAmount);
    updateTotalProductCostDisplay();

    const locationId = document.getElementById('contract-location').getAttribute('data-location-id');
    if (locationId) {
        fetchTaxRate(locationId);
    }

    document.querySelectorAll('.quantity-input').forEach(function(quantityInput) {
        quantityInput.addEventListener('input', function() {
            var row = this.closest('tr');
            var basePrice = parseFloat(row.querySelector('.unit-price').textContent.replace('$', ''));
            var quantity = parseInt(this.value) || 0;
            var newPrice = basePrice * quantity;

            if (!isNaN(newPrice)) {
                row.querySelector('.total-price').textContent = '$' + newPrice.toFixed(2);
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
            let totalForms = document.querySelector("#id_contract_products-TOTAL_FORMS");
            totalForms.value = parseInt(totalForms.value, 10) - 1;
            updateTotalProductCostDisplay(); // Update total cost and tax amount after removing the product
            calculateTax();
            const contractId = document.getElementById('contract-id').value; // Assuming you have this ID available
            updateServerSideProducts(contractId);
        }
    });
});
