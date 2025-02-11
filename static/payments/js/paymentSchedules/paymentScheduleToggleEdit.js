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

  // Update the hidden recalculation flag.
  // If any "Enable Editing" checkbox is checked, we want to preserve custom changes (so recalc = false).
  const recalcField = document.getElementById('recalculateFlag');
  if (recalcField) {
    const anyEditingEnabled = Array.from(document.querySelectorAll('.edit-toggle'))
                                   .some(cb => cb.checked);
    recalcField.value = anyEditingEnabled ? 'false' : 'true';
  }
}
