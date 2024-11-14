// Get CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Add formset entry
function addFormsetEntry(containerId, totalFormsId, formClass) {
    let container = document.getElementById(containerId);
    let totalForms = document.getElementById(totalFormsId);
    if (!totalForms) {
        console.error('Total forms input not found:', totalFormsId);
        return;
    }
    let currentTotal = parseInt(totalForms.value, 10);

    // Determine the correct empty form template based on the form class
    let emptyFormTemplate;
    if (formClass === '.payment-form') {
        emptyFormTemplate = document.querySelector('.empty-payment-form');
    } else if (formClass === '.service-fee-form') {
        emptyFormTemplate = document.querySelector('.empty-service-fee-form');
    }

    if (!emptyFormTemplate) {
        console.error('Empty form template not found:', formClass);
        return;
    }

    let newFormHtml = emptyFormTemplate.innerHTML.replace(/__prefix__/g, currentTotal);

    // Create a new form element and set its inner HTML
    let newFormDiv = document.createElement('div');
    newFormDiv.classList.add(formClass.replace('.', ''), 'mb-3');
    newFormDiv.innerHTML = newFormHtml;

    // Append the new form to the container
    container.appendChild(newFormDiv);

    // Increment the total forms count
    totalForms.value = currentTotal + 1;

    // Ensure new inputs are enabled for editing
    let newFormCheckbox = newFormDiv.querySelector('.edit-toggle');
    if (newFormCheckbox) {
        newFormCheckbox.checked = true;
        toggleEdit(newFormCheckbox);
    }
}

// Toggle edit state
function toggleEdit(checkbox) {
    var formFields = checkbox.closest('.payment-form, .service-fee-form').querySelector('.form-fields');
    var inputs = formFields.querySelectorAll('input, select, textarea');

    inputs.forEach(function(input) {
        input.disabled = !checkbox.checked;
    });
}

// Enable all inputs
function enableAllInputs() {
    var inputs = document.querySelectorAll('#scheduleForm input, #scheduleForm select, #scheduleForm textarea, #serviceFeeForm input, #serviceFeeForm select, #serviceFeeForm textarea');
    inputs.forEach(function(input) {
        input.disabled = false;
    });
}

// Initialize form inputs as disabled
function initializeFormInputs() {
    var formInputs = document.querySelectorAll('.payment-form .form-fields input, .payment-form .form-fields select, .payment-form .form-fields textarea, .service-fee-form .form-fields input, .service-fee-form .form-fields select, .service-fee-form .form-fields textarea');
    formInputs.forEach(function(input) {
        input.disabled = true;
    });
}

// Format payment method
function formatPaymentMethod(method) {
    const methodMapping = {
        'CASH': 'Cash',
        'CHECK': 'Check',
        'CREDIT_CARD': 'Credit Card',
        'ZELLE': 'Zelle',
        'VENMO': 'Venmo'
    };
    return methodMapping[method] || method;
}

// Populate schedule table based on schedule type
function populateScheduleTable(scheduleType) {
    let container = document.getElementById('payment-schedule-table');
    container.innerHTML = ''; // Clear existing table content

    let table = document.createElement('table');
    table.className = 'table';

    let thead = table.createTHead();
    let headerRow = thead.insertRow();
    createHeaderCell(headerRow, 'Description');
    createHeaderCell(headerRow, 'Due Date');
    createHeaderCell(headerRow, 'Amount');
    createHeaderCell(headerRow, 'Status');

    let tbody = table.createTBody();

    if (scheduleType === 'schedule_a') {
        populateScheduleA(tbody);
    } else if (scheduleType === 'custom') {
        populateCustomSchedule(tbody);
    }

    container.appendChild(table);
    updateDepositStatus();
}

// Populate Schedule A
function populateScheduleA(tbody) {
    let depositAmount = Math.ceil((contractData.servicesTotalAfterDiscounts * 0.50) / 100) * 100;
    let totalContractAmount = parseFloat(document.querySelector('.contract-total').getAttribute('data-contract-total'));
    let balanceAmount = totalContractAmount - depositAmount;
    let balanceDueDate = new Date(contractData.eventDate);
    balanceDueDate.setDate(balanceDueDate.getDate() - 60);

    let totalPayments = getTotalPayments();
    let depositStatus = (totalPayments >= depositAmount - 0.01) ? 'Paid' : 'Unpaid';
    let balanceStatus = (totalPayments >= totalContractAmount) ? 'Paid' : 'Unpaid';

    addScheduleRow(tbody, 'Deposit', 'Upon Booking', depositAmount, depositStatus);
    addScheduleRow(tbody, 'Balance Due', balanceDueDate.toISOString().slice(0, 10), balanceAmount, balanceStatus);

    fetchServiceFees();
}

// Populate custom schedule
function populateCustomSchedule(tbody) {
    let contractId = document.body.getAttribute('data-contract-id');
    fetch(`/payments/${contractId}/get_custom_schedule/`)
        .then(response => response.json())
        .then(data => {
            let totalPayments = getTotalPayments();
            data.forEach(payment => {
                let status = totalPayments >= parseFloat(payment.amount) ? 'Paid' : 'Unpaid';
                addScheduleRow(tbody, payment.purpose, payment.due_date, parseFloat(payment.amount), status);
                totalPayments -= parseFloat(payment.amount);
            });
            fetchServiceFees();
        })
        .catch(error => console.error('Error fetching custom schedule:', error));
}

// Add a schedule row
function addScheduleRow(tbody, description, dueDate, amount, status) {
    let row = tbody.insertRow();
    row.insertCell().textContent = description;
    row.insertCell().textContent = dueDate;
    row.insertCell().textContent = `$${amount.toFixed(2)}`;
    row.insertCell().textContent = status;
}

// Fetch service fees
function fetchServiceFees() {
    let contractId = document.body.getAttribute('data-contract-id');
    let serviceFeeContainers = document.getElementsByClassName('service-fees-table');

    if (serviceFeeContainers.length === 0) {
        console.error('Service fee container element not found.');
        return;
    }

    let serviceFeeContainer = serviceFeeContainers[0];

    fetch(`/contracts/${contractId}/get_service_fees/`)
        .then(response => response.json())
        .then(data => {
            serviceFeeContainer.innerHTML = '';

            let table = document.createElement('table');
            table.className = 'table';

            let thead = table.createTHead();
            let headerRow = thead.insertRow();
            createHeaderCell(headerRow, 'Description');
            createHeaderCell(headerRow, 'Fee Type');
            createHeaderCell(headerRow, 'Amount');
            createHeaderCell(headerRow, 'Applied Date');  // Added Applied Date header

            let tbody = table.createTBody();

            data.forEach(fee => {
                let row = tbody.insertRow();
                row.insertCell().textContent = fee.description;
                row.insertCell().textContent = fee.fee_type;
                row.insertCell().textContent = `$${parseFloat(fee.amount).toFixed(2)}`;
                row.insertCell().textContent = fee.applied_date;  // Added Applied Date data
            });

            serviceFeeContainer.appendChild(table);
        })
        .catch(error => console.error('Error fetching service fees:', error));
}

// Create header cell
function createHeaderCell(row, text) {
    let cell = row.insertCell();
    cell.textContent = text;
    cell.style.fontWeight = 'bold';
}

// Handle schedule change
function handleScheduleChange(scheduleType) {
    populateScheduleTable(scheduleType);
    let scheduleModalButton = document.querySelector('[data-target="#scheduleModal"]');

    if (scheduleType === 'custom') {
        scheduleModalButton.style.display = 'inline-block';
    } else {
        scheduleModalButton.style.display = 'none';
    }
}

// Receive payment
function receivePayment() {
    let scheduleType = document.getElementById('payment-schedule').value;

    if (scheduleType === 'schedule_a') {
        document.getElementById('amount').value = '';
    } else if (scheduleType === 'custom') {
        let payments = document.querySelectorAll('.payments-content .table tbody tr');
        let nextPaymentAmount = '';
        for (let row of payments) {
            let statusCell = row.cells[row.cells.length - 1];
            if (statusCell.textContent.trim() === 'Unpaid') {
                nextPaymentAmount = row.cells[2].textContent.replace('$', '').trim();
                break;
            }
        }
        document.getElementById('amount').value = nextPaymentAmount;
    } else {
        document.getElementById('amount').value = '';
    }

    $('#paymentModal').modal('show');
}

// Get total payments
function getTotalPayments() {
    let paymentsTableBody = document.querySelector('.existing-payments-table tbody');
    let totalPayments = 0;

    for (let row of paymentsTableBody.rows) {
        totalPayments += parseFloat(row.cells[1].textContent.replace('$', ''));
    }

    return totalPayments;
}

// Confirm payment
function confirmPayment() {
    let paymentAmount = parseFloat(document.getElementById('amount').value);
    let balanceDueElement = document.getElementById('balance-due-amount');
    let balanceDue = parseFloat(balanceDueElement.textContent.replace('$', ''));
    let paymentMethod = document.getElementById('payment_method').value;
    let paymentPurposeElement = document.getElementById('payment_purpose');
    let paymentPurpose = paymentPurposeElement.value;
    let paymentPurposeText = paymentPurposeElement.options[paymentPurposeElement.selectedIndex].text;  // Get payment purpose text
    let paymentMemo = document.getElementById('memo').value;
    let paymentReference = document.getElementById('payment_reference').value;
    let paymentId = document.getElementById('payment-id').value;
    let paymentAction = document.getElementById('payment-action').value;
    let url = (paymentAction === 'edit') ? `/payments/edit_payment/${paymentId}/` : `/payments/add_payment/${contractData.paymentScheduleId}/`;

    let originalAmount = parseFloat(document.getElementById('original-amount').value) || 0;
    let amountDifference = paymentAmount - originalAmount;

    // Check if the difference in payment amount exceeds balance due
    if (amountDifference > balanceDue) {
        alert('The difference in the payment amount exceeds the remaining balance. Please enter a valid amount.');
        return;
    }

    let formData = new FormData();
    formData.append('amount', paymentAmount);
    formData.append('payment_method', paymentMethod);
    formData.append('payment_purpose', paymentPurpose);
    formData.append('memo', paymentMemo);
    formData.append('payment_reference', paymentReference);

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Error saving payment');
        }
    })
    .then(data => {
        // Update the UI based on the payment
        updatePaymentsTable(paymentAmount, paymentMethod, paymentPurposeText, paymentReference, paymentMemo, data.payment_id, paymentAction);  // Pass paymentPurposeText

        // Recalculate the balance due
        let newBalanceDue = balanceDue - amountDifference;
        balanceDueElement.textContent = `$${newBalanceDue.toFixed(2)}`;

        // Update the deposit status if applicable
        if (paymentAction !== 'edit') {
            updateDepositStatus(paymentAmount, newBalanceDue);
        }

        clearPaymentForm();
    })
    .catch(error => console.error('Error saving payment:', error));

    $('#paymentModal').on('hidden.bs.modal', clearPaymentForm);
    $('#paymentModal').modal('hide');
}


// Clear payment form
function clearPaymentForm() {
    document.getElementById('payment-form').reset();
    document.getElementById('payment-id').value = '';
    document.getElementById('payment-action').value = 'add';
    document.getElementById('original-amount').value = '';
}

// Edit payment
function editPayment(paymentId, amount, paymentMethod, paymentReference, memo, paymentPurpose) {
    document.getElementById('payment-id').value = paymentId;
    document.getElementById('original-amount').value = amount; // Store original amount
    document.getElementById('amount').value = amount;
    document.getElementById('payment_method').value = paymentMethod;
    document.getElementById('payment_reference').value = paymentReference || '';
    document.getElementById('memo').value = memo || '';

    const paymentPurposeElement = document.getElementById('payment_purpose');
    const options = paymentPurposeElement.options;
    for (let i = 0; i < options.length; i++) {
        if (options[i].text === paymentPurpose) {
            paymentPurposeElement.selectedIndex = i;
            break;
        }
    }

    document.getElementById('payment-action').value = 'edit';
    $('#paymentModal').modal('show');
}

// Update payments table
function updatePaymentsTable(paymentAmount, paymentMethod, paymentPurpose, paymentReference, paymentMemo, paymentId, paymentAction) {
    let paymentsTableBody = document.querySelector('.existing-payments-table tbody');

    if (paymentAction === 'edit') {
        let rowToUpdate = paymentsTableBody.querySelector(`tr[data-payment-id="${paymentId}"]`);
        if (rowToUpdate) {
            rowToUpdate.cells[1].textContent = `$${paymentAmount.toFixed(2)}`;
            rowToUpdate.cells[2].textContent = formatPaymentMethod(paymentMethod);
            rowToUpdate.cells[3].textContent = paymentPurpose;
            rowToUpdate.cells[4].textContent = paymentReference;
            rowToUpdate.cells[5].textContent = paymentMemo;
        }
    } else {
        let newRow = paymentsTableBody.insertRow();
        newRow.setAttribute('data-payment-id', paymentId);

        let currentDate = new Date();
        let formattedDate = currentDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

        newRow.insertCell().textContent = formattedDate;
        newRow.insertCell().textContent = `$${paymentAmount.toFixed(2)}`;
        newRow.insertCell().textContent = formatPaymentMethod(paymentMethod);
        newRow.insertCell().textContent = paymentPurpose;
        newRow.insertCell().textContent = paymentReference;
        newRow.insertCell().textContent = paymentMemo;

        let actionCell = newRow.insertCell();
        actionCell.innerHTML = `
            <button type="button" class="btn btn-info btn-sm" onclick="editPayment('${paymentId}', '${paymentAmount}', '${paymentMethod}', '${paymentReference}', '${paymentMemo}', '${paymentPurpose}')">Edit</button>
            <button type="button" class="btn btn-danger btn-sm" onclick="if(confirm('Are you sure?')){ window.location.href='/payments/delete_payment/${paymentId}/'; }">Delete</button>
        `;
    }

    updateBalanceDue(paymentAmount);
}

// Update balance due
function updateBalanceDue(paymentAmount) {
    let balanceDueElement = document.getElementById('balance-due-amount');
    let balanceDue = parseFloat(balanceDueElement.textContent.replace('$', '')) || 0;
    let newBalanceDue = balanceDue - paymentAmount;
    balanceDueElement.textContent = `$${newBalanceDue.toFixed(2)}`;
}

// Update deposit status
function updateDepositStatus() {
    let scheduleType = document.getElementById('payment-schedule').value;
    let totalContractAmount = parseFloat(document.querySelector('.contract-total').getAttribute('data-contract-total'));
    let totalPayments = getTotalPayments();

    if (scheduleType === 'schedule_a') {
        let depositRow = document.querySelector('.payments-content .table tbody tr:first-child');
        let balanceRow = document.querySelector('.payments-content .table tbody tr:last-child');

        let depositAmount = parseFloat(depositRow.cells[2].textContent.replace('$', ''));
        depositRow.cells[3].textContent = totalPayments >= depositAmount ? 'Paid' : 'Unpaid';
        totalPayments -= depositAmount;

        balanceRow.cells[3].textContent = totalPayments >= totalContractAmount - depositAmount ? 'Paid' : 'Unpaid';
    } else if (scheduleType === 'custom') {
        let paymentRows = document.querySelectorAll('.payments-content .table tbody tr');
        paymentRows.forEach(row => {
            let paymentAmount = parseFloat(row.cells[2].textContent.replace('$', ''));
            row.cells[3].textContent = totalPayments >= paymentAmount ? 'Paid' : 'Unpaid';
            totalPayments -= paymentAmount;
        });
    }
}

// Load existing payments
function loadExistingPayments() {
    let contractId = document.body.getAttribute('data-contract-id');
    fetch(`/payments/${contractId}/get_existing_payments/`)
        .then(response => response.json())
        .then(data => {
            let paymentsTableBody = document.querySelector('.existing-payments-table tbody');
            paymentsTableBody.innerHTML = '';

            data.forEach(payment => {
                let newRow = paymentsTableBody.insertRow();
                newRow.setAttribute('data-payment-id', payment.id);

                let formattedDate = new Date(payment.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

                newRow.insertCell().textContent = formattedDate;
                newRow.insertCell().textContent = `$${parseFloat(payment.amount).toFixed(2)}`;
                newRow.insertCell().textContent = formatPaymentMethod(payment.method);
                newRow.insertCell().textContent = payment.purpose || '';
                newRow.insertCell().textContent = payment.reference || '';
                newRow.insertCell().textContent = payment.memo || '';

                let actionCell = newRow.insertCell();
                actionCell.innerHTML = `
                    <button type="button" class="btn btn-info btn-sm" onclick="editPayment('${payment.id}', '${payment.amount}', '${payment.method}', '${payment.reference}', '${payment.memo}', '${payment.purpose}')">Edit</button>
                    <button type="button" class="btn btn-danger btn-sm" onclick="if(confirm('Are you sure?')){ window.location.href='/payments/delete_payment/${payment.id}/'; }">Delete</button>
                `;
            });
        })
        .catch(error => console.error('Error fetching existing payments:', error));
}

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    loadExistingPayments();

    let contractId = document.body.getAttribute('data-contract-id');
    let paymentScheduleId = document.body.getAttribute('data-payment-schedule-id');

    if (paymentScheduleId) {
        console.log("Payment schedule exists for contract " + contractId + ": " + paymentScheduleId);
    } else {
        console.log("No payment schedule exists for contract " + contractId);
    }

    initializeFormInputs(); // Initialize form inputs as disabled

    // Add an empty form when the modal is shown
    $('#scheduleModal').on('show.bs.modal', function () {
        addFormsetEntry('paymentScheduleEntries', 'id_schedule_payments-TOTAL_FORMS', '.payment-form');
    });

    $('#serviceFeeModal').on('show.bs.modal', function () {
        addFormsetEntry('serviceFeeEntries', 'id_servicefees-TOTAL_FORMS', '.service-fee-form');
    });

    // Handle schedule type changes
    let scheduleDropdown = document.getElementById('payment-schedule');
    let initialScheduleType = scheduleDropdown.value;
    populateScheduleTable(initialScheduleType);

    scheduleDropdown.addEventListener('change', function() {
        let selectedValue = this.value;
        let scheduleModalButton = document.querySelector('[data-target="#scheduleModal"]');

        if (selectedValue === 'custom') {
            scheduleModalButton.style.display = 'inline-block';
        } else {
            scheduleModalButton.style.display = 'none';
        }

        populateScheduleTable(selectedValue);
    });

    let scheduleSelect = document.getElementById('payment-schedule');
    scheduleSelect.setAttribute('data-original-value', scheduleSelect.value);
});
