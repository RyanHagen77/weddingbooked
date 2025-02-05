// serviceFeeManager

import { enableAllServiceFeeInputs } from "./enableInputs.js"; // Function to enable inputs
import { getCookie } from "../contractsHelpers.js";
import { updateBalanceDue, updateContractSummary } from "../../../payments/js/payments/receivingPayments.js";


export function populateServiceFeeTable() {
  const contractId = document.body.getAttribute('data-contract-id');
  if (!contractId) {
    console.error("No contract ID found in body data attributes.");
    return;
  }

  const url = `/contracts/get_service_fees/${contractId}/`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      let html = '';
      if (data.length > 0) {
        html += '<table class="table table-striped"><thead><tr>';
        html += '<th>Date Applied</th>';
        html += '<th>Description</th>';
        html += '<th>Fee Type</th>';
        html += '<th>Amount</th>';
        html += '</tr></thead><tbody>';
        data.forEach(fee => {
          html += `<tr>
            <td>${fee.applied_date}</td>
            <td>${fee.description}</td>
            <td>${fee.fee_type}</td>
            <td>$${parseFloat(fee.amount).toFixed(2)}</td>
          </tr>`;
        });
        html += '</tbody></table>';
      } else {
        html = '<p>No service fees found.</p>';
      }
      const tableContainer = document.getElementById('serviceFeeTableContainer');
      if (tableContainer) {
        tableContainer.innerHTML = html;
      }
    })
    .catch(error => console.error("Error fetching service fees:", error));
}

/**
 * Adds a new service fee entry by cloning the empty template.
 * Replaces __prefix__ with a computed index based on the current number of fee forms.
 */
export function addServiceFeeEntry(containerId, totalFormsId, formClass) {
  const container = document.getElementById(containerId);
  const totalForms = document.getElementById(totalFormsId);
  if (!container || !totalForms) {
    console.error("addServiceFeeEntry: Container or management form not found.");
    return;
  }
  const emptyTemplate = document.querySelector('.empty-service-fee-form');
  if (!emptyTemplate) {
    console.error("addServiceFeeEntry: Empty service fee form template not found.");
    return;
  }
  // Calculate the new index based on the number of fee forms (including hidden ones)
  const feeForms = container.querySelectorAll('.service-fee-form');
  const formIndex = feeForms.length; // This will be 0 if none exist, 1 if one exists, etc.

  // Replace all __prefix__ placeholders with the computed index.
  let newFormHTML = emptyTemplate.innerHTML.replace(/__prefix__/g, formIndex);

  // Create a new container for the cloned form.
  const newForm = document.createElement('div');
  newForm.classList.add('service-fee-form', 'mb-3');
  newForm.innerHTML = newFormHTML;
  newForm.style.display = '';

  container.appendChild(newForm);
  totalForms.value = feeForms.length + 1;

  // Dispatch custom event to update UI:
  document.dispatchEvent(new Event('feeUpdated'));
}

/**
 * Submits the service fee form via AJAX.
 * On success, hides the modal and, after a short delay, re-fetches the updated fee entries and updates the contract summary.
 * The formset remains locked (inputs disabled) until the user checks the "Enable Editing" tickbox.
 */
export function confirmServiceFee() {
  enableAllServiceFeeInputs()
  // Do NOT automatically enable inputs; require the user to check the edit toggle.
  const form = document.getElementById('serviceFeeForm');
  if (!form) {
    console.error("confirmServiceFee: Service fee form not found.");
    return;
  }
  const url = form.getAttribute('action');
  const formData = new FormData(form);
  const csrfToken = getCookie('csrftoken');

  fetch(url, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: formData
  })
  .then(response => {
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
      return response.json();
    } else {
      return response.text();
    }
  })
  .then(data => {
    if (typeof data === "object" && data.success) {
      console.log("Service fee saved successfully:", data);
      $('#serviceFeeModal').modal('hide');
      // Delay the refresh so that the updated fee entries and totals are available.
      setTimeout(() => {
        fetchServiceFees();
        updateContractSummary();
        // Optionally, update balance due if fees affect it:
        updateBalanceDue(0); // Pass 0 if no direct fee amount adjustment is needed.
      }, 300);
    } else {
      console.log("Service fee save failed. Response:", data);
    }
  })
  .catch(error => {
    console.error("Error saving service fee:", error);
  });
}
/**
 * Fetches the updated fee entries from the server and updates the container.
 * Assumes your get_service_fees view returns HTML for the fee entries.
 */
export function fetchServiceFees() {
  const contractId = document.body.getAttribute('data-contract-id');
  if (!contractId) {
    console.error("No contract id found on body.");
    return;
  }
  fetch(`/contracts/get_service_fees/${contractId}/`)
    .then(response => response.text())
    .then(html => {
      const container = document.getElementById('serviceFeeEntries');
      if (container) {
        container.innerHTML = html;
      }
    })
    .catch(error => console.error("Error fetching service fees:", error));
}

/**
 * Toggles editing for a service fee form entry.
 * If the edit-toggle checkbox is checked, enable inputs; otherwise, disable them.
 */


/**
 * Removes a service fee entry.
 * For an existing fee (with an id and DELETE field), mark it for deletion and hide the form.
 * For a new fee (without an id), remove it from the DOM and update TOTAL_FORMS.
 */

