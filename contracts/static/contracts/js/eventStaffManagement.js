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




    // Function to update prospect photographer dropdowns
    updateProspectDropdowns(savedData) {
        const prospectFields = ['prospect_photographer1', 'prospect_photographer2', 'prospect_photographer3'];
        prospectFields.forEach(field => {
            const dropdown = document.getElementById(`id_${field}`);
            if (dropdown && savedData[field]) {
                dropdown.innerHTML = '';  // Clear existing options

                // Add the saved prospect as the first option
                const savedOption = document.createElement('option');
                savedOption.value = savedData[field].id;
                savedOption.textContent = savedData[field].name;
                dropdown.appendChild(savedOption);

                // Set the selected index to the saved option
                dropdown.selectedIndex = 0;
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
            .then(response => response.json())
            .then(data => {
                const photographers = data.photographers; // Assuming the backend returns a list of photographers
                this.updateDropdowns(['id_prospect_photographer1', 'id_prospect_photographer2', 'id_prospect_photographer3'], photographers);

                // Fetch and populate saved prospect photographers
                return fetch(`/contracts/get_prospect_photographers/?contract_id=${contractId}`);
            })
            .then(response => response.json())
            .then(data => {
                this.updateProspectDropdowns(data);
            })
            .catch(error => {
                console.error('Error updating prospect photographers:', error);
            });
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
    const roles = ['PHOTOGRAPHER1', 'PHOTOGRAPHER2', 'VIDEOGRAPHER1', 'VIDEOGRAPHER2'];
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

    // Event listener for the delete button
    document.getElementById('deleteBooking').addEventListener('click', function() {
        const bookingId = $('#id_booking_id').val();
        const role = $('#id_role').val(); // Get the role from the form
        if (bookingId && role) {
            fetch(`/contracts/booking/${bookingId}/clear/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        console.log(data.message);
                        // Close the modal
                        $('#bookingModal').modal('hide');
                        // Clear the assigned staff name for the corresponding role
                        const assignedStaffField = document.getElementById(`assigned-${role.toLowerCase()}`);
                        if (assignedStaffField) {
                            assignedStaffField.textContent = "None assigned";
                        }
                    } else {
                        throw new Error(data.message || 'Failed to delete booking');
                    }
                })
                .catch(error => {
                    console.error('Error deleting booking:', error);
                });
        }
    });

    $('#bookingModal').on('show.bs.modal', function (event) {
        // Reset the form fields to their default values
        const staffSelect = document.getElementById('id_staff');
        staffSelect.innerHTML = ''; // Clear existing options

        // Retrieve the button that triggered the modal
        const button = $(event.relatedTarget); // Button that triggered the modal
        const role = button.data('role'); // Extract role from data-* attributes
        const serviceType = button.data('serviceType'); // Extract service type from data-* attributes
        const contractId = $('#contractId').val();
        const eventDate = $('#id_event_date').val(); // Get the event date from the input field

        // Pre-populate the role field based on the button clicked
        $('#id_role').val(role);

        // Variable to track if a current booking exists
        let currentBookingExists = false;

        // Fetch current booking data
        fetch(`/contracts/get_current_booking/?contract_id=${contractId}&role=${role}`)
            .then(response => response.json())
            .then(data => {
                if (data.current_booking && data.current_booking.staff_id) {
                    currentBookingExists = true;

                    // Add the currently booked staff member as an option
                    const staffOption = new Option(data.current_booking.staff_name, data.current_booking.staff_id, true, true);
                    staffSelect.appendChild(staffOption);

                    // Populate other form fields...
                    $('#id_booking_id').val(data.current_booking.id);
                    $('#id_status').val(data.current_booking.status);
                    $('#id_hours_booked').val(data.current_booking.hours_booked);
                    $('#id_confirmed').prop('checked', data.current_booking.confirmed);

                    // Update the assigned staff name in the modal
                    $('#assignedStaffName').text(data.current_booking.staff_name);

                }
            });

        // Fetch available staff data
        fetch(`/contracts/get_available_staff/?event_date=${$('#id_event_date').val()}&service_type=${serviceType}`)
            .then(response => response.json())
            .then(data => {
                const staffKey = `${serviceType.toLowerCase()}_staff`;

                if (data[staffKey] && data[staffKey].length > 0) {
                    data[staffKey].forEach(staff => {
                        if (staff.name.trim()) {
                            const option = new Option(staff.name.trim(), staff.id);
                            staffSelect.appendChild(option);
                        }
                    });
                }

                // Add a "Select Staff" placeholder option only if there is no saved booking and no available staff
                if (!currentBookingExists && staffSelect.options.length === 0) {
                    const placeholderOption = new Option('Select Staff', '');
                    staffSelect.appendChild(placeholderOption);
                    staffSelect.value = '';
                }
            });
    });
});






