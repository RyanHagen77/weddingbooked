// enableInputs.js
export function enablePaymentScheduleInputs() {
    const inputs = document.querySelectorAll('#scheduleForm input, #scheduleForm select, #scheduleForm textarea');
    inputs.forEach(input => input.disabled = false);
}
