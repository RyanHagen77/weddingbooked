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
                        } else {
                            assignedStaffField.textContent = "None assigned";
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

        if (!submitButton) {
            console.error("Submit button not found. Aborting form submission setup.");
            return;
        }

        submitButton.addEventListener('click', (event) => {
            event.preventDefault();

            const bookingId = document.getElementById('id_booking_id').value;
            const isEdit = !!bookingId; // Determine if this is an update

            const formData = new FormData(bookingForm);
            if (isEdit) {
                console.log(`Updating booking ID: ${bookingId}`);
                formData.append('booking_id', bookingId);
            } else {
                console.log('Creating a new booking.');
            }

            fetch(bookingForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
                .then(response => response.ok ? response.json() : Promise.reject('Failed to save booking.'))
                .then(data => {
                    if (data.success) {
                        console.log(`Booking ${isEdit ? "updated" : "created"} successfully.`);
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
                .catch(error => console.error('Error submitting booking form:', error));
        });
    },

    init() {
        this.setupEventDateChangeListener();

        const contractId = document.getElementById('contractId').value;
        if (!contractId) {
            console.error("Contract ID is missing. Initialization aborted.");
            return;
        }

        const roles = [
            'PHOTOGRAPHER1', 'PHOTOGRAPHER2',
            'VIDEOGRAPHER1', 'VIDEOGRAPHER2',
            'DJ1', 'DJ2',
            'PHOTOBOOTH_OP1', 'PHOTOBOOTH_OP2',
            'ENGAGEMENT',
        ];

        this.updateAssignedFields(contractId, roles);
        this.handleBookingFormSubmission();
    },
};


$(document).on('click', '.book-button', function (event) {
    const button = $(this);
    const role = button.data('role'); // e.g., "DJ1", "PHOTOBOOTH_OP1"
    let serviceType = button.data('service-type'); // e.g., "DJ", "Photobooth"
    const contractId = $('#contractId').val();
    const eventDate = $('#id_event_date').val();

    console.log(`Button clicked. Role: ${role}, Service: ${serviceType}, Event Date: ${eventDate}`);

    // Normalize serviceType to capitalize only the first letter
    serviceType = serviceType.charAt(0).toUpperCase() + serviceType.slice(1).toLowerCase();
    console.log(`Normalized service type: ${serviceType}`);

    // Validate event date
    if (!eventDate) {
        alert('Event date is required to proceed.');
        return;
    }

    // Determine the specific row's hidden field for validation
    let fieldToCheck, hasService;
    if (role === 'ENGAGEMENT') {
        fieldToCheck = $('#hiddenSavedEngagementSessionId');
        hasService = fieldToCheck.val() !== '';
    } else if (role.includes('1')) {
        fieldToCheck = $(`#hiddenSaved${serviceType}PackageId`);
        hasService = fieldToCheck.val() !== '';
    } else if (role.includes('2')) {
        fieldToCheck = $(`#hiddenSaved${serviceType}AdditionalStaffId`);
        hasService = fieldToCheck.val() !== '';
    } else {
        fieldToCheck = null;
        hasService = false;
    }

    console.log(`Field to check: ${fieldToCheck?.attr('id') || 'undefined'}, Value: ${fieldToCheck?.val() || 'undefined'}`);

    // Block modal if no service is assigned for this row
    if (!hasService) {
        const message = `No ${serviceType} service assigned for the selected role (${role}). Modal will not open.`;
        console.warn(message);
        alert(message);
        return;
    }

    // Clear modal fields
    $('#id_role').val(role);
    $('#id_booking_id').val('');
    $('#id_status').val('');
    $('#id_hours_booked').val('');
    $('#id_confirmed').prop('checked', false);
    $('#id_staff').empty().append(new Option('Select Staff', ''));

    // Set modal title
    $('#bookingModalLabel').text('Assign or Edit Staff');

    // Fetch available staff for the role and service type
    const staffKey = role === 'ENGAGEMENT' ? 'photographers' : `${serviceType.toLowerCase()}_staff`;

    fetch(`/bookings/get_available_staff/?event_date=${eventDate}&service_type=${serviceType}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch available staff.');
            }
            return response.json();
        })
        .then(data => {
            console.log('Available staff data received:', data);
            console.log('Staff key:', staffKey);

            const staffSelect = $('#id_staff');

            if (data[staffKey] && data[staffKey].length > 0) {
                data[staffKey].forEach(staff => {
                    staffSelect.append(new Option(staff.name, staff.id));
                });
                console.log('Available staff added to dropdown.');
            } else {
                console.warn(`No staff available for the selected service type: ${serviceType}`);
                staffSelect.append(new Option('No staff available', ''));
            }
        })
        .catch(error => {
            console.error('Error fetching available staff:', error);
            alert('Could not fetch available staff. Please try again later.');
        });

    // Fetch existing booking data
    fetch(`/bookings/get_current_booking/?contract_id=${contractId}&role=${role}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch booking data.');
            }
            return response.json();
        })
        .then(data => {
            if (data.current_booking && Object.keys(data.current_booking).length > 0) {
                console.log('Populating modal with existing booking data:', data.current_booking);

                // Populate modal fields with existing booking data
                $('#id_booking_id').val(data.current_booking.id);
                $('#id_status').val(data.current_booking.status || 'BOOKED');
                $('#id_hours_booked').val(data.current_booking.hours_booked || '');
                $('#id_confirmed').prop('checked', data.current_booking.confirmed);

                // Add the assigned staff member to the dropdown and select it
                const currentStaffOption = new Option(
                    data.current_booking.staff_name,
                    data.current_booking.staff_id,
                    true,
                    true
                );
                $('#id_staff').append(currentStaffOption);
            } else {
                console.log('No existing booking found. Preparing modal for a new booking.');
                $('#id_status').val(role.includes('PROSPECT') ? 'PROSPECT' : 'BOOKED'); // Default status
            }
        })
        .catch(error => {
            console.error('Error fetching booking data:', error);
            alert('Could not fetch booking data. Please try again later.');
        });

    // Show the modal
    $('#bookingModal').modal('show');
});


$(document).on('click', '#deleteBooking', function (event) {
    console.log('Delete button clicked'); // Debug log
    const bookingId = $('#id_booking_id').val(); // Get the booking ID from the modal field
    const contractId = $('#contractId').val(); // Get the contract ID for additional context

    if (!bookingId) {
        alert('No booking ID provided. Cannot delete.');
        return;
    }

    if (confirm('Are you sure you want to delete this booking?')) {
        fetch(`/bookings/booking/${bookingId}/clear/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Failed to delete booking. HTTP Status: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                console.log('Server response:', data); // Debug log
                if (data.success) {
                    alert(data.message);

                    // Clear assigned staff field in the UI
                    const assignedField = document.getElementById(`assigned-${data.role.toLowerCase()}`);
                    if (assignedField) {
                        assignedField.textContent = 'None assigned';
                    }

                    // Close the modal and reset the form
                    $('#bookingModal').modal('hide');
                    $('body').removeClass('modal-open');
                    $('.modal-backdrop').remove();
                    $('#bookingForm').trigger('reset'); // Reset the modal form
                } else {
                    alert('Error deleting booking: ' + (data.message || 'Unknown error.'));
                }
            })
            .catch((error) => {
                console.error('Error during booking deletion:', error);
                alert('Error deleting booking. Please try again later.');
            });
    }
});


    document.addEventListener("DOMContentLoaded", () => {
        eventStaffManagement.init();
    });

