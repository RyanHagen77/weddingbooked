// serviceFeeEvents

import { populateServiceFeeTable } from "./serviceFeeManager.js";

export function initializeServiceFeeEvents() {
  // (Optional) If you have a dropdown to filter service fee data, attach its event listener:
  const feeDropdown = document.getElementById('service-fee-dropdown');
  if (feeDropdown) {
    // Set initial table
    const initialFeeType = feeDropdown.value;
    populateServiceFeeTable(initialFeeType);

    feeDropdown.addEventListener('change', function() {
      const selectedValue = this.value;
      populateServiceFeeTable(selectedValue);
    });
  }

  // When the service fee modal is shown, disable all inputs in the fee entries and uncheck all edit toggles.
  $('#serviceFeeModal').on('show.bs.modal', () => {
    // Lock existing fee entries if the key field (e.g., fee amount with class "key-field") is non-empty.
    const feeForms = document.querySelectorAll('#serviceFeeForm .service-fee-form');
    feeForms.forEach(form => {
      const checkbox = form.querySelector('.edit-toggle');
      const inputs = form.querySelectorAll('.form-fields input, .form-fields select, .form-fields textarea');
      let keyInput = form.querySelector('.form-fields .key-field');
      if (!keyInput) {
        // Fallback to first input if key-field class is not set.
        keyInput = form.querySelector('.form-fields input');
      }
      if (checkbox) {
        if (keyInput && keyInput.value.trim() !== "") {
          // Existing fee: lock the inputs and uncheck the checkbox.
          inputs.forEach(input => input.disabled = true);
          checkbox.checked = false;
        } else {
          // Blank fee: leave inputs enabled and check the checkbox.
          inputs.forEach(input => input.disabled = false);
          checkbox.checked = true;
        }
      } else {
        inputs.forEach(input => input.disabled = false);
      }
    });
  });
      // Uncheck all delete tickboxes so none are pre-marked.
  const deleteBoxes = document.querySelectorAll('#serviceFeeForm input[name$="-DELETE"]');
  deleteBoxes.forEach(box => {
    box.checked = false;
  });
}
