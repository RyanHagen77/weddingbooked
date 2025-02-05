// paymentScheduleEvents.js
import { populateScheduleTable } from './paymentScheduleManager.js';

export function initializeScheduleEvents() {
    const scheduleDropdown = document.getElementById('payment-schedule');
    if (!scheduleDropdown) return;

    // Set initial schedule table
    const initialScheduleType = scheduleDropdown.value;
    populateScheduleTable(initialScheduleType);

    scheduleDropdown.addEventListener('change', function() {
        const selectedValue = this.value;
        const scheduleModalButton = document.querySelector('[data-target="#scheduleModal"]');

        // Show modal button for custom schedule only
        if (selectedValue === 'custom') {
            scheduleModalButton.style.display = 'inline-block';
        } else {
            scheduleModalButton.style.display = 'none';
        }
        populateScheduleTable(selectedValue);
    });

    // When the schedule modal is shown, disable all inputs in the payment schedule entries
    $('#scheduleModal').on('show.bs.modal', function () {
        // Disable all inputs, selects, and textareas within .form-fields in #paymentScheduleEntries
        const inputs = document.querySelectorAll(
            '#paymentScheduleEntries .form-fields input, ' +
            '#paymentScheduleEntries .form-fields select, ' +
            '#paymentScheduleEntries .form-fields textarea'
        );
        inputs.forEach(function(input) {
            input.disabled = true;
        });

        // Uncheck all the "Enable Editing" checkboxes
        const checkboxes = document.querySelectorAll('#paymentScheduleEntries .edit-toggle');
        checkboxes.forEach(function(cb) {
            cb.checked = false;
        });
    });
}
