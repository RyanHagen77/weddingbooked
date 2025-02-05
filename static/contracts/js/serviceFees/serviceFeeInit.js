// serviceFeeInit

import { addServiceFeeEntry, confirmServiceFee } from "./serviceFeeManager.js";
import { toggleEditServiceFee } from "./serviceFeeToggleEdit.js";
import { initializeServiceFeeEvents } from "./serviceFeeEvents.js";

document.addEventListener("DOMContentLoaded", () => {
  initializeServiceFeeEvents();

  const addFeeBtn = document.getElementById('addServiceFeeBtn');
  if (addFeeBtn) {
    addFeeBtn.addEventListener('click', () => {
      addServiceFeeEntry("serviceFeeEntries", "id_servicefees-TOTAL_FORMS", ".service-fee-form");
    });
  } else {
    console.warn("Add Service Fee button not found.");
  }

  const saveFeeBtn = document.getElementById('saveServiceFeeBtn');
  if (saveFeeBtn) {
    saveFeeBtn.addEventListener('click', (event) => {
      event.preventDefault();
      confirmServiceFee();
    });
  } else {
    console.warn("Save Service Fee button not found.");
  }

  // Attach listeners to existing edit-toggle checkboxes.
  const editToggles = document.querySelectorAll('#serviceFeeForm .edit-toggle');
  editToggles.forEach(checkbox => {
    checkbox.addEventListener('click', () => {
      toggleEditServiceFee(checkbox);
    });
  });
});
