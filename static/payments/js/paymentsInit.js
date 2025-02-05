// paymentsInit.js

// Import payment schedule initialization functions.
import { toggleEditSchedule } from ".***REMOVED***dit.js";
import { addPaymentScheduleFormsetEntry } from "./formsetUtils.js";
import { enablePaymentScheduleInputs } from "./paymentSchedules/enableInputs.js";
import { initializeScheduleEvents } from "./paymentSchedules/paymentScheduleEvents.js"; // Correct file
import { handleScheduleChange } from ".***REMOVED***.js"; // Correct file
// Import receive payment initialization.
import { initializeReceivePaymentHandler } from "./payments/receivePaymentHandler.js";



// Now, create a single DOMContentLoaded handler.
document.addEventListener('DOMContentLoaded', () => {

  // *** Payment Schedule Modal Initialization ***

  // When the schedule modal is about to be shown, disable all inputs in each schedule entry.
  $('#scheduleModal').on('show.bs.modal', () => {
    const inputs = document.querySelectorAll(
      '.schedule-payment-form .form-fields input, ' +
      '.schedule-payment-form .form-fields select, ' +
      '.schedule-payment-form .form-fields textarea'
    );
    inputs.forEach(input => {
      input.disabled = true;
    });
  });

  // Attach event listeners to all checkboxes for editing schedule entries.
  const editToggles = document.querySelectorAll('.edit-toggle');
  editToggles.forEach(toggle => {
    toggle.addEventListener('click', event => {
      toggleEditSchedule(event.currentTarget);
    });
  });

  // Attach event listener for the "Add Payment Entry" button.
  const addEntryBtn = document.getElementById('addEntryBtn');
  if (addEntryBtn) {
    addEntryBtn.addEventListener('click', () => {
      addPaymentScheduleFormsetEntry('paymentScheduleEntries', 'id_schedule_payments-TOTAL_FORMS', '.schedule-payment-form');
    });
  } else {
    console.warn("Add Payment Entry button not found.");
  }

  // Initialize any additional schedule events.
  initializeScheduleEvents();

  // *** AJAX Schedule Form Submission ***

  // Use the form ID from your HTML: "scheduleForm"
  const scheduleForm = document.getElementById('scheduleForm');
  console.log('scheduleForm element:', scheduleForm); // Debug log

  if (scheduleForm) {
    // Attach the submit event handler to intercept form submission.
    scheduleForm.addEventListener('submit', function(event) {
      console.log('Submit event triggered.');
      event.preventDefault(); // Prevent full-page submission

      const formData = new FormData(scheduleForm);
      const url = scheduleForm.getAttribute('action');

      fetch(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest', // Mark this as AJAX
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          console.log('Schedule updated successfully via AJAX.', data);
          // Optionally update other parts of the UI (payments table, balance, etc.)

          // Use a slight delay (e.g., 200 milliseconds) before updating the schedule table
          setTimeout(() => {
            // You can either call populateScheduleTable or your global handleScheduleChange.
            // For example, if you expose handleScheduleChange globally:
            window.handleScheduleChange(data.schedule_type);

            // Or if you want to update just the table:
            // populateScheduleTable(data.schedule_type);
          }, 200);

          // Update the payment schedule dropdown if necessary:
          const scheduleDropdown = document.getElementById('payment-schedule');
          if (scheduleDropdown) {
            scheduleDropdown.disabled = false;
            scheduleDropdown.value = data.schedule_type;
            scheduleDropdown.dispatchEvent(new Event('change'));
          }

          // Ensure the "Add or Update Schedule" button is visible.
          const addUpdateBtn = document.querySelector('.payment-schedule-selection button[data-toggle="modal"]');
          if (addUpdateBtn) {
            addUpdateBtn.style.display = 'inline-block';
          }

          // Hide the schedule modal.
          $('#scheduleModal').modal('hide');
        } else {
          console.error('Error updating schedule:', data);
        }
      })

      .catch(error => {
        console.error('AJAX error updating schedule:', error);
      });
    });
  } else {
    console.warn("Schedule form not found.");
  }

  // *** Combined Save Changes Button Handler ***

  // The "Save Changes" button is defined with form="scheduleForm" so it triggers form submission.
  // To be sure, we also intercept its click event.
  const saveChangesBtn = document.getElementById('saveChangesBtn');
  if (saveChangesBtn) {
    saveChangesBtn.addEventListener('click', function(event) {
      event.preventDefault(); // Prevent default button action
      console.log('Save Changes button clicked. Enabling inputs and submitting form via AJAX.');
      // Unlock inputs before submission.
      enablePaymentScheduleInputs();
      // Manually trigger the form's submit event.
      if (scheduleForm) {
        scheduleForm.dispatchEvent(new Event('submit', { cancelable: true }));
      }
    });
  } else {
    console.warn("Save Changes button not found.");
  }

  // *** Receive Payment Modal Initialization ***

  // Initialize receive payment handler.
  initializeReceivePaymentHandler();

  // Note: If your receivePaymentHandler.js previously had its own DOMContentLoaded block,
  // remove it so that initialization is only done here.
});

// Expose it globally.
window.handleScheduleChange = handleScheduleChange;