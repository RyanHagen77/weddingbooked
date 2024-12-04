const eventStaffManagement = {
    updateAssignedFields(contractId, roles) {
        if (!contractId) {
            console.error("Contract ID is missing. Cannot update assigned fields.");
            return;
        }

        roles.forEach(role => {
            fetch(`/bookings/get_current_booking/?contract_id=${contractId}&role=${role}`)
                .then(response => response.json())
                .then(data => {
                    const assignedStaffField = document.getElementById(`assigned-${role.toLowerCase()}`);
                    if (assignedStaffField) {
                        if (data.current_booking && data.current_booking.staff_name) {
                            console.log(`Updating field for role ${role}: ${data.current_booking.staff_name}`);
                            assignedStaffField.textContent = data.current_booking.staff_name;
                        }
                    }
                })
                .catch(error => {
                    console.error(`Error fetching current booking for ${role}:`, error);
                });
        });
    },

    setupEventDateChangeListener() {
        const eventDateInput = document.getElementById('id_event_date');
        if (eventDateInput) {
            eventDateInput.addEventListener('change', () => {
                const eventDate = eventDateInput.value;
                if (eventDate) {
                    console.log(`Event date changed to: ${eventDate}`);
                    this.updateAvailableStaff(eventDate);
                }
            });
        } else {
            console.error("Event date input not found!");
        }
    },

    handleBookingFormSubmission() {
        const bookingForm = document.getElementById('bookingForm');
        const submitButton = document.getElementById('submitBooking');
        const updateButton = document.getElementById('updateBooking');

        const submitHandler = (event) => {
            event.preventDefault();
            const isUpdate = event.target.id === 'updateBooking';

            const eventDateInput = document.getElementById('id_event_date');
            if (eventDateInput) {
                const eventDateField = bookingForm.elements['event_date'];
                if (eventDateField) {
                    eventDateField.value = eventDateInput.value;
                }
            }

            const formData = new FormData(bookingForm);
            if (isUpdate) {
                const bookingId = document.getElementById('id_booking_id').value;
                console.log(`Updating booking ID: ${bookingId}`);
                formData.append('booking_id', bookingId);
            }

            fetch(bookingForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    console.log(`Booking saved successfully: ${data.message}`);
                    const assignedStaffField = document.getElementById(`assigned-${data.role.toLowerCase()}`);
                    if (assignedStaffField) {
                        assignedStaffField.textContent = data.staff_name;
                    }
                    $('#bookingModal').modal('hide');
                    bookingForm.reset();
                    $('body').removeClass('modal-open');
                    $('.modal-backdrop').remove();
                } else {
                    console.error('Error saving booking:', data.errors);
                }
            })
            .catch(error => {
                console.error('Error submitting booking form:', error);
            });
        };

        submitButton.addEventListener('click', submitHandler);
        updateButton.addEventListener('click', submitHandler);
    },

    init() {
        this.setupEventDateChangeListener();
        const contractId = document.getElementById('contractId').value;
        const roles = [
            'PHOTOGRAPHER1',
            'PHOTOGRAPHER2',
            'VIDEOGRAPHER1',
            'VIDEOGRAPHER2',
            'DJ1',
            'DJ2',
            'PHOTOBOOTH_OP1',
            'PHOTOBOOTH_OP2',
            'ENGAGEMENT',
        ];
        this.updateAssignedFields(contractId, roles);
        this.handleBookingFormSubmission();



    }
};
$(document).on('click', '.book-button, .edit-button', function (event) {
    const button = $(this);
    const role = button.data('role'); // e.g., "ENGAGEMENT", "DJ1", "PHOTOGRAPHER1", "PROSPECT1"
    const serviceType = button.data('service-type'); // e.g., "Photography", "DJ"
    const bookingId = button.data('booking-id') || '';

    console.log(`Button clicked. Role: ${role}, Service: ${serviceType}, Booking ID: ${bookingId}`);

    // Skip validation for all PROSPECT roles
    if (role.toLowerCase().includes('prospect')) {
        console.log(`Skipping validation for prospect role: ${role}`);

        // Open the modal directly without validation
        $('#bookingModal').modal('show');

        // Prepopulate fields for the prospect role
        $('#id_role').val(role); // Set the role
        $('#id_booking_id').val(bookingId); // If available, set the booking ID

        const staffSelect = $('#id_staff');
        staffSelect.empty(); // Clear existing options
        staffSelect.append(new Option('Select Staff', '')); // Add default "Select Staff" option

        // Prepopulate staff dropdown with options for this role
        fetch(`/bookings/get_available_staff/?role=${role}`)
            .then(response => response.json())
            .then(data => {
                const staffKey = `${serviceType.toLowerCase()}_staff`;

                if (data[staffKey]) {
                    data[staffKey].forEach(staff => {
                        staffSelect.append(new Option(staff.name, staff.id));
                    });

                    // Select the currently assigned staff, if any
                    if (data.current_staff) {
                        staffSelect.val(data.current_staff.id);
                    }
                }
            })
            .catch(error => console.error('Error fetching available staff:', error));

        return; // Skip further validation and execution
    }

    // Normalize serviceType to match hidden field IDs (capitalize first letter if needed)
    const normalizedServiceType = serviceType.charAt(0).toUpperCase() + serviceType.slice(1).toLowerCase();

    // Determine the field to validate based on the role and service type
    let fieldToCheck;
    if (role === 'ENGAGEMENT') {
        // Special case for engagement
        fieldToCheck = $('#hiddenSavedEngagementSessionId'); // Engagement session field
    } else if (role.includes('1')) {
        // Primary role, check package
        fieldToCheck = $(`#hiddenSaved${normalizedServiceType}PackageId`);
    } else {
        // Secondary role, check additional staff
        fieldToCheck = $(`#hiddenSaved${normalizedServiceType}AdditionalStaffId`);
    }

    const fieldValue = fieldToCheck?.val() || null;

    console.log(`Field to check: ${fieldToCheck?.attr('id') || 'undefined'}, Value: ${fieldValue}`);

    // Block modal if the relevant field is empty
    if (!fieldValue) {
        const message = `No ${serviceType} service assigned for the selected role (${role}). Modal will not open.`;
        console.warn(message);
        alert(message); // Display the warning message as an alert
        event.preventDefault(); // Prevent default behavior
        return; // Explicitly stop function execution
    }

    // Block modal if the edit button is clicked without a booking ID
    if (button.hasClass('edit-button') && !bookingId) {
        const message = `Edit button clicked for ${role}, but no booking exists. Modal will not open.`;
        console.warn(message);
        alert(message); // Display the warning message as an alert
        event.preventDefault(); // Prevent default behavior
        return; // Explicitly stop function execution
    }

    // Open the modal programmatically
    console.log('Validation passed. Opening modal...');
    $('#bookingModal').modal('show');

    // Prepare the modal fields
    console.log(`Preparing modal for role: ${role}, booking ID: ${bookingId}, service type: ${serviceType}`);
    $('#id_role').val(role);
    $('#id_booking_id').val(bookingId);

    const staffSelect = $('#id_staff');
    staffSelect.empty(); // Clear existing options
    staffSelect.append(new Option('Select Staff', '')); // Add default "Select Staff" option

    const contractId = $('#contractId').val();
    const eventDate = $('#id_event_date').val();

    if (!bookingId) {
        console.log('No booking ID provided. Preparing modal for a new booking.');
        $('#id_status').val(role.includes('PROSPECT') ? 'PROSPECT' : 'BOOKED'); // Default to PROSPECT for prospect roles
        $('#id_hours_booked').val('');
        $('#id_confirmed').prop('checked', false);
    } else {
        // Fetch current booking data if editing an existing booking
        fetch(`/bookings/get_current_booking/?contract_id=${contractId}&role=${role}`)
            .then(response => response.json())
            .then(data => {
                if (data.current_booking) {
                    console.log('Populating modal with current booking data:', data.current_booking);

                    // Populate fields based on current booking
                    $('#id_status').val(data.current_booking.status || 'BOOKED');
                    $('#id_hours_booked').val(data.current_booking.hours_booked);
                    $('#id_confirmed').prop('checked', data.current_booking.confirmed);

                    // Add the assigned staff member to the dropdown and select it
                    const currentStaffOption = new Option(
                        data.current_booking.staff_name,
                        data.current_booking.staff_id,
                        true, // Mark as selected
                        true  // Set as default selected
                    );
                    staffSelect.append(currentStaffOption);
                } else {
                    console.log('No current booking found. Preparing modal for a new booking.');
                }
            })
            .catch(error => console.error('Error fetching current booking:', error));
    }

    // Populate available staff for the service type
    fetch(`/bookings/get_available_staff/?event_date=${eventDate}&service_type=${serviceType}`)
        .then(response => response.json())
        .then(data => {
            const staffKey = `${serviceType.toLowerCase()}_staff`;

            if (data[staffKey]) {
                data[staffKey].forEach(staff => {
                    staffSelect.append(new Option(staff.name, staff.id));
                });
            }
        })
        .catch(error => console.error('Error fetching available staff:', error));
});

$('#deleteBooking').on('click', function() {
        const bookingId = $('#id_booking_id').val();
        const contractId = $('#contractId').val();
        const role = $('#id_role').val().toLowerCase();

        console.log('Attempting to delete booking with ID:', bookingId);

        if (!bookingId) {
            console.error("No booking ID found for deletion.");
            alert("No booking ID found for deletion.");
            return;
        }

        if (confirm('Are you sure you want to delete this booking?')) {
            fetch(`/bookings/booking/${bookingId}/clear/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text();
            })
            .then(() => {
                console.log('Booking deleted successfully');
                $('#bookingModal').modal('hide');
                $(`#assigned-${role}`).text("None assigned");
                $('body').removeClass('modal-open');
                $('.modal-backdrop').remove();
            })
            .catch(error => {
                console.error('Error deleting booking:', error);
                alert('Error clearing booking: ' + error.message);
            });
        }
    });


    document.addEventListener("DOMContentLoaded", () => {
        eventStaffManagement.init();
    });

