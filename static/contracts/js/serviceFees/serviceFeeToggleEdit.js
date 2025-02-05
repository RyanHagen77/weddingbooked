// serviceFeeToggleEdit

/**
 * Toggles the edit state for a service fee form entry.
 * Disables/enables all inputs within the form's .form-fields.
 * @param {HTMLElement} checkbox - The checkbox element.
 */
// serviceFeeToggleEdit.js
export function toggleEditServiceFee(checkbox) {
  const formFields = checkbox.closest('.service-fee-form').querySelector('.form-fields');
  if (!formFields) {
    console.error("toggleEditServiceFee: No .form-fields found.");
    return;
  }
  const inputs = formFields.querySelectorAll('input, select, textarea');
  inputs.forEach(input => {
    input.disabled = !checkbox.checked;
  });
}

