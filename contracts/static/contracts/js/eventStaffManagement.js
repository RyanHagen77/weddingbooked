const eventStaffManagement = {
    // Function to fetch available staff based on the event date
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

// Function to update dropdowns with available staff
updateDropdowns(fieldNames, data) {
    console.log(`Updating dropdowns: ${fieldNames.join(', ')} with data:`, data);
    fieldNames.forEach(fieldName => {
        const dropdown = document.getElementById(fieldName);
        if (dropdown) {
            dropdown.innerHTML = '';  // Clear existing options

            // Add a placeholder option
            const placeholderOption = document.createElement('option');
            placeholderOption.textContent = "Select Staff";
            placeholderOption.value = "";
            dropdown.appendChild(placeholderOption);

            // Add new options from fetched data
            data.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option.id;
                optionElement.textContent = option.name;
                dropdown.appendChild(optionElement);
            });

            // If there are no other options, make the placeholder option selected
            if (data.length === 0) {
                placeholderOption.selected = true;
            } else {
                // If there are other options, make sure the placeholder is not selected
                placeholderOption.selected = false;
            }
        } else {
            console.error(`Dropdown element with id '${fieldName}' not found.`);
        }
    });
},


    // Function to fetch and update dropdowns with available photographers based on the event date
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

        // Fetch available staff data based on the event date
        fetch(`/contracts/get_available_staff/?event_date=${formattedDate}`)
    },

    // Function to update the staff dropdown in the modal based on the selected event date
    updateEventStaff() {
        const eventDateInput = document.getElementById('id_event_date');
        if (!eventDateInput) {
            console.error("Event date input not found!");
            return;
        }

        const eventDate = eventDateInput.value;

        this.fetchAvailableStaff(eventDate).then(data => {
            // Ensure that data is not undefined before calling updateDropdowns
            if (data) {
                this.updateDropdowns(['id_staff'], data.photographers);  // Assuming 'photographers' is the correct key
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

        submitButton.addEventListener('click', () => {
            // Set the value of the event_date field in the form
            const eventDateInput = document.getElementById('id_event_date');
            if (eventDateInput) {
                const eventDateField = bookingForm.elements['event_date'];
                if (eventDateField) {
                    eventDateField.value = eventDateInput.value;
                }
            }

            fetch(bookingForm.action, {
                method: 'POST',
                body: new FormData(bookingForm),
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
                    // Update the assigned staff field for the corresponding role
                    const assignedStaffField = document.getElementById(`assigned-${data.role.toLowerCase()}`);
                    if (assignedStaffField) {
                        assignedStaffField.textContent = data.staff_name;
                    }
                    // Close the modal and clear the form
                    $('#bookingModal').modal('hide');
                    bookingForm.reset();
                } else {
                    // Handle errors
                    console.error('Error saving booking:', data.errors);
                }
            })
            .catch(error => {
                console.error('Error submitting booking form:', error);
            });
        });
    },


    setupEventDateChangeListener: function() {
        const eventDateInput = document.getElementById('id_event_date');
        if (eventDateInput) {
            eventDateInput.addEventListener('change', () => this.updateAvailablePhotographers(eventDateInput.value));
        }
    },

    // Initialize the module
    init() {
        this.setupEventDateChangeListener();
        this.updateEventStaff();
        this.updateAvailablePhotographers(new Date().toISOString().split('T')[0]);
        this.handleBookingFormSubmission();
        this.setupEventDateChangeListener();


    }
};

document.addEventListener("DOMContentLoaded", () => {
    eventStaffManagement.init();

    // Update assigned staff for all roles on page load
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
    const button = $(event.relatedTarget); // Button that triggered the modal
    const role = button.data('role');
    const serviceType = button.data('serviceType'); // Extract service type from data-* attributes
    const contractId = $('#contractId').val();
    const eventDate = $('#id_event_date').val(); // Get the event date from the input field

    // Pre-populate the role field based on the button clicked
    $('#id_role').val(role);

    // Reset the form fields to their default values
    const staffSelect = document.getElementById('id_staff');
    staffSelect.innerHTML = ''; // Clear existing options

    // Always add a placeholder initially
    const placeholderOption = new Option('Select Staff', '');
    staffSelect.appendChild(placeholderOption);
    staffSelect.value = ''; // Set the placeholder as the default selected option

    // Fetch current booking data
    fetch(`/contracts/get_current_booking/?contract_id=${contractId}&role=${role}`)
        .then(response => response.json())
        .then(data => {
            if (data.current_booking && data.current_booking.staff_id) {
                // Set the booking ID for deletion
                $('#id_booking_id').val(data.current_booking.id);
                // Create and append the option for the current staff
                const option = new Option(data.current_booking.staff_name, data.current_booking.staff_id, true, true);
                staffSelect.appendChild(option);
                staffSelect.value = data.current_booking.staff_id; // Set this staff as the selected option

                // Set status and confirmation
                $('#id_status').val('APPROVED');
                $('#id_confirmed').prop('checked', true);
                $('#assignedStaffName').text(data.current_booking.staff_name);

                // Remove the placeholder if a staff is assigned
                staffSelect.removeChild(placeholderOption);
            } else {
                $('#id_booking_id').val('');
                $('#assignedStaffName').text('No staff assigned');
            }
        })
        .catch(error => console.error('Error fetching current booking:', error));

    // Fetch available staff data based on the event date and service type
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
                // Only show the placeholder if no staff are found and there's no current booking
                staffSelect.value = '';
            }
        })
        .catch(error => console.error('Error fetching available staff:', error));
});


    document.getElementById('deleteBooking').addEventListener('click', function() {
        const bookingId = $('#id_booking_id').val(); // Fetch the booking ID
        const contractId = $('#contractId').val(); // Fetch the contract ID from a hidden input or relevant element in your page
        const role = $('#id_role').val().toLowerCase(); // Get the role from the modal, assuming it's stored in an input

        console.log('Attempting to delete booking with ID:', bookingId); // Log the fetched booking ID

        if (!bookingId) {
            console.error("No booking ID found for deletion.");
            alert("No booking ID found for deletion.");
            return;
        }

        if (confirm('Are you sure you want to delete this booking?')) {
            fetch(`/contracts/booking/${bookingId}/clear/`, {
                method: 'POST', // Make sure your server is set to accept POST for this operation
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text();  // We don't expect a JSON response
            })
            .then(() => {
                console.log('Booking deleted successfully');
                $('#bookingModal').modal('hide'); // Hide the modal
                $(`#assigned-${role}`).text("None assigned"); // Update the page to remove the staff name from the assigned area
                // Optionally, you can trigger an event to refresh other parts of the page if necessary
            })
            .catch(error => {
                console.error('Error deleting booking:', error);
                alert('Error clearing booking: ' + error.message);
            });
        }
    });
});
