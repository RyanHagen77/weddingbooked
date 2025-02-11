
// paymentScheduleManager.js
import { getTotalPayments } from "../payments/paymentHelpers.js";

/**
 * Populates the payment schedule table based on the provided schedule type.
 * Clears any existing table content, creates a new table with headers,
 * populates it with rows from either schedule A or custom schedule,
 * and finally updates the deposit status.
 */
export function populateScheduleTable(scheduleType) {
    const container = document.getElementById('payment-schedule-table');
    if (!container) {
        console.error("No element with ID 'payment-schedule-table' found.");
        return;
    }
    container.innerHTML = ''; // Clear existing table content

    const table = document.createElement('table');
    table.className = 'table';

    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    createHeaderCell(headerRow, 'Description');
    createHeaderCell(headerRow, 'Due Date');
    createHeaderCell(headerRow, 'Amount');
    createHeaderCell(headerRow, 'Status');

    const tbody = table.createTBody();

    if (scheduleType === 'schedule_a') {
        populateScheduleA(tbody);
    } else if (scheduleType === 'custom') {
        populateCustomSchedule(tbody);
    }

    container.appendChild(table);
    updateDepositStatus();
}

/**
 * Creates a header cell in the provided row with the given text.
 */
function createHeaderCell(row, text) {
    const cell = row.insertCell();
    cell.textContent = text;
    cell.style.fontWeight = 'bold';
}

/**
 * Populates the table body for Schedule A.
 * Assumes that the total contract amount is stored in an element with class "contract-total"
 * as a data attribute, and that global contractData contains an event_date property.
 */
export function populateScheduleA(tbody) {
    const totalContractAmount = parseFloat(
        document.querySelector('.contract-total').getAttribute('data-contract-total')
    );

    // Compute half, then simulate rounding to the nearest hundred.
    const rawDeposit = totalContractAmount * 0.5;
    // Divide by 100, round using Math.round (which rounds half up), then multiply by 100.
    const depositAmount = Math.round(rawDeposit / 100) * 100;
    const balanceAmount = totalContractAmount - depositAmount;

    // Use event_date from global contractData (make sure it's defined)
    const balanceDueDate = new Date(window.contractData.event_date);
    balanceDueDate.setDate(balanceDueDate.getDate() - 60);

    const totalPayments = getTotalPayments();
    const depositStatus = (totalPayments >= depositAmount - 0.01) ? 'Paid' : 'Unpaid';
    const balanceStatus = (totalPayments >= totalContractAmount) ? 'Paid' : 'Unpaid';

    addScheduleRow(tbody, 'Deposit', 'Upon Booking', depositAmount, depositStatus);
    addScheduleRow(tbody, 'Balance Due', balanceDueDate.toISOString().slice(0, 10), balanceAmount, balanceStatus);
}


/**
 * Populates the table body for a custom schedule by fetching data via AJAX.
 */
export function populateCustomSchedule(tbody) {
    const contractId = document.body.getAttribute('data-contract-id');
    fetch(`/payments/${contractId}/get_custom_schedule/`)
        .then(response => response.json())
        .then(data => {
            let totalPayments = getTotalPayments();
            data.forEach(payment => {
                const status = totalPayments >= parseFloat(payment.amount) ? 'Paid' : 'Unpaid';
                addScheduleRow(tbody, payment.purpose, payment.due_date, parseFloat(payment.amount), status);
                totalPayments -= parseFloat(payment.amount);
            });
        })
        .catch(error => console.error('Error fetching custom schedule:', error));
}

/**
 * Inserts a new row into the provided table body with the given schedule data.
 */
export function addScheduleRow(tbody, description, dueDate, amount, status) {
    const row = tbody.insertRow();
    row.insertCell().textContent = description;
    row.insertCell().textContent = dueDate;
    row.insertCell().textContent = `$${amount.toFixed(2)}`;
    row.insertCell().textContent = status;
}

/**
 * Updates the deposit status based on the current payments.
 * This function assumes that the schedule type is available in the
 * <select id="payment-schedule"> element, and that the contract total is
 * stored in an element with class "contract-total".
 */
export function updateDepositStatus() {
    const scheduleType = document.getElementById('payment-schedule').value;
    const totalContractAmount = parseFloat(
        document.querySelector('.contract-total').getAttribute('data-contract-total')
    );
    let totalPayments = getTotalPayments();

    // Target the schedule table inside its container.
    const container = document.getElementById('payment-schedule-table');
    if (!container) {
        console.error("No element with ID 'payment-schedule-table' found.");
        return;
    }
    const table = container.querySelector('table');
    if (!table) {
        console.error("No table found inside #payment-schedule-table.");
        return;
    }
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error("No tbody found in the schedule table.");
        return;
    }

    if (scheduleType === 'schedule_a') {
        const rows = tbody.querySelectorAll('tr');
        if (rows.length >= 2) {
            const depositRow = rows[0];
            const balanceRow = rows[rows.length - 1];
            const depositAmount = parseFloat(depositRow.cells[2].textContent.replace('$', ''));
            depositRow.cells[3].textContent = totalPayments >= depositAmount ? 'Paid' : 'Unpaid';
            totalPayments -= depositAmount;
            balanceRow.cells[3].textContent = totalPayments >= (totalContractAmount - depositAmount) ? 'Paid' : 'Unpaid';
        }
    } else if (scheduleType === 'custom') {
        const rows = tbody.querySelectorAll('tr');
        rows.forEach(row => {
            const paymentAmount = parseFloat(row.cells[2].textContent.replace('$', ''));
            row.cells[3].textContent = totalPayments >= paymentAmount ? 'Paid' : 'Unpaid';
            totalPayments -= paymentAmount;
        });
    }
}


/**
 * Handles schedule change events by repopulating the schedule table and
 * adjusting the display of the schedule modal button.
 */
export function handleScheduleChange(scheduleType) {
    populateScheduleTable(scheduleType);
    const scheduleModalButton = document.querySelector('[data-target="#scheduleModal"]');
    if (scheduleModalButton) {
        scheduleModalButton.style.display = (scheduleType === 'custom') ? 'inline-block' : 'none';
    }
}
