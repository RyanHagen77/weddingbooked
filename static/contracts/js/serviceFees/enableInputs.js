// enableInputs

/**
 * Enables all inputs in the service fee form.
 */
export function enableAllServiceFeeInputs() {
    const inputs = document.querySelectorAll('#serviceFeeForm input, #serviceFeeForm select, #serviceFeeForm textarea');
    inputs.forEach(input => {
        input.disabled = false;
    });
}