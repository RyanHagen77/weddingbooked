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

function addFormsetEntry() {
    let totalForms = document.querySelector("#id_form-TOTAL_FORMS");
    let currentTotal = parseInt(totalForms.value);
    totalForms.value = currentTotal + 1;

    // Submit the form to re-render it with the new entry
    document.getElementById("scheduleForm").submit();
}

function populateScheduleTable(scheduleType) {
    let container = document.getElementById('payment-schedule-table');
    container.innerHTML = ''; // Clear existing table content

    // Create a new table element
    let table = document.createElement('table');
    table.className = 'table'; // Add any necessary classes

    // Create table header
    let thead = table.createTHead();
    let headerRow = thead.insertRow();
    let descriptionCell = headerRow.insertCell();
    descriptionCell.textContent = 'Description';
    descriptionCell.style.fontWeight = 'bold';  // Make the text bold

    let dueDateCell = headerRow.insertCell(); // Added due date header cell
    dueDateCell.textContent = 'Due Date';
    dueDateCell.style.fontWeight = 'bold';  // Make the text bold

    let amountCell = headerRow.insertCell();
    amountCell.textContent = 'Amount';
    amountCell.style.fontWeight = 'bold';  // Make the text bold

    let statusCell = headerRow.insertCell();
    statusCell.textContent = 'Status';
    statusCell.style.fontWeight = 'bold';  // Make the text bold

    let tbody = table.createTBody();

    if (scheduleType === 'schedule_a') {
        // Calculate Schedule A details
        let depositAmount = contractData.servicesTotalAfterDiscounts * 0.40;
        let totalContractAmount = parseFloat(document.querySelector('.contract-total').getAttribute('data-contract-total'));
        let balanceAmount = totalContractAmount - depositAmount;
        let balanceDueDate = new Date(contractData.eventDate);
        balanceDueDate.setDate(balanceDueDate.getDate() - 60);

        let totalPayments = getTotalPayments(); // Get the total payments made
        let depositStatus = (totalPayments >= depositAmount - 0.01) ? 'Paid' : 'Unpaid';
        let balanceStatus = (totalPayments >= totalContractAmount) ? 'Paid' : 'Unpaid';

        // Populate the table with Schedule A details
        let depositRow = tbody.insertRow();
        depositRow.insertCell().textContent = 'Deposit';
        depositRow.insertCell().textContent = 'Upon Booking'; // Added due date for deposit
        depositRow.insertCell().textContent = `$${depositAmount.toFixed(2)}`;
        depositRow.insertCell().textContent = depositStatus;

        let balanceRow = tbody.insertRow();
        balanceRow.insertCell().textContent = `Balance Due`;
        balanceRow.insertCell().textContent = balanceDueDate.toISOString().slice(0, 10); // Added due date for balance
        balanceRow.insertCell().textContent = `$${balanceAmount.toFixed(2)}`;
        balanceRow.insertCell().textContent = balanceStatus;

        // Add rows for service fees or additional entries
        let serviceFeeRow = tbody.insertRow();
        serviceFeeRow.insertCell().textContent = 'Service Fee'; // Example fee description
        serviceFeeRow.insertCell().textContent = '2024-06-01'; // Example due date
        serviceFeeRow.insertCell().textContent = '$100.00'; // Example fee amount
        serviceFeeRow.insertCell().textContent = 'Unpaid'; // Default status

        // Repeat the above for additional fees or entries as needed
    } else if (scheduleType === 'custom') {
        // Fetch and populate the table with custom schedule data
        let contractId = document.body.getAttribute('data-contract-id');
        fetch(`/contracts/${contractId}/get_custom_schedule/`)
            .then(response => response.json())
            .then(data => {
                data.forEach(payment => {
                    let row = tbody.insertRow();
                    row.insertCell().textContent = payment.purpose;
                    row.insertCell().textContent = payment.due_date; // Added due date for custom payment
                    row.insertCell().textContent = `$${payment.amount}`;
                    row.insertCell().textContent = payment.paid ? 'Paid' : 'Unpaid';
                });
            })
            .catch(error => console.error('Error fetching custom schedule:', error));
    }

    // Append the table to the container
    container.appendChild(table);

    // Call updateDepositStatus after the table is populated
    updateDepositStatus();
}

function handleScheduleChange(scheduleType) {
    populateScheduleTable(scheduleType);
    let scheduleModalButton = document.querySelector('[data-target="#scheduleModal"]');

    if (scheduleType === 'custom') {
        scheduleModalButton.style.display = 'inline-block'; // Show the "Add or Update Schedule" button
    } else {
        scheduleModalButton.style.display = 'none'; // Hide the button
    }
}



function receivePayment() {
    let scheduleType = document.getElementById('payment-schedule').value;

    if (scheduleType === 'schedule_a') {
        // For Schedule A, set the amount to an empty string
        document.getElementById('amount').value = '';
    } else if (scheduleType === 'custom') {
        // For custom schedule, set the amount to the next unpaid payment
        let payments = document.querySelectorAll('.payments-content .table tbody tr');
        let nextPaymentAmount = '';
        for (let row of payments) {
            let statusCell = row.cells[row.cells.length - 1];
            if (statusCell.textContent.trim() === 'Unpaid') {
                nextPaymentAmount = row.cells[1].textContent.replace('$', '').trim();
                break;
            }
        }
        document.getElementById('amount').value = nextPaymentAmount;
    } else {
        // For other schedule types, set the amount to an empty string
        document.getElementById('amount').value = '';
    }

    $('#paymentModal').modal('show');
}


// Function to calculate the total payments made
function getTotalPayments() {
    let paymentsTableBody = document.querySelector('.existing-payments-table tbody');
    let totalPayments = 0;

    for (let row of paymentsTableBody.rows) {
        totalPayments += parseFloat(row.cells[1].textContent.replace('$', ''));
    }

    return totalPayments;
}




function confirmPayment() {
    let paymentAmount = parseFloat(document.getElementById('amount').value);
    let balanceDueElement = document.getElementById('balance-due-amount');
    let balanceDue = parseFloat(balanceDueElement.textContent.replace('$', ''));
    let paymentMethod = document.getElementById('payment_method').value;
    let paymentMemo = document.getElementById('memo').value;
    let paymentReference = document.getElementById('payment_reference').value;
    let paymentId = document.getElementById('payment-id').value;
    let paymentAction = document.getElementById('payment-action').value;
    let url = (paymentAction === 'edit') ? `/contracts/edit_payment/${paymentId}/` : `/contracts/add_payment/${contractData.paymentScheduleId}/`;

    // Check if payment amount exceeds balance due
    if (paymentAmount > balanceDue) {
        alert('Payment amount exceeds the remaining balance. Please enter a valid amount.');
        return;
    }

    let formData = new FormData();
    formData.append('amount', paymentAmount);
    formData.append('payment_method', paymentMethod);
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
        updatePaymentsTable(paymentAmount, paymentMethod, paymentReference, paymentMemo, data.payment_id, paymentAction);

        // Recalculate the balance due
        let newBalanceDue = balanceDue - paymentAmount;
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

function clearPaymentForm() {
    document.getElementById('payment-form').reset();
    document.getElementById('payment-id').value = '';
    document.getElementById('payment-action').value = 'add';
}


function editPayment(paymentId, amount, paymentMethod, paymentReference, memo) {
    document.getElementById('payment-id').value = paymentId;
    document.getElementById('amount').value = amount;
    document.getElementById('payment_method').value = paymentMethod;
    document.getElementById('payment_reference').value = paymentReference;
    document.getElementById('memo').value = memo;
    document.getElementById('payment-action').value = 'edit';
    $('#paymentModal').modal('show');
}


function updatePaymentsTable(paymentAmount, paymentMethod, paymentReference, paymentMemo, paymentId, paymentAction) {
    let paymentsTableBody = document.querySelector('.existing-payments-table tbody');

    if (paymentAction === 'edit') {
        // Update the existing payment row
        let rowToUpdate = paymentsTableBody.querySelector(`tr[data-payment-id="${paymentId}"]`);
        if (rowToUpdate) {
            rowToUpdate.cells[1].textContent = `$${paymentAmount.toFixed(2)}`;
            rowToUpdate.cells[2].textContent = paymentMethod;
            rowToUpdate.cells[3].textContent = paymentReference;
            rowToUpdate.cells[4].textContent = paymentMemo;
        }
    } else {
        // Add a new row for the payment
        let newRow = paymentsTableBody.insertRow();
        newRow.setAttribute('data-payment-id', paymentId);

        let currentDate = new Date();
        let formattedDate = currentDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

        newRow.insertCell().textContent = formattedDate;
        newRow.insertCell().textContent = `$${paymentAmount.toFixed(2)}`;
        newRow.insertCell().textContent = paymentMethod;
        newRow.insertCell().textContent = paymentReference;
        newRow.insertCell().textContent = paymentMemo;
    }

    // Update the balance due if necessary
    updateBalanceDue(paymentAmount);
}



function updateDepositStatus() {
    let scheduleType = document.getElementById('payment-schedule').value;
    let depositRow = document.querySelector('.payments-content .table tbody tr:first-child');
    let balanceRow = document.querySelector('.payments-content .table tbody tr:last-child');
    let totalContractAmount = parseFloat(document.querySelector('.contract-total').getAttribute('data-contract-total'));
    let totalPayments = getTotalPayments();

    if (scheduleType === 'schedule_a') {
        let depositAmount = parseFloat(depositRow.cells[2].textContent.replace('$', ''));
        depositRow.cells[3].textContent = totalPayments >= depositAmount ? 'Paid' : 'Unpaid';
        totalPayments -= depositAmount;  // Subtract the deposit amount from total payments
        balanceRow.cells[3].textContent = totalPayments >= totalContractAmount - depositAmount ? 'Paid' : 'Unpaid';
    } else if (scheduleType === 'custom') {
        let paymentRows = document.querySelectorAll('.payments-content .table tbody tr');
        for (let row of paymentRows) {
            let paymentAmount = parseFloat(row.cells[2].textContent.replace('$', ''));
            row.cells[3].textContent = totalPayments >= paymentAmount ? 'Paid' : 'Unpaid';
            totalPayments -= paymentAmount;  // Subtract the payment amount from total payments
        }
    }
}



function updateBalanceDue(paymentAmount, paymentAction) {
    let balanceDueElement = document.getElementById('balance-due-amount');
    let initialBalance = parseFloat(document.querySelector('.balance-due').getAttribute('data-initial-balance'));
    let totalPayments = getTotalPayments();

    // Calculate new balance
    let newBalance = initialBalance - totalPayments;

    // Update the balance due element
    balanceDueElement.textContent = '$' + newBalance.toFixed(2);
}



document.addEventListener('DOMContentLoaded', function() {

    let contractId = document.body.getAttribute('data-contract-id');
    let paymentScheduleId = document.body.getAttribute('data-payment-schedule-id');

    if (paymentScheduleId) {
        console.log("Payment schedule exists for contract " + contractId + ": " + paymentScheduleId);
    } else {
        console.log("No payment schedule exists for contract " + contractId);
    }

    let scheduleDropdown = document.getElementById('payment-schedule');
    let initialScheduleType = scheduleDropdown.value;
    populateScheduleTable(initialScheduleType);


    scheduleDropdown.addEventListener('change', function() {
        let selectedValue = this.value;
        let scheduleModalButton = document.querySelector('[data-target="#scheduleModal"]');

        if (selectedValue === 'custom') {
            scheduleModalButton.style.display = 'inline-block'; // Show the "Add or Update Schedule" button
        } else {
            scheduleModalButton.style.display = 'none'; // Hide the button
        }


        populateScheduleTable(selectedValue);
    });


        let scheduleSelect = document.getElementById('payment-schedule');
    scheduleSelect.setAttribute('data-original-value', scheduleSelect.value);

    // Other initialization code...
});

