


// Contract Edit Form Handling
document.addEventListener('DOMContentLoaded', function() {
    // Handling for the contract info edit form
    let contractEditButton = document.getElementById('edit-contract-info-button');
    let contractEditForm = document.getElementById('edit-contract-info-form');
    let contractDisplayDetails = document.getElementById('contract-info');

    if (contractEditButton && contractEditForm && contractDisplayDetails) {
        contractEditButton.addEventListener('click', function() {
            toggleEditForm(true, 'contract');
        });

        contractEditForm.addEventListener('submit', function(event) {
            event.preventDefault();
            submitEditForm('edit-contract-info-form', 'contract_info', updateContractDisplay);
        });
    } else {
        console.error('One or more contract elements not found', {contractEditButton, contractEditForm, contractDisplayDetails});
    }

    // Handling for the client info edit form
    let clientEditForm = document.getElementById('edit-client-form');
    if (clientEditForm) {
        clientEditForm.addEventListener('submit', function(event) {
            event.preventDefault();
            submitEditForm('edit-client-form', 'client_info', updateContractDisplay);
        });
    } else {
        console.error('Client form element not found', {clientEditForm});
    }

    // Handling for the event details edit form
    let eventEditForm = document.getElementById('edit-event-form');
    if (eventEditForm) {
        eventEditForm.addEventListener('submit', function(event) {
            event.preventDefault();
            submitEditForm('edit-event-form', 'event_details', updateContractDisplay);
        });
    } else {
        console.error('Event form element not found', {eventEditForm});
    }

    // Toggle functionality for additional client and event details
    let toggleClientButton = document.getElementById('toggleClientInfo');
    let additionalClientInfo = document.getElementById('additionalClientInfo');
    let toggleEventButton = document.getElementById('toggleEventDetails');
    let additionalEventInfo = document.getElementById('additionalEventDetails');

    if (toggleClientButton && additionalClientInfo) {
        toggleClientButton.addEventListener('click', function() {
            additionalClientInfo.style.display = additionalClientInfo.style.display === 'none' ? 'block' : 'none';
            toggleClientButton.textContent = additionalClientInfo.style.display === 'none' ? 'Show More Client Info' : 'Show Less Client Info';
        });
    } else {
        console.error('Toggle button or additional client info section not found');
    }

    if (toggleEventButton && additionalEventInfo) {
        toggleEventButton.addEventListener('click', function() {
            additionalEventInfo.style.display = additionalEventInfo.style.display === 'none' ? 'block' : 'none';
            toggleEventButton.textContent = additionalEventInfo.style.display === 'none' ? 'Show More Event Details' : 'Show Less Event Details';
        });
    } else {
        console.error('Toggle button or additional event info section not found');
    }
});

function toggleEditForm(editMode) {
    let infoDisplay = document.getElementById('contract-info');
    let editForm = document.getElementById('edit-contract-info');

    if (editMode) {
        infoDisplay.style.display = 'none';
        editForm.style.display = 'block';
    } else {
        infoDisplay.style.display = 'block';
        editForm.style.display = 'none';
    }
}


    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

function submitEditForm(formId, formDataIdentifier, updateDisplayCallback) {
    console.log("Form ID:", formId); // Log the form ID for debugging purposes
    let contractId = document.body.getAttribute('data-contract-id'); // Get the contract ID from the body element
    let form = document.getElementById(formId); // Get the form element by ID
    console.log("Form element:", form); // Log the form element for debugging purposes
    const csrftoken = getCookie('csrftoken'); // Get CSRF token

    if (contractId && form) {
        let formData = new FormData(form); // Create FormData object from the form
        formData.append(formDataIdentifier, 'true'); // Append an identifier to distinguish between different forms

        fetch(`/contracts/${contractId}/edit/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken,
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not OK');
            }
            return response.json(); // Parse the JSON response
        })
        .then(data => {
            if (data.status === 'success') {
                console.log(`${formDataIdentifier} updated successfully.`);
                if (updateDisplayCallback) {
                    updateDisplayCallback(contractId); // Call the callback function to update the UI
                }
                toggleEditForm(false); // Toggle the edit form to hide it
            } else {
                console.error(`Error updating ${formDataIdentifier}:`, data.errors); // Log any errors
                // Display validation errors on the form
            }
        })
        .catch(error => {
            console.error('Error:', error); // Log any network or unexpected errors
            // Handle network or other unexpected errors
        });
    } else {
        console.error(`Failed to submit ${formDataIdentifier} form - missing data`, {contractId, form});
    }

    document.getElementById('edit-contract-info-form').addEventListener('submit', function(event) {
        event.preventDefault();
        submitEditForm('edit-contract-info-form', 'contract_info', updateContractDisplay);
    });

    document.getElementById('edit-client-form').addEventListener('submit', function(event) {
        event.preventDefault();
        submitEditForm('edit-client-form', 'client_info', updateContractDisplay);
    });

    document.getElementById('edit-event-form').addEventListener('submit', function(event) {
        event.preventDefault();
        submitEditForm('edit-event-form', 'event_details', updateContractDisplay);
    });

}

function updateContractDisplay(contractId) {
    fetch(`/contracts/${contractId}/data/`)
    .then(response => response.json())
    .then(data => {
         console.log('Received data:', data); // Log the entire data object

        // Update the main contract info section
        updateField('contract-location', 'Location: ' + data.location);
        updateField('contract-event-date', 'Event Date: ' + data.event_date);
        updateField('contract-status', 'Status: ' + data.status);
        updateField('contract-csr', 'Sales Person: ' + data.csr);
        updateField('contract-lead-source', 'Lead Source: ' + data.lead_source);


        // Check and update client information if available
        if (data.client) {
            updateField('client-primary-contact', 'Primary Contact: ' + data.client.primary_contact);
            updateField('client-primary-email', 'Primary Email: ' + data.client.primary_email);
            updateField('client-primary-phone1', 'Primary Phone 1: ' + data.client.primary_phone1);

            updateField('client-partner-contact', 'Partner Contact: ' + data.client.partner_contact);
            updateField('client-partner-email', 'Partner Email: ' + data.client.partner_email);
            updateField('client-partner-phone1', 'Partner Phone 1: ' + data.client.partner_phone1);

            updateField('client-primary-address1', 'Primary Address 1: ' + data.client.primary_address1);
            updateField('client-primary-address2', 'Primary Address 2: ' + data.client.primary_address2);
            updateField('client-city', 'City: ' + data.client.city);
            updateField('client-state', 'State: ' + data.client.state);
            updateField('client-postal-code', 'Postal Code: ' + data.client.postal_code);

            updateField('client-alt-contact', 'Alternative Contact: ' + data.client.alt_contact);
            updateField('client-alt-email', 'Alternative Email: ' + data.client.alt_email);
            updateField('client-alt-phone', 'Alternative Phone: ' + data.client.alt_phone);

            // Assuming 'data.client' is defined and contains the necessary fields
            if (data.client) {
                updateField('header-primary-contact', 'Primary Contact: ' + data.client.primary_contact);
                updateField('header-primary-email', 'Primary Email: ' + data.client.primary_email);
                updateField('header-primary-phone', 'Primary Phone: ' + data.client.primary_phone1);
                updateField('header-partner-contact', 'Partner Contact: ' + data.client.partner_contact);            }

        }

        // Check and update event details if available
        if (data.event) {
            updateField('event-bridal-party-qty', 'Bridal Party Quantity: ' + data.event.bridal_party_qty);
            updateField('event-ceremony-site', 'Ceremony Site: ' + data.event.ceremony_site);
            updateField('event-ceremony-city', 'Ceremony City: ' + data.event.ceremony_city);
            updateField('event-ceremony-state', 'Ceremony State: ' + data.event.ceremony_state);
            updateField('event-guests-qty', 'Guests Quantity: ' + data.event.guests_qty);
            updateField('event-reception-site', 'Reception Site: ' + data.event.reception_site);
            updateField('event-reception-city', 'Reception City: ' + data.event.reception_city);
            updateField('event-reception-state', 'Reception State: ' + data.event.reception_state);
            updateField('event-ceremony-contact', 'Ceremony Contact: ' + data.event.ceremony_contact);
            updateField('event-ceremony-phone', 'Ceremony Phone: ' + data.event.ceremony_phone);
            updateField('event-ceremony-email', 'Ceremony Email: ' + data.event.ceremony_email);
            updateField('event-reception-contact', 'Reception Contact: ' + data.event.reception_contact);
            updateField('event-reception-phone', 'Reception Phone: ' + data.event.reception_phone);
            updateField('event-reception-email', 'Reception Email: ' + data.event.reception_email);
        }


        // Update the header section
        updateField('header-location', 'Location: ' + data.location);
        updateField('header-lead-source', 'Lead Source: ' + data.lead_source);
        updateField('header-csr', 'Sales Person: ' + data.csr);
        updateField('header-status', 'Status: ' + data.status);



        console.log('Contract display updated for contract ID:', contractId);
    })
    .catch(error => {
        console.error('Error updating contract display:', error);
    });
}

function updateField(elementId, text) {
    const element = document.getElementById(elementId);
    console.log('Updating:', elementId, 'with', text);
    if (element) {
        element.textContent = text;
    } else {
        console.error('Element not found:', elementId);
    }
}


