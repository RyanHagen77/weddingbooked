// paymentHelpers.js

export function getTotalPayments() {
    const paymentsTableBody = document.querySelector('.existing-payments-table tbody');
    let totalPayments = 0;

    if (paymentsTableBody) {
        for (let row of paymentsTableBody.rows) {
            totalPayments += parseFloat(row.cells[1].textContent.replace('$', ''));
        }
    }
    return totalPayments;
}

export function formatPaymentMethod(method) {
    const methodMapping = {
        'CASH': 'Cash',
        'CHECK': 'Check',
        'CREDIT_CARD': 'Credit Card',
        'ZELLE': 'Zelle',
        'VENMO': 'Venmo'
    };
    return methodMapping[method] || method;
}
