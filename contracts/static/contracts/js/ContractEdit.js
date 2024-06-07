document.addEventListener('DOMContentLoaded', function() {
    // Initialize buttons and forms
    const contractEditButton = document.getElementById('edit-contract-info-button');
    const contractEditForm = document.getElementById('edit-contract-info-form');
    const clientEditForm = document.getElementById('edit-client-form');
    const eventEditForm = document.getElementById('edit-event-form');
    const saveCustomTextButton = document.getElementById('saveCustomText');
    const modalCustomText = document.getElementById('modalCustomText');


    // Event listener for contract info edit button
    if (contractEditButton && contractEditForm) {
        contractEditButton.addEventListener('click', function() {
            toggleEditForm(true);
        });
    }

    // Event listeners for form submissions
    if (contractEditForm) {
        contractEditForm.addEventListener('submit', function(event) {
            event.preventDefault();
            submitEditForm('edit-contract-info-form', 'contract_info', updateContractDisplay);
        });
    }

    if (clientEditForm) {
        clientEditForm.addEventListener('submit', function(event) {
            event.preventDefault();
            submitEditForm('edit-client-form', 'client_info', updateContractDisplay);
        });
    }

    if (eventEditForm) {
        eventEditForm.addEventListener('submit', function(event) {
            event.preventDefault();
            submitEditForm('edit-event-form', 'event_details', updateContractDisplay);
        });
    }

    // Event listener for the custom text modal
    $('#customTextModal').on('show.bs.modal', function () {
        const contractId = document.body.getAttribute('data-contract-id');
        fetch(`/contracts/${contractId}/data/`)
            .then(response => response.json())
            .then(data => {
                modalCustomText.value = data.custom_text || '';
            })
            .catch(error => {
                console.error('Error fetching custom text:', error);
            });
    });

    if (saveCustomTextButton) {
        saveCustomTextButton.addEventListener('click', function() {
            const customText = modalCustomText.value;
            const customTextField = document.querySelector('[name="contract_info-custom_text"]');
            if (customTextField) {
                customTextField.value = customText;
                $('#customTextModal').modal('hide');
                document.getElementById('edit-contract-info-form').submit();
            } else {
                console.error('Custom text field not found');
            }
        });
    }

    // Toggle client and event info sections
    const toggleClientButton = document.getElementById('toggleClientInfo');
    const additionalClientInfo = document.getElementById('additionalClientInfo');
    const toggleEventButton = document.getElementById('toggleEventDetails');
    const additionalEventInfo = document.getElementById('additionalEventDetails');

    if (toggleClientButton && additionalClientInfo) {
        toggleClientButton.addEventListener('click', function() {
            const isHidden = additionalClientInfo.style.display === 'none';
            additionalClientInfo.style.display = isHidden ? 'block' : 'none';
            toggleClientButton.textContent = isHidden ? 'Show Less Client Info' : 'Show More Client Info';
        });
    }

    if (toggleEventButton && additionalEventInfo) {
        toggleEventButton.addEventListener('click', function() {
            const isHidden = additionalEventInfo.style.display === 'none';
            additionalEventInfo.style.display = isHidden ? 'block' : 'none';
            toggleEventButton.textContent = isHidden ? 'Show Less Event Details' : 'Show More Event Details';
        });
    }
});

function toggleEditForm(editMode) {
    const infoDisplay = document.getElementById('contract-info');
    const editForm = document.getElementById('edit-contract-info');

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
    const contractId = document.body.getAttribute('data-contract-id');
    const form = document.getElementById(formId);
    const csrftoken = getCookie('csrftoken');

    console.log("Submitting form", formId, "with contract ID", contractId);

    if (contractId && form) {
        const formData = new FormData(form);
        formData.append(formDataIdentifier, 'true');

        fetch(`/contracts/${contractId}/edit/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken,
            },
            body: formData
        })
        .then(response => {
            console.log("Response status:", response.status);
            if (!response.ok) {
                throw new Error('Network response was not OK');
            }
            return response.json();
        })
        .then(data => {
            console.log("Response data:", data);
            if (data.status === 'success') {
                console.log(`${formDataIdentifier} updated successfully.`);
                if (updateDisplayCallback) {
                    updateDisplayCallback(contractId);
                }
                toggleEditForm(false);
            } else if (data.status === 'unauthorized') {
                showUnauthorizedModal(data.message);
            } else {
                console.error(`Error updating ${formDataIdentifier}:`, data.message);
                displayFormErrors(formId, data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else {
        console.error(`Failed to submit ${formDataIdentifier} form - missing data`, {contractId, form});
    }
}

function showUnauthorizedModal(message) {
    const modal = document.getElementById('unauthorizedModal');
    const modalMessage = document.getElementById('unauthorizedMessage');

    // Debugging logs
    console.log("modal:", modal);
    console.log("modalMessage:", modalMessage);

    if (modal && modalMessage) {
        modalMessage.textContent = message;
        modal.style.display = 'block';
    } else {
        console.error('Modal or modal message element not found');
    }
}

function displayFormErrors(formId, errors) {
    const form = document.getElementById(formId);
    if (form) {
        for (const [field, messages] of Object.entries(errors)) {
            const fieldElement = form.querySelector(`[name="${field}"]`);
            if (fieldElement) {
                const errorContainer = document.createElement('div');
                errorContainer.className = 'error-messages';
                messages.forEach(message => {
                    const errorMessage = document.createElement('p');
                    errorMessage.textContent = message;
                    errorContainer.appendChild(errorMessage);
                });
                fieldElement.parentElement.appendChild(errorContainer);
            }
        }
    }
}

function updateContractDisplay(contractId) {
    fetch(`/contracts/${contractId}/data/`)
    .then(response => response.json())
    .then(data => {
        updateField('contract-location', 'Location: ' + data.location);
        updateField('contract-coordinator', 'Coordinator: ' + data.coordinator);
        updateField('contract-event-date', 'Event Date: ' + data.event_date);
        updateField('contract-status', 'Status: ' + data.status);
        updateField('contract-csr', 'Sales Person: ' + data.csr);
        updateField('contract-lead-source', 'Lead Source: ' + data.lead_source);

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

            if (data.client) {
                updateField('header-primary-contact', 'Primary Contact: ' + data.client.primary_contact);
                updateField('header-primary-email', 'Primary Email: ' + data.client.primary_email);
                updateField('header-primary-phone', 'Primary Phone: ' + data.client.primary_phone1);
                updateField('header-partner-contact', 'Partner Contact: ' + data.client.partner_contact);
            }
        }

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

        updateField('header-location', 'Location: ' + data.location);
        updateField('header-lead-source', 'Lead Source: ' + data.lead_source);
        updateField('header-csr', 'Sales Person: ' + data.csr);
        updateField('header-status', 'Status: ' + data.status);
    })
    .catch(error => {
        console.error('Error updating contract display:', error);
    });
}

function updateField(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    } else {
        console.error('Element not found:', elementId);
    }
}
