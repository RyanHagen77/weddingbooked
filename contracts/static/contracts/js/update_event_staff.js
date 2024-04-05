// Initial console log and global variables
console.log("JS file loaded and executed!");



var globalAdditionalProducts = [];
var globalTaxRates = {};  // Stores tax rates based on location

// Function to fetch and store overtime rates globally



function setupProductSectionListener() {
    const productsSection = document.getElementById('products-section');
    if (productsSection) {
        productsSection.addEventListener('change', function(event) {
            if (event.target.matches('select[name="additional_products[]"]')) {
                calculateAndUpdateCosts();
            }
        });
    } else {
        console.error("Products section not found!");
    }
}

// Function to add a new product selection and attach event listener
window.addProduct = function() {
    const productsTableBody = document.getElementById('products-table').getElementsByTagName('tbody')[0];
    if (!productsTableBody) {
        console.error("Products table body not found");
        return;
    }

    const newRow = productsTableBody.insertRow();

    // Cell for product dropdown
    const cellProduct = newRow.insertCell(0);
    const selectProduct = document.createElement('select');
    selectProduct.name = 'additional_products[]';
    selectProduct.innerHTML = '<option value="">Select Product</option>';
    globalAdditionalProducts.forEach(product => {
        const option = document.createElement('option');
        option.value = product.id;
        option.textContent = `${product.name} - $${product.price}`;
        option.dataset.taxable = product.is_taxable.toString(); // Convert boolean to string
        selectProduct.appendChild(option);
    });

    cellProduct.appendChild(selectProduct);

    // Cell for description
    const cellDescription = newRow.insertCell(1);
    const inputDescription = document.createElement('input');
    inputDescription.type = 'text';
    inputDescription.name = 'product_description[]';
    inputDescription.disabled = true; // Disabled initially
    cellDescription.appendChild(inputDescription);

    // Cell for quantity
    const cellQuantity = newRow.insertCell(2);
    const inputQuantity = document.createElement('input');
    inputQuantity.type = 'number';
    inputQuantity.name = 'product_quantity[]';
    inputQuantity.min = '1'; // Ensure it's a string
    inputQuantity.value = '1'; // Default value as 1
    cellQuantity.appendChild(inputQuantity);

    // Cell for notes
    const cellNotes = newRow.insertCell(3);
    const inputNotes = document.createElement('input');
    inputNotes.type = 'text';
    inputNotes.name = 'product_notes[]';
    cellNotes.appendChild(inputNotes);

    // Cell for special notes
    const cellSpecialNotes = newRow.insertCell(4);
    const inputSpecialNotes = document.createElement('input');
    inputSpecialNotes.type = 'text';
    inputSpecialNotes.name = 'product_special_notes[]';
    cellSpecialNotes.appendChild(inputSpecialNotes);

    // Cell for price (read-only)
    const cellPrice = newRow.insertCell(5);
    const inputPrice = document.createElement('input');
    inputPrice.type = 'text';
    inputPrice.name = 'product_price[]';
    inputPrice.readOnly = true;
    cellPrice.appendChild(inputPrice);

    // Event listeners for product selection and quantity change
    selectProduct.addEventListener('change', function() {
        updateProductDetails(selectProduct, inputDescription, inputQuantity, inputPrice);
    });
    inputQuantity.addEventListener('input', function() {
        updateProductDetails(selectProduct, inputDescription, inputQuantity, inputPrice);
    });
};

// Function to update product details and recalculate costs
function updateProductDetails(selectProduct, inputDescription, inputQuantity, inputPrice) {
    const selectedProduct = globalAdditionalProducts.find(product => product.id.toString() === selectProduct.value);
    if (selectedProduct) {
        inputDescription.value = selectedProduct.description || '';
        const price = parseFloat(selectedProduct.price);
        const quantity = parseInt(inputQuantity.value) || 1;
        inputPrice.value = (price * quantity).toFixed(2);
    } else {
        inputDescription.value = '';
        inputPrice.value = '';
    }
    calculateAndUpdateCosts(); // Recalculate total costs including tax
}

// Function to calculate the taxable amount
function calculateTaxableAmount() {
    let taxableAmount = 0;
    const productRows = document.getElementById('products-table').getElementsByTagName('tbody')[0].rows;

    for (let row of productRows) {
        const selectElement = row.cells[0].getElementsByTagName('select')[0];
        const quantityInput = row.cells[2].getElementsByTagName('input')[0]; // Get the quantity input
        const selectedOption = selectElement.options[selectElement.selectedIndex];

        if (selectedOption && selectedOption.dataset.taxable === 'true') { // Compare as string
            console.log("Selected Option: ", selectedOption); // Debugging line

            const price = extractPrice(selectedOption.textContent);
            const quantity = parseInt(quantityInput.value) || 1; // Default to 1 if no quantity
            console.log("Price: ", price, "Quantity: ", quantity); // Debugging line

            taxableAmount += price * quantity;
        }
    }

    console.log("Calculated Taxable Amount: ", taxableAmount); // Debugging line
    return taxableAmount;
}



function calculateTax() {
    const selectedLocation = document.getElementById('id_location').value;
    const taxRate = globalTaxRates[selectedLocation] || 0;
    let taxableAmount = 0;

    // Calculate tax for additional products marked as taxable
    document.querySelectorAll('select[name="additional_products[]"]').forEach(selectElement => {
        if (selectElement.value) {
            const option = selectElement.options[selectElement.selectedIndex];
            const price = extractPrice(option.text);
            const isTaxable = option.dataset.taxable === 'true'; // Assuming each option has a data-taxable attribute
            if (isTaxable) {
                taxableAmount += price;
            }
        }
    });

    return taxableAmount * taxRate;
}
// Function to calculate and display the tax amount
function updateTaxAmount() {
    const taxRate = parseFloat(document.getElementById('id_tax_rate').value) || 0;
    const taxableAmount = calculateTaxableAmount();
    const taxAmount = taxableAmount * taxRate / 100;

    console.log("Tax Rate: ", taxRate, "Taxable Amount: ", taxableAmount, "Tax Amount: ", taxAmount); // Debugging line

    document.getElementById('tax_amount').value = taxAmount.toFixed(2);
}


function calculateAndUpdateCosts() {
    let totalCost = 0;

    // Calculate costs for packages
    packageFields.forEach(fieldId => {
        const fieldElement = document.getElementById(fieldId);
        if (fieldElement && fieldElement.value) {
            const selectedOptionText = fieldElement.options[fieldElement.selectedIndex].text;
            totalCost += extractPrice(selectedOptionText);
        }
    });


    // Add costs for additional products
    totalCost += calculateAdditionalProductCosts();

    // Calculate tax only if there are taxable products
    const taxableAmount = calculateTaxableAmount();
    const selectedLocation = document.getElementById('id_location').value;
    const taxRate = globalTaxRates[selectedLocation] || 0; // Default to 0 if location is not in globalTaxRates
    const taxAmount = taxableAmount * taxRate / 100;

    // Update the tax amount field
    document.getElementById('tax_amount').value = taxAmount.toFixed(2);

    // Add tax to total cost
    totalCost += taxAmount;

    // Update the total cost field
    document.getElementById('total_cost').value = Math.max(0, totalCost).toFixed(2);
}


// Function to calculate costs for additional products
function calculateAdditionalProductCosts() {
    let totalAdditionalProductsCost = 0;
    const productRows = document.getElementById('products-table').getElementsByTagName('tbody')[0].rows;

    for (let row of productRows) {
        const selectElement = row.cells[0].getElementsByTagName('select')[0];
        const priceInput = row.cells[5].getElementsByTagName('input')[0]; // Price input field

        if (selectElement.value) {
            const price = parseFloat(priceInput.value) || 0;
            totalAdditionalProductsCost += price;
        }
    }

    return totalAdditionalProductsCost;
}

// DOMContentLoaded event listener to set up initial state
document.addEventListener("DOMContentLoaded", async function() {

    await fetchAdditionalProducts(); // Fetches additional products and awaits its completion
    setupProductSectionListener(); // Sets up listeners for the products section

});

