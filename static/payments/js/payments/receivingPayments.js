// receivingPayments.js

import { formatPaymentMethod } from './paymentHelpers.js';
import { updateDepositStatus, populateScheduleTable } from '..***REMOVED***.js';

/**
 * Utility: Get CSRF Token (used for secure POST requests)
 */
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

/**
 * Opens the payment modal.
 */
export function receivePayment() {
    // Clear the amount field.
    document.getElementById('amount').value = '';
    $('#paymentModal').modal('show');
}

/**
 * Submits a new payment or edits an existing one.
 */
export function confirmPayment() {
    const paymentAmount = parseFloat(document.getElementById('amount').value);
    // Use querySelector to get an element with the class "balance-due-amount"
    const balanceDueElement = document.querySelector('.balance-due-amount');
    if (!balanceDueElement) {
        console.error("No element with class 'balance-due-amount' found.");
        return;
    }
    const balanceDue = parseFloat(balanceDueElement.textContent.replace('$', ''));
    const paymentMethod = document.getElementById('payment_method').value;
    const paymentPurposeElement = document.getElementById('payment_purpose');
    const paymentPurpose = paymentPurposeElement.value;
    const paymentPurposeText = paymentPurposeElement.options[paymentPurposeElement.selectedIndex].text;
    const paymentMemo = document.getElementById('memo').value;
    const paymentReference = document.getElementById('payment_reference').value;
    const paymentId = document.getElementById('payment-id').value;
    const paymentAction = document.getElementById('payment-action').value;

    // Determine URL based on whether this is an edit or new payment.
    const url = (paymentAction === 'edit')
        ? `/payments/edit_payment/${paymentId}/`
        : `/payments/add_payment/${contractData.paymentScheduleId}/`;

    const originalAmount = parseFloat(document.getElementById('original-amount').value) || 0;
    const amountDifference = paymentAmount - originalAmount;

    // Validate that the payment does not exceed the remaining balance.
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
        if (response.ok) return response.json();
        else throw new Error('Error saving payment');
    })
    .then(data => {
        // Update payments table, balance due, and amount paid.
        updatePaymentsTable(paymentAmount, paymentMethod, paymentPurposeText, paymentReference, paymentMemo, data.payment_id, paymentAction);

        const newBalanceDue = balanceDue - amountDifference;
        balanceDueElement.textContent = `$${newBalanceDue.toFixed(2)}`;

        updateAmountPaid(paymentAmount);

        // Update contract status in the UI.
        document.getElementById("id_status").value = data.new_status;
        document.querySelector("#contract-status").textContent = `Status: ${data.new_status_display}`;

        // Delay refreshing the schedule table and contract summary.
        setTimeout(() => {
            const scheduleDropdown = document.getElementById('payment-schedule');
            const currentScheduleType = scheduleDropdown ? scheduleDropdown.value : 'schedule_a';
            populateScheduleTable(currentScheduleType);
            updateDepositStatus();
            updateContractSummary();
        }, 300);

        clearPaymentForm();
    })
    .catch(error => console.error('Error saving payment:', error));

    // Ensure the form is cleared when the modal is hidden.
    $('#paymentModal').on('hidden.bs.modal', clearPaymentForm);
    $('#paymentModal').modal('hide');
}

/**
 * Clears the payment form for the next transaction.
 */
export function clearPaymentForm() {
    document.getElementById('payment-form').reset();
    document.getElementById('payment-id').value = '';
    document.getElementById('payment-action').value = 'add';
    document.getElementById('original-amount').value = '';
}

/**
 * Pre-fills the payment modal for editing an existing payment.
 */
export function editPayment(paymentId, amount, paymentMethod, paymentReference, memo, paymentPurpose) {
    document.getElementById('payment-id').value = paymentId;
    document.getElementById('original-amount').value = amount;
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

/**
 * Deletes a payment.
 */
export function deletePayment(paymentId) {
    if (confirm('Are you sure you want to delete this payment?')) {
        fetch(`/payments/delete_payment/${paymentId}/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
        })
        .then(response => {
            if (response.ok) return response.json();
            else throw new Error('Error deleting payment');
        })
        .then(data => {
            if (data.success) {
                const paymentsTableBody = document.querySelector('.existing-payments-table tbody');
                const rowToDelete = paymentsTableBody.querySelector(`tr[data-payment-id="${paymentId}"]`);
                if (rowToDelete) {
                    const paymentAmountText = rowToDelete.cells[1].textContent;
                    const paymentAmount = parseFloat(paymentAmountText.replace('$', ''));
                    updateBalanceDue(-paymentAmount);
                    updateAmountPaid(-paymentAmount);
                    rowToDelete.remove();
                    updateContractSummary();
                }
                setTimeout(() => {
                    const scheduleDropdown = document.getElementById('payment-schedule');
                    const currentScheduleType = scheduleDropdown ? scheduleDropdown.value : 'schedule_a';
                    populateScheduleTable(currentScheduleType);
                    updateDepositStatus();
                    updateContractSummary();
                }, 300);
            } else {
                alert('Failed to delete payment.');
            }
        })
        .catch(error => console.error('Error deleting payment:', error));
    }
}
window.deletePayment = deletePayment;

/**
 * Updates the payments table with a new or updated payment.
 */
export function updatePaymentsTable(paymentAmount, paymentMethod, paymentPurpose, paymentReference, paymentMemo, paymentId, paymentAction) {
    const paymentsTableBody = document.querySelector('.existing-payments-table tbody');

    if (paymentAction === 'edit') {
        const rowToUpdate = paymentsTableBody.querySelector(`tr[data-payment-id="${paymentId}"]`);
        if (rowToUpdate) {
            rowToUpdate.cells[1].textContent = `$${paymentAmount.toFixed(2)}`;
            rowToUpdate.cells[2].textContent = formatPaymentMethod(paymentMethod);
            rowToUpdate.cells[3].textContent = paymentPurpose;
            rowToUpdate.cells[4].textContent = paymentReference;
            rowToUpdate.cells[5].textContent = paymentMemo;
        }
    } else {
        const newRow = paymentsTableBody.insertRow();
        newRow.setAttribute('data-payment-id', paymentId);

        const currentDate = new Date();
        const formattedDate = currentDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

        newRow.insertCell().textContent = formattedDate;
        newRow.insertCell().textContent = `$${paymentAmount.toFixed(2)}`;
        newRow.insertCell().textContent = formatPaymentMethod(paymentMethod);
        newRow.insertCell().textContent = paymentPurpose;
        newRow.insertCell().textContent = paymentReference;
        newRow.insertCell().textContent = paymentMemo;

        const actionCell = newRow.insertCell();
        actionCell.innerHTML = `
            <button type="button" class="btn btn-info btn-sm" onclick="window.editPayment('${paymentId}', '${paymentAmount}', '${paymentMethod}', '${paymentReference}', '${paymentMemo}', '${paymentPurpose}')">Edit</button>
            <button type="button" class="btn btn-danger btn-sm" onclick="deletePayment('${paymentId}')">Delete</button>
        `;
    }
    updateBalanceDue(paymentAmount);
}

/**
 * Updates the amount paid display.
 */
export function updateAmountPaid(paymentAmount) {
    const amountPaidElement = document.getElementById('amount-paid-amount');
    const currentAmountPaid = parseFloat(amountPaidElement.textContent.replace('$', '')) || 0;
    const newAmountPaid = currentAmountPaid + paymentAmount;
    amountPaidElement.textContent = `$${newAmountPaid.toFixed(2)}`;
}

/**
 * Updates the displayed balance due.
 */
export function updateBalanceDue(paymentAmount) {
    const balanceDueElements = document.querySelectorAll('.balance-due-amount');
    balanceDueElements.forEach(elem => {
        const currentValue = elem.textContent.replace(/[^0-9.-]+/g, '');
        const balanceDue = parseFloat(currentValue) || 0;
        const newBalanceDue = balanceDue - paymentAmount;
        elem.textContent = `$${newBalanceDue.toFixed(2)}`;
    });
}

/**
 * Loads and displays existing payments when the page loads.
 */
export function loadExistingPayments() {
    const contractId = document.body.getAttribute('data-contract-id');
    fetch(`/payments/${contractId}/get_existing_payments/`)
        .then(response => response.json())
        .then(data => {
            const paymentsTableBody = document.querySelector('.existing-payments-table tbody');
            paymentsTableBody.innerHTML = '';

            data.forEach(payment => {
                const newRow = paymentsTableBody.insertRow();
                newRow.setAttribute('data-payment-id', payment.id);

                const formattedDate = new Date(payment.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
                newRow.insertCell().textContent = formattedDate;
                newRow.insertCell().textContent = `$${parseFloat(payment.amount).toFixed(2)}`;
                newRow.insertCell().textContent = formatPaymentMethod(payment.method);
                newRow.insertCell().textContent = payment.purpose || '';
                newRow.insertCell().textContent = payment.reference || '';
                newRow.insertCell().textContent = payment.memo || '';

                const actionCell = newRow.insertCell();
                actionCell.innerHTML = `
                    <button type="button" class="btn btn-info btn-sm" onclick="window.editPayment('${payment.id}', '${payment.amount}', '${payment.method}', '${payment.reference}', '${payment.memo}', '${payment.purpose}')">Edit</button>
                    <button type="button" class="btn btn-danger btn-sm" onclick="deletePayment('${payment.id}')">Delete</button>
                `;
            });
        })
        .catch(error => console.error('Error fetching existing payments:', error));
}

// Expose editPayment to the global scope so inline event handlers work.
window.editPayment = editPayment;

// Initialize receiving payments when the DOM is ready.
document.addEventListener('DOMContentLoaded', function() {
    loadExistingPayments();

    const receivePaymentBtn = document.getElementById('receivePaymentBtn');
    if (receivePaymentBtn) {
        receivePaymentBtn.addEventListener('click', receivePayment);
    }
});

/**
 * Updates the contract summary fields (Next Payment Due and Due Date)
 * by reading the current schedule table.
 */
export function updateContractSummary() {
    console.log("Updating contract summary...");
    const container = document.getElementById('payment-schedule-table');
    if (!container) {
        console.error("No element with ID 'payment-schedule-table' found.");
        return;
    }
    const table = container.querySelector('table');
    if (!table) {
        console.error("No table found in #payment-schedule-table.");
        return;
    }
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error("No tbody found in the schedule table.");
        return;
    }
    let nextPaymentDue = null;
    let dueDate = null;
    const rows = tbody.querySelectorAll('tr');
    for (let row of rows) {
        const status = row.cells[3].textContent.trim().toLowerCase();
        if (status === 'unpaid') {
            nextPaymentDue = row.cells[2].textContent;
            dueDate = row.cells[1].textContent;
            break;
        }
    }
    if (nextPaymentDue === null) {
        nextPaymentDue = "$0.00";
        dueDate = "All payments complete";
    }
    console.log("Next Payment Due:", nextPaymentDue, "Due Date:", dueDate);
    const paymentAmountDueElem = document.getElementById('payment-amount-due');
    if (paymentAmountDueElem) {
        paymentAmountDueElem.textContent = `Next Payment Due: ${nextPaymentDue}`;
    }
    const dueDateElem = document.getElementById('due-date');
    if (dueDateElem) {
        dueDateElem.textContent = `Due Date: ${dueDate}`;
    }
}
