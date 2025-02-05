// scheduleToggleEdit.js

/**
 * Toggles the disabled state of all input, select, and textarea elements
 * inside the nearest element with the class "form-fields" that is a child
 * of the closest parent with the class "payment-form".
 *
 * @param {HTMLInputElement} checkbox - The checkbox that triggered the event.
 */

// paymentScheduleToggleEdit.js
export function toggleEditSchedule(checkbox) {
  const parentForm = checkbox.closest('.schedule-payment-form');
  if (!parentForm) return;
  const formFields = parentForm.querySelector('.form-fields');
  if (!formFields) return;
  const inputs = formFields.querySelectorAll('input, select, textarea');
  // Toggle the disabled state based on whether the checkbox is checked.
  inputs.forEach(input => {
    input.disabled = !checkbox.checked;
  });
}

