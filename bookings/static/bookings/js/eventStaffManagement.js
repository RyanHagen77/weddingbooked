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
    const role = button.data('role'); // Role (e.g., "PHOTOGRAPHER1", "PROSPECT1")
    const serviceType = button.data('service-type'); // Service type (e.g., "Photography")
    const bookingId = button.data('booking-id') || '';
    const eventDate = $('#id_event_date').val(); // Event date from input field

    console.log(`Button clicked. Role: ${role}, Service: ${serviceType}, Booking ID: ${bookingId}, Event Date: ${eventDate}`);

    if (!eventDate) {
        alert('Event date is required to fetch available staff.');
        console.error('Event date is missing.');
        return;
    }

    // Open the modal
    console.log('Opening modal...');
    $('#bookingModal').modal('show');

    // Prepopulate fields in the modal
    $('#id_role').val(role);
    $('#id_booking_id').val(bookingId);

    const staffSelect = $('#id_staff');
    staffSelect.empty(); // Clear existing options
    staffSelect.append(new Option('Select Staff', '')); // Add a default "Select Staff" option

    // Fetch current booking data if editing an existing booking
    if (bookingId) {
        console.log('Fetching current booking data...');
        fetch(`/bookings/get_current_booking/?contract_id=${$('#contractId').val()}&role=${role}`)
            .then(response => response.json())
            .then(data => {
                if (data.current_booking) {
                    console.log('Populating modal with current booking data:', data.current_booking);

                    // Populate fields based on current booking
                    $('#id_status').val(data.current_booking.status || 'BOOKED');
                    $('#id_hours_booked').val(data.current_booking.hours_booked);
                    $('#id_confirmed').prop('checked', data.current_booking.confirmed);

                    // Add the assigned staff member to the dropdown and select it
                    staffSelect.append(
                        new Option(data.current_booking.staff_name, data.current_booking.staff_id, true, true)
                    );
                } else {
                    console.log('No current booking found. Preparing for new booking.');
                }
            })
            .catch(error => console.error('Error fetching current booking:', error));
    } else {
        console.log('Preparing modal for a new booking.');
        $('#id_status').val(role.includes('PROSPECT') ? 'PROSPECT' : 'BOOKED');
        $('#id_hours_booked').val('');
        $('#id_confirmed').prop('checked', false);
    }

    // Fetch available staff for the selected role and event date
    console.log('Fetching available staff...');
    fetch(`/bookings/get_available_staff/?role=${role}&event_date=${eventDate}&service_type=${serviceType}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error fetching available staff: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Available staff:', data);

            // Populate staff dropdown without IDs
            const staffKey = `${serviceType.toLowerCase()}_staff`;
            if (data[staffKey]) {
                data[staffKey].forEach(staff => {
                    staffSelect.append(new Option(staff.name, staff.id)); // Only display name
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

