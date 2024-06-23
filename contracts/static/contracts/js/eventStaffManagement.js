const eventStaffManagement = {
    fetchAvailableStaff(date) {
        console.log(`Fetching available staff for date: ${date}`);
        return fetch(`/contracts/get_available_staff/?event_date=${date}`)
            .then(response => response.json())
            .then(data => {
                console.log('Available staff data:', data);
                return data;
            })
            .catch(error => console.error("Error fetching available staff:", error));
    },

    updateDropdowns(fieldNames, data) {
        console.log(`Updating dropdowns: ${fieldNames.join(', ')} with data:`, data);
        fieldNames.forEach(fieldName => {
            const dropdown = document.getElementById(fieldName);
            if (dropdown) {
                dropdown.innerHTML = '';  // Clear existing options

                const placeholderOption = document.createElement('option');
                placeholderOption.textContent = "Select Staff";
                placeholderOption.value = "";
                dropdown.appendChild(placeholderOption);

                data.forEach(option => {
                    const optionElement = document.createElement('option');
                    optionElement.value = option.id;
                    optionElement.textContent = option.name;
                    dropdown.appendChild(optionElement);
                });

                if (data.length === 0) {
                    placeholderOption.selected = true;
                } else {
                    placeholderOption.selected = false;
                }
            } else {
                console.error(`Dropdown element with id '${fieldName}' not found.`);
            }
        });
    },

    updateAvailablePhotographers(eventDate) {
        const contractIdElement = document.getElementById('contractId');
        const contractId = contractIdElement ? contractIdElement.value : null;

        if (!contractId) {
            console.error("Contract ID is undefined or not available.");
            return;
        }

        const eventDateInput = document.getElementById('id_event_date');
        if (!eventDateInput) {
            console.error("Event date input not found!");
            return;
        }

        const rawEventDate = eventDateInput.value;
        const parsedDate = new Date(rawEventDate);
        if (isNaN(parsedDate.getTime())) {
            console.error("Invalid date format:", rawEventDate);
            return;
        }

        const formattedDate = parsedDate.toISOString().split('T')[0];

        this.fetchAvailableStaff(formattedDate).then(data => {
            if (data) {
                this.updateDropdowns(['id_staff'], data.photographers);
            }
        }).catch(error => console.error("Error updating available photographers:", error));
    },

    updateEventStaff() {
        const eventDateInput = document.getElementById('id_event_date');
        if (!eventDateInput) {
            console.error("Event date input not found!");
            return;
        }

        const eventDate = eventDateInput.value;

        this.fetchAvailableStaff(eventDate).then(data => {
            if (data) {
                this.updateDropdowns(['id_staff'], data.photographers);
            } else {
                console.error('Error updating event staff: data is undefined');
            }
        }).catch(error => {
            console.error("Error updating event staff:", error);
        });
    },

    handleBookingFormSubmission: function() {
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
                formData.append('booking_id', document.getElementById('id_booking_id').value);
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
                    console.log(data.message);
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

    setupEventDateChangeListener: function() {
        const eventDateInput = document.getElementById('id_event_date');
        if (eventDateInput) {
            eventDateInput.addEventListener('change', () => this.updateAvailablePhotographers(eventDateInput.value));
        }
    },

    init() {
        this.setupEventDateChangeListener();
        this.updateEventStaff();
        this.updateAvailablePhotographers(new Date().toISOString().split('T')[0]);
        this.handleBookingFormSubmission();
    }
};

document.addEventListener("DOMContentLoaded", () => {
    eventStaffManagement.init();

    const contractId = $('#contractId').val();
    const roles = ['PHOTOGRAPHER1', 'PHOTOGRAPHER2', 'VIDEOGRAPHER1', 'VIDEOGRAPHER2', 'DJ1', 'DJ2', 'PHOTOBOOTH1',
        'PHOTOBOOTH2', 'PROSPECT1', 'PROSPECT2', 'PROSPECT3'];
    roles.forEach(role => {
        fetch(`/contracts/get_current_booking/?contract_id=${contractId}&role=${role}`)
            .then(response => response.json())
            .then(data => {
                const assignedStaffField = document.getElementById(`assigned-${role.toLowerCase()}`);
                if (assignedStaffField) {
                    if (data.current_booking) {
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

    $('#bookingModal').on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        const role = button.data('role');
        const serviceType = button.data('serviceType');
        const bookingId = button.data('booking-id');
        const contractId = $('#contractId').val();
        const eventDate = $('#id_event_date').val();

        $('#id_role').val(role);
        $('#id_booking_id').val(bookingId);

        const staffSelect = document.getElementById('id_staff');
        staffSelect.innerHTML = '';

        const placeholderOption = new Option('Select Staff', '');
        staffSelect.appendChild(placeholderOption);
        staffSelect.value = '';

        fetch(`/contracts/get_current_booking/?contract_id=${contractId}&role=${role}`)
            .then(response => response.json())
            .then(data => {
                if (data.current_booking && data.current_booking.staff_id) {
                    $('#id_booking_id').val(data.current_booking.id);
                    const option = new Option(data.current_booking.staff_name, data.current_booking.staff_id, true, true);
                    staffSelect.appendChild(option);
                    staffSelect.value = data.current_booking.staff_id;

                    $('#id_status').val(data.current_booking.status);
                    $('#id_confirmed').prop('checked', data.current_booking.confirmed);
                    $('#id_hours_booked').val(data.current_booking.hours_booked);
                    $('#assignedStaffName').text(data.current_booking.staff_name);

                    staffSelect.removeChild(placeholderOption);
                } else {
                    $('#assignedStaffName').text('No staff assigned');
                    if (role === 'PROSPECT1' || role === 'PROSPECT2' || role === 'PROSPECT3') {
                        $('#id_status').val('PROSPECT');
                    } else {
                        $('#id_status').val('APPROVED');
                    }
                }
            })
            .catch(error => console.error('Error fetching current booking:', error));

        fetch(`/contracts/get_available_staff/?event_date=${eventDate}&service_type=${serviceType}`)
            .then(response => response.json())
            .then(data => {
                const staffKey = `${serviceType.toLowerCase()}_staff`;
                let foundStaff = false;

                if (data[staffKey]) {
                    data[staffKey].forEach(staff => {
                        if (!staffSelect.options[0] || staffSelect.options[0].value !== staff.id.toString()) {
                            const option = new Option(staff.name.trim(), staff.id);
                            staffSelect.appendChild(option);
                            foundStaff = true;
                        }
                    });
                }

                if (!foundStaff && !data.current_booking) {
                    staffSelect.value = '';
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
            fetch(`/contracts/booking/${bookingId}/clear/`, {
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

    $('#bookingModal').on('hidden.bs.modal', function () {
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();
    });
});
