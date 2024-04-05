console.log("JS file loaded and executed!");

    let availableEventStaff = {};
    console.log("Value of availableEventStaff at script start:", availableEventStaff);

    function fetchBookedAndAvailableStaff(date) {
        // Fetch available staff based on event date
        return fetch(`/contracts/get_available_staff/?event_date=${date}`)
            .then(response => response.json())
            .then(availableStaff => {
                // Extract currently booked staff from the form fields
                const bookedStaff = {
                    photographers: [
                        { id: document.getElementById("id_photographer1").value, name: document.getElementById("id_photographer1").selectedOptions[0]?.textContent },
                        { id: document.getElementById("id_photographer2").value, name: document.getElementById("id_photographer2").selectedOptions[0]?.textContent },
                    ],
                    videographers: [
                        { id: document.getElementById("id_videographer1").value, name: document.getElementById("id_videographer1").selectedOptions[0]?.textContent },
                        { id: document.getElementById("id_videographer2").value, name: document.getElementById("id_videographer2").selectedOptions[0]?.textContent },
                    ],
                     djs: [
                        { id: document.getElementById("id_dj").value, name: document.getElementById("id_dj").selectedOptions[0]?.textContent },
                    ],
                     photobooth_operators: [
                        { id: document.getElementById("id_photobooth_op").value, name: document.getElementById("id_photobooth_op").selectedOptions[0]?.textContent },
                     ],
                };

                // Log the available and booked staff here
                console.log("Available Staff:", availableStaff);
                console.log("Booked Photographers:", bookedStaff.photographers);
                console.log("Booked Videographers:", bookedStaff.videographers);
                console.log("Booked DJs:", bookedStaff.djs);
                console.log("Booked Photobooth Operators:", bookedStaff.photobooth_operators);

                // Merge booked and available staff lists and remove duplicates
                const mergeAndDedupe = (booked, available) => {
                    const combined = booked.concat(available);
                    return combined.filter((item, index, self) =>
                        index === self.findIndex(t => t.id === item.id)
                    );
                };

                return {
                    photographers: mergeAndDedupe(bookedStaff.photographers, availableStaff.photographers),
                    videographers: mergeAndDedupe(bookedStaff.videographers, availableStaff.videographers),
                    djs: mergeAndDedupe(bookedStaff.djs, availableStaff.djs),
                    photobooth_operators: mergeAndDedupe(bookedStaff.photobooth_operators, availableStaff.photobooth_operators),
                };
            })
            .catch(error => {
                console.error("Error fetching staff:", error);
                return {};
            });

    }

    // Utility function to update a dropdown with new values.
function updateDropdown(fieldName, data) {
    const dropdown = document.getElementById(`id_${fieldName}`);

    if (!dropdown) {
        console.error(`Dropdown for ${fieldName} not found!`);
        return;
    }

    // Store the current selection before updating the dropdown
    const previousSelection = dropdown.value;

    dropdown.innerHTML = "";  // clear current options
    const defaultOption = document.createElement('option');
    defaultOption.value = "";
    defaultOption.textContent = "---------";
    dropdown.appendChild(defaultOption);

    data.forEach(staff => {
        const option = document.createElement('option');
        option.value = staff.id;
        option.textContent = staff.name;
        dropdown.appendChild(option);
    });

    // Re-apply the previous selection after updating the options
    dropdown.value = previousSelection;
}

    // Update all the staff dropdowns based on fetched data.
    function updateEventStaff() {
        const eventDate = document.getElementById('id_event_date').value;

        fetchBookedAndAvailableStaff(eventDate).then(data => {
                availableEventStaff = data;
                console.log("Fetched Data:", availableEventStaff);

                updateDropdown('photographer1', data.photographers);
                updateDropdown('photographer2', data.photographers);
                updateDropdown('videographer1', data.videographers);
                updateDropdown('videographer2', data.videographers);
                updateDropdown('dj1', data.djs);
                updateDropdown('dj2', data.djs)
                updateDropdown('photobooth_op', data.photobooth_operators);

            }).catch(error => {
                console.error("Error updating event staff:", error);
            });
        }

    $(document).ready(function() {
    console.log("Document ready function triggered!");

    let eventDateInput = document.getElementById('event_date');
    if (!eventDateInput) {
        console.error("Event date input not found!");
        return;
    }

    // This uses jQuery to attach the event.
    // It's equivalent to the vanilla JS method but you're already using jQuery, so it's fine.
    $("#event_date").change(function() {
        console.log("Event date input changed using jQuery!");
        updateEventStaff();
    });
});





