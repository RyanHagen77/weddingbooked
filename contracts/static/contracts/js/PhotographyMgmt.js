console.log("PhotographyMgmt.js loaded and executed!");

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function() {
        const targetTab = this.getAttribute('href').substring(1); // Get the target tab ID (e.g., 'photography')
        const targetButtonId = 'save' + targetTab.charAt(0).toUpperCase() + targetTab.slice(1) + 'Section'; // Construct the button ID
        document.querySelectorAll('.save-btn').forEach(btn => {
            if (btn.id === targetButtonId) {
                btn.style.display = 'block'; // Show the save button for the active tab
            } else {
                btn.style.display = 'none'; // Hide other save buttons
            }
        });
    });
});
// Trigger click event on the active tab link to ensure correct initial state
document.querySelector('.nav-link.active').click();

document.addEventListener('DOMContentLoaded', () => {
    const PhotographyMgmt = {
        init() {
            this.setupElements();
            this.bindEvents();

            const serviceTypes = ['Photography', 'Videography', 'Dj', 'Photobooth'];

            // Fetch and populate packages, additional staff, and overtime options for each service type
            serviceTypes.forEach(serviceType => {
                this.fetchAndPopulatePackages(serviceType);
                this.fetchAndPopulateAdditionalStaff(serviceType);
                this.fetchAndPopulateOvertimeOptions(serviceType);
                this.updateOvertimePriceDisplay(serviceType);
                this.updateTotalServiceCost(serviceType);
            });

            // Fetch and populate engagement sessions
            this.fetchAndPopulateEngagementSessions();

            // Fetch and update overtime entries if contract ID is available
            const contractId = this.getContractId();
            if (contractId) {
                serviceTypes.forEach(serviceType => {
                    this.fetchAndUpdateOvertimeEntries(contractId, serviceType);
                    this.updateTotalOvertimeCost(serviceType);
                });
            } else {
                console.error('Contract ID is not available.');
            }
        },


        setupElements() {
            this.eventDateElement = document.getElementById('id_event_date');

            // Define an array of service types
            const serviceTypes = ['Photography', 'Videography', 'Dj', 'Photobooth'];

            // Initialize properties for each service type
            serviceTypes.forEach(serviceType => {
                const serviceTypeLower = serviceType.toLowerCase();

                // Saved IDs
                this[`saved${serviceType}PackageId`] = document.getElementById(`hiddenSaved${serviceType}PackageId`) ? document.getElementById(`hiddenSaved${serviceType}PackageId`).value : null;
                this[`saved${serviceType}AdditionalStaffId`] = document.getElementById(`hiddenSaved${serviceType}AdditionalStaffId`) ? document.getElementById(`hiddenSaved${serviceType}AdditionalStaffId`).value : null;

                // Dropdowns
                this[`${serviceTypeLower}PackageDropdown`] = document.getElementById(`id_${serviceTypeLower}_package`);
            // Display elements
                this[`${serviceTypeLower}PackageHoursDisplayElement`] = document.getElementById(`${serviceTypeLower}-package-hours`);
                this[`${serviceTypeLower}AdditionalStaffHoursDisplayElement`] = document.getElementById(`additional-${serviceTypeLower}-hours`);
                this[`${serviceTypeLower}PriceDisplayElement`] = document.getElementById(`${serviceTypeLower}-package-price`);
                this[`${serviceTypeLower}AdditionalStaffPriceDisplayElement`] = document.getElementById(`additional-${serviceTypeLower}-price`); // Add this line
            });

            const contractId = this.getContractId();
                if (contractId) {
                    const serviceTypes = ['Photography', 'Videography', 'Dj', 'Photobooth'];
                    serviceTypes.forEach(serviceType => {
                        this.fetchAndUpdateOvertimeEntries(contractId, serviceType);
                    });
                } else {
                    console.error('Contract ID is not available.');
                }
            // Engagement session specific
            this.savedEngagementSessionId = document.getElementById('hiddenSavedEngagementSessionId') ? document.getElementById('hiddenSavedEngagementSessionId').value : null;
        },


        bindEvents() {
            const serviceTypes = ['Photography', 'Videography', 'Dj', 'Photobooth'];

            serviceTypes.forEach(serviceType => {
                const serviceTypeLower = serviceType.toLowerCase();

                // Bind for package selection
                const packageDropdown = this[`${serviceTypeLower}PackageDropdown`];
                if (packageDropdown) {
                    packageDropdown.addEventListener('change', () => {
                        this.updatePriceAndHoursDisplay(
                            `id_${serviceTypeLower}_package`,
                            `${serviceTypeLower}-package-price`,
                            `${serviceTypeLower}-package-hours`,
                            serviceType
                        );
                        this.updateTotalServiceCost(serviceType);
                    });
                }

                // Bind for additional staff selection
                const additionalDropdown = document.getElementById(`id_${serviceTypeLower}_additional`);
                if (additionalDropdown) {
                    additionalDropdown.addEventListener('change', () => {
                        this.updatePriceAndHoursDisplay(
                            `id_${serviceTypeLower}_additional`,
                            `additional-${serviceTypeLower}-price`,
                            `additional-${serviceTypeLower}-hours`,
                            serviceType
                        );
                        this.updateTotalServiceCost(serviceType);
                    });
                }

                            // Bind for engagement session selection if applicable
                const engagementDropdown = document.getElementById('id_engagement_session');
                if (engagementDropdown) {
                    engagementDropdown.addEventListener('change', () => {
                        this.updatePriceAndHoursDisplay(
                            'id_engagement_session',
                            'engagement-session-price',
                            null, // No hours element for engagement session
                            'Photography'
                        );
                    });
                }

                const savePhotographySectionButton = document.getElementById('savePhotographySection');
                const saveVideographySectionButton = document.getElementById('saveVideographySection');
                const saveDjSectionButton = document.getElementById('saveDjSection');
                const savePhotoboothSectionButton = document.getElementById('savePhotoboothSection');

                if (savePhotographySectionButton) {
                    savePhotographySectionButton.addEventListener('click', this.savePhotographySection.bind(this));
                }

                if (saveVideographySectionButton) {
                    saveVideographySectionButton.addEventListener('click', this.saveVideographySection.bind(this));
                }

                if (saveDjSectionButton) {
                    saveDjSectionButton.addEventListener('click', this.saveDjSection.bind(this));
                }

                if (savePhotoboothSectionButton) {
                    savePhotoboothSectionButton.addEventListener('click', this.savePhotoboothSection.bind(this));
                }


                        // Bind for overtime options
                const overtimeDropdown = document.getElementById(`id_${serviceTypeLower}_overtime`);
                const overtimeHoursInput = document.getElementById(`id_${serviceTypeLower}_overtime_hours`);
                if (overtimeDropdown) {
                    overtimeDropdown.addEventListener('change', () => {
                        this.updateOvertimePriceDisplay(serviceType);
                        this.updateTotalServiceCost(serviceType); // Update total service cost
                    });
                }
                if (overtimeHoursInput) {
                    overtimeHoursInput.addEventListener('input', () => {
                        this.updateOvertimePriceDisplay(serviceType);
                        this.updateTotalServiceCost(serviceType); // Update total service cost
                    });
                }

                // Binding for the Add Overtime Entry button
                const addOvertimeEntryButton = document.getElementById(`add${serviceType}OvertimeEntryButton`);
                if (addOvertimeEntryButton) {
                    addOvertimeEntryButton.addEventListener('click', () => {
                        this.showOvertimeForm('', serviceType);
                    });
                }

                // Binding for the Save Overtime Entry button
                const saveOvertimeEntryButton = document.getElementById(`save${serviceType}OvertimeEntryButton`);
                if (saveOvertimeEntryButton) {
                    saveOvertimeEntryButton.addEventListener('click', () => {
                        this.saveOvertimeEntry(serviceType);
                    });
                }
            });

            // Event delegation for dynamic edit and remove buttons within the overtime entries display for all service types
            document.querySelectorAll('.overtime-entries-display').forEach(display => {
                display.addEventListener('click', (e) => {
                    if (e.target && e.target.matches('.edit-overtime-button')) {
                        const entryId = e.target.getAttribute('data-id');
                        const serviceType = e.target.getAttribute('data-service');
                        this.loadEntryForEdit(entryId, serviceType);
                    } else if (e.target && e.target.matches('.remove-overtime-button')) {
                        const entryId = e.target.getAttribute('data-id');
                        const serviceType = e.target.getAttribute('data-service');
                        this.removeOvertimeEntry(entryId, serviceType);
                    }
                });
            });
        },

        getContractId() {
            const contractIdElement = document.getElementById('contractId'); // Ensure this is the correct ID
            return contractIdElement ? contractIdElement.value : null; // This correctly retrieves the input's value
        },


    fetchAndPopulatePackages(serviceType) {
        const url = `/contracts/api/package_options/?service_type=${serviceType}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                const defaultOptionText = `Select a ${serviceType} Package`;
                this.populateDropdown(data.packages, defaultOptionText, serviceType);
            })
            .catch(error => console.error(`Error fetching ${serviceType} packages:`, error));
    },




    getPriceDisplayElementId(serviceType, category) {
        const serviceTypeLower = serviceType.toLowerCase();
        const categoryLower = category.toLowerCase();
        if (categoryLower === 'package') {
            return `${serviceTypeLower}-package-price`;
        } else if (categoryLower === 'additionalstaff') {
            return `additional-${serviceTypeLower}-price`;
        }
        // Add more conditions for other categories if needed
    },

    getHoursDisplayElementId(serviceType, category) {
        const serviceTypeLower = serviceType.toLowerCase();
        const categoryLower = category.toLowerCase();
        if (categoryLower === 'package') {
            return `${serviceTypeLower}-package-hours`;
        } else if (categoryLower === 'additionalstaff') {
            return `additional-${serviceTypeLower}-hours`;
        }
        // Add more conditions for other categories if needed
    },

    populateDropdown(packages, defaultOptionText, serviceType) {
        console.log(`Populating dropdown for service type: ${serviceType}`);

        let dropdown;
        let savedPackageId;
        if (serviceType === 'Photography') {
            dropdown = this.photographyPackageDropdown;
            savedPackageId = this.savedPhotographyPackageId;
        } else if (serviceType === 'Videography') {
            dropdown = this.videographyPackageDropdown;
            savedPackageId = this.savedVideographyPackageId;
        } else if (serviceType === 'Dj') {
            dropdown = this.djPackageDropdown;
            savedPackageId = this.savedDjPackageId;
        } else if (serviceType === 'Photobooth') {
            dropdown = this.photoboothPackageDropdown;
            savedPackageId = this.savedPhotoboothPackageId;
        }

        console.log(`Dropdown element:`, dropdown);
        console.log(`Saved package ID for ${serviceType}:`, savedPackageId);

        let optionsHtml = `<option value="">${defaultOptionText}</option>`;
        packages.forEach(pkg => {
            let isSelected = pkg.id.toString() === savedPackageId;
            optionsHtml += `<option value="${pkg.id}" data-price="${parseFloat(pkg.price).toFixed(2)}" data-hours="${pkg.hours}"${isSelected ? ' selected' : ''}>${pkg.name} - $${parseFloat(pkg.price).toFixed(2)} - ${pkg.hours} hours</option>`;
        });
        dropdown.innerHTML = optionsHtml;

        // Call the appropriate update function based on the service type
        const priceDisplayElementId = this.getPriceDisplayElementId(serviceType, 'Package');
        const hoursDisplayElementId = this.getHoursDisplayElementId(serviceType, 'Package');
        this.updatePriceAndHoursDisplay(dropdown.id, priceDisplayElementId, hoursDisplayElementId, serviceType);

        console.log(`Updated dropdown for ${serviceType} with options:`, optionsHtml);
    },


    updatePriceAndHoursDisplay(dropdownId, priceDisplayElementId, hoursDisplayElementId = null, serviceType) {
            console.log('Price Display Element ID:', priceDisplayElementId); // Debugging statement
            const dropdown = document.getElementById(dropdownId);
        if (dropdown) {
            const selectedOption = dropdown.options[dropdown.selectedIndex];
            const price = selectedOption ? selectedOption.getAttribute('data-price') : '0.00';

            if (priceDisplayElementId) {
                const priceDisplayElement = document.getElementById(priceDisplayElementId);
                priceDisplayElement.textContent = `$${parseFloat(price).toFixed(2)}`;
            }

            if (hoursDisplayElementId) {
                const hours = selectedOption ? selectedOption.getAttribute('data-hours') : '0';
                const hoursDisplayElement = document.getElementById(hoursDisplayElementId);
                hoursDisplayElement.textContent = `${hours} hours`;
            }

            this.updateTotalServiceCost(serviceType); // Recalculate the total cost
        }
    },

    fetchAndPopulateAdditionalStaff(serviceType) {
        const url = `/contracts/api/additional_staff_options/?service_type=${serviceType}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.populateAdditionalStaffDropdown(data.staff_options, `Select Additional ${serviceType} Staff`, serviceType);
            })
            .catch(error => console.error(`Error fetching additional staff options for ${serviceType}:`, error));
    },

    populateAdditionalStaffDropdown(options, defaultOptionText, serviceType) {
        let dropdownId = `id_${serviceType.toLowerCase()}_additional`;
        let savedStaffId = this[`saved${serviceType}AdditionalStaffId`];
        let dropdown = document.getElementById(dropdownId);

        let optionsHtml = `<option value="">${defaultOptionText}</option>`;
        options.forEach(option => {
            let isSelected = option.id.toString() === savedStaffId;
            optionsHtml += `<option value="${option.id}" data-price="${parseFloat(option.price).toFixed(2)}" data-hours="${option.hours}"${isSelected ? ' selected' : ''}>${option.name} - $${parseFloat(option.price).toFixed(2)} - ${option.hours} hours</option>`;
        });
        dropdown.innerHTML = optionsHtml;

        // Update price and hours display
        this.updatePriceAndHoursDisplay(dropdownId, `additional-${serviceType.toLowerCase()}-price`, `additional-${serviceType.toLowerCase()}-hours`, serviceType);
    },

    fetchAndPopulateEngagementSessions() {
        const url = `/contracts/api/engagement_session_options`; // Adjust the URL as needed
        fetch(url)
            .then(response => response.json())
            .then(data => {
                console.log('API response for engagement sessions:', data); // Debugging statement
                if (Array.isArray(data.sessions)) {
                    this.populateEngagementSessionDropdown(data.sessions, 'Select an Engagement Session');
                } else {
                    console.error('Error: Expected an array of sessions, but received:', data);
                }
            })
            .catch(error => console.error('Error fetching engagement session options:', error));
    },


    populateEngagementSessionDropdown(sessions, defaultOptionText) {
        console.log('Sessions in populate function:', sessions); // Debugging statement
        let optionsHtml = `<option value="">${defaultOptionText}</option>`;
        sessions.forEach(session => {
            let isSelected = session.id.toString() === this.savedEngagementSessionId; // Ensure string comparison
            optionsHtml += `<option value="${session.id}" data-price="${parseFloat(session.price).toFixed(2)}"${isSelected ? ' selected' : ''}>${session.name} - $${parseFloat(session.price).toFixed(2)}</option>`;
        });
        const dropdown = document.getElementById('id_engagement_session');
        dropdown.innerHTML = optionsHtml;

        // Update price display
        this.updatePriceAndHoursDisplay('id_engagement_session', 'engagement-session-price', null, 'Photography');
    },


        showOvertimeForm(entryId, serviceType) {
            const entryIdInput = document.getElementById(`${serviceType.toLowerCase()}OvertimeEntryId`);
            const optionSelect = document.getElementById(`${serviceType.toLowerCase()}OvertimeOptionSelect`);
            const hoursInput = document.getElementById(`${serviceType.toLowerCase()}OvertimeHours`);
            const form = document.getElementById(`${serviceType.toLowerCase()}OvertimeEntryForm`);

            if (entryIdInput && optionSelect && hoursInput && form) {
                entryIdInput.value = entryId || '';
                optionSelect.value = ''; // Reset or set to entry's current value
                hoursInput.value = ''; // Reset or set to entry's current hours
                form.style.display = 'block'; // Show the form
            }
        },

        getCSRFToken() {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            return csrfToken;
        },

        saveOvertimeEntry(serviceType) {
            const contractId = this.getContractId();
            if (!contractId) {
                console.error("Contract ID is undefined.");
                return;
            }

            const entryIdInputId = serviceType.toLowerCase() + 'OvertimeEntryId';
            const optionSelectId = serviceType.toLowerCase() + 'OvertimeOptionSelect';
            const hoursInputId = serviceType.toLowerCase() + 'OvertimeHours';

            const entryId = document.getElementById(entryIdInputId).value;
            const optionId = document.getElementById(optionSelectId).value;
            const hours = document.getElementById(hoursInputId).value;

            const headers = new Headers({
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            });

            const body = JSON.stringify({ entryId, optionId, hours, serviceType });

            fetch(`/contracts/${contractId}/save_overtime_entry/`, {
                method: 'POST',
                headers: headers,
                body: body,
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    this.clearFormFields(serviceType); // Clear form fields for new entries
                    return this.fetchAndUpdateOvertimeEntries(contractId, serviceType); // Refresh list to show the new entry
                } else {
                    console.error('Error saving overtime entry:', data.message);
                }
            })
            .then(() => {
                this.updateTotalOvertimeCost(serviceType);
                this.updateTotalServiceCost(serviceType); // Update the total cost for the service type
            })
            .catch(error => console.error('Error:', error));
        },




        clearFormFields(serviceType) {
            const optionSelectId = serviceType.toLowerCase() + 'OvertimeOptionSelect';
            const hoursInputId = serviceType.toLowerCase() + 'OvertimeHours';
            const entryIdInputId = serviceType.toLowerCase() + 'OvertimeEntryId';

            const optionSelect = document.getElementById(optionSelectId);
            const hoursInput = document.getElementById(hoursInputId);
            const entryIdInput = document.getElementById(entryIdInputId);

            if (optionSelect) {
                optionSelect.selectedIndex = 0;
            }
            if (hoursInput) {
                hoursInput.value = '';
            }
            if (entryIdInput) {
                entryIdInput.value = ''; // Clear this in case it was an edit
            }
        },

        appendOvertimeEntry(entry, serviceType) {
            const displayId = serviceType.toLowerCase() + 'OvertimeEntriesDisplay';
            const display = document.getElementById(displayId);
            if (!display) {
                console.error(`Display element with ID ${displayId} not found.`);
                return;
            }

            // Check if overtime_option is an object and has a property 'role'
            let overtimeOptionDisplay = '';
            if (typeof entry.overtime_option === 'object' && entry.overtime_option.role) {
                overtimeOptionDisplay = entry.overtime_option.role;
            } else if (typeof entry.overtime_option === 'string') {
                // If overtime_option is a string, use it directly
                overtimeOptionDisplay = entry.overtime_option;
            } else {
                // Fallback or default display if neither condition is met
                overtimeOptionDisplay = 'Unknown Option';
            }

            // When appending overtime entries to the DOM
            const row = document.createElement('tr');
            row.setAttribute('data-id', entry.id); // Make sure 'entry.id' matches the overtime entry's ID
            // Populate row with entry data and append to the table

            row.innerHTML = `
                <td>${overtimeOptionDisplay}</td>
                <td>${entry.hours} hours</td>
                <td>$${parseFloat(entry.cost).toFixed(2)}</td> <!-- Assuming 'cost' is always present -->
                <td><!-- Assigned Staff --></td>
                <td>
                    <button type="button" class="edit-overtime-button" data-id="${entry.id}" data-service="${serviceType}">Edit</button>
                    <button type="button" class="remove-overtime-button" data-id="${entry.id}" data-service="${serviceType}">Remove</button>
                </td>
            `;
            display.appendChild(row);
        },


        fetchAndPopulateOvertimeOptions(serviceType) {
            const url = `/contracts/api/overtime_options?service_type=${serviceType}`;
            fetch(url)
                .then(response => response.json())
                .then(overtimeOptions => {
                    const dropdownId = serviceType.toLowerCase() + 'OvertimeOptionSelect'; // Construct the dropdown ID based on the service type
                    const savedOptionId = this['saved' + serviceType + 'OvertimeOptionId']; // Get the saved option ID for the service type
                    this.populateOvertimeDropdown(overtimeOptions, 'Select Overtime Option', dropdownId, savedOptionId);
                })
                .catch(error => console.error('Error fetching overtime options:', error));
        },


        populateOvertimeDropdown(overtimeOptions, defaultOptionText, dropdownId, savedOptionId) {
            const dropdown = document.getElementById(dropdownId);
            if (!dropdown) {
                console.error(`Dropdown with ID ${dropdownId} not found`);
                return;
            }

            let optionsHtml = `<option value="">${defaultOptionText}</option>`;
            overtimeOptions.forEach(option => {
                let isSelected = option.id.toString() === savedOptionId;
                optionsHtml += `<option value="${option.id}" data-price="${parseFloat(option.rate_per_hour).toFixed(2)}"${isSelected ? ' selected' : ''}>${option.role} - $${parseFloat(option.rate_per_hour).toFixed(2)}/hr</option>`;
            });
            dropdown.innerHTML = optionsHtml;
        },


        fetchAndUpdateOvertimeEntries(contractId, serviceType) {
            console.log(`Fetching overtime entries for contract ${contractId} and service type ${serviceType}`);
            fetch(`/contracts/${contractId}/overtime_entries/?service_type=${serviceType}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        console.log('Successfully fetched overtime entries:', data.entries);
                        const displayId = serviceType.toLowerCase() + 'OvertimeEntriesDisplay';
                        const display = document.getElementById(displayId);
                        display.innerHTML = ''; // Clear existing entries

                        data.entries.forEach(entry => {
                            console.log(`Appending entry ${entry.id} to ${displayId}`);
                            this.appendOvertimeEntry(entry, serviceType);
                        });

                         this.updateTotalOvertimeCost(serviceType);
                         this.updateOvertimePriceDisplay(serviceType);
                         this.updateTotalServiceCost(serviceType); // Add this line
                    } else {

                        console.error('Failed to fetch overtime entries:', data.message);
                    }
                })
                .catch(error => {
                    console.error('Error fetching overtime entries:', error);
                });
        },

        updateOvertimePriceDisplay(serviceType) {
            const overtimeDropdown = document.getElementById(`id_${serviceType.toLowerCase()}_overtime`);
            const overtimeHoursInput = document.getElementById(`id_${serviceType.toLowerCase()}_overtime_hours`);
            const priceDisplayElement = document.getElementById(`${serviceType.toLowerCase()}-overtime-price`);

            if (overtimeDropdown && overtimeHoursInput && priceDisplayElement) {
                const selectedOption = overtimeDropdown.options[overtimeDropdown.selectedIndex];
                const ratePerHour = selectedOption ? parseFloat(selectedOption.getAttribute('data-price')) : 0;
                const hours = parseFloat(overtimeHoursInput.value) || 0;
                const cost = ratePerHour * hours;
                priceDisplayElement.textContent = `$${cost.toFixed(2)}`;
            }
        },


        loadEntryForEdit(entryId, serviceType) {
            fetch(`/contracts/${entryId}/get_overtime_entry/`)  // Adjust the URL to match your actual endpoint
            .then(response => response.json())
            .then(data => {
                const entryFormId = serviceType.toLowerCase() + 'OvertimeEntryForm';
                const entryIdInputId = serviceType.toLowerCase() + 'OvertimeEntryId';
                const optionSelectId = serviceType.toLowerCase() + 'OvertimeOptionSelect';
                const hoursInputId = serviceType.toLowerCase() + 'OvertimeHours';

                document.getElementById(entryIdInputId).value = data.id;
                document.getElementById(optionSelectId).value = data.overtime_option_id;  // Ensure this matches your select option values
                document.getElementById(hoursInputId).value = data.hours;
                document.getElementById(entryFormId).style.display = 'block';
            })
            .catch(error => console.error('Error:', error));

            this.updateOvertimePriceDisplay(serviceType);
            this.updateTotalOvertimeCost(serviceType);
            this.updateTotalServiceCost(serviceType); // Add this line
        },

        removeOvertimeEntry(entryId, serviceType) {
            fetch(`/contracts/${entryId}/delete_overtime_entry/`, {
               method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({ entryId })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // Remove the entry's row from the UI or refresh the list
                    document.querySelector(`tr[data-id="${entryId}"]`).remove();
                    // Update the costs after the entry has been successfully removed
                    this.updateTotalOvertimeCost(serviceType);
                    this.updateTotalServiceCost(serviceType); // Add this line
                } else {
                    console.error('Error removing entry:', data.message);
                }
            })
            .catch(error => console.error('Error:', error));
        },

        calculateTotalOvertimeCost(serviceType) {
            let totalOvertimeCost = 0;
            const displayId = `${serviceType.toLowerCase()}OvertimeEntriesDisplay`;
            const overtimeEntries = document.querySelectorAll(`#${displayId} tr`);
            overtimeEntries.forEach(entry => {
                const cost = parseFloat(entry.querySelector('td:nth-child(3)').textContent.replace('$', '')) || 0;
                totalOvertimeCost += cost;
            });
            return totalOvertimeCost;
        },

        updateTotalOvertimeCost(serviceType) {
            const totalCost = this.calculateTotalOvertimeCost(serviceType);
            const totalCostDisplayId = `total-${serviceType.toLowerCase()}-overtime-cost`;
            const totalCostDisplay = document.getElementById(totalCostDisplayId);
            if (totalCostDisplay) {
                totalCostDisplay.textContent = `$${totalCost.toFixed(2)}`;
            }
        },


    updateTotalServiceCost(serviceType) {
        let packagePrice = 0;
        let additionalPrice = 0;
        let engagementSessionPrice = 0;
        let totalOvertimeCost = this.calculateTotalOvertimeCost(serviceType);

        const packagePriceElement = document.getElementById(`${serviceType.toLowerCase()}-package-price`);
        if (packagePriceElement) {
            packagePrice = parseFloat(packagePriceElement.textContent.replace('$', '')) || 0;
        }

        const additionalPriceElement = document.getElementById(`additional-${serviceType.toLowerCase()}-price`);
        if (additionalPriceElement) {
            additionalPrice = parseFloat(additionalPriceElement.textContent.replace('$', '')) || 0;
        }

        // Only add engagement session price for Photography service
        if (serviceType === 'Photography') {
            const engagementSessionPriceElement = document.getElementById('engagement-session-price');
            if (engagementSessionPriceElement) {
                engagementSessionPrice = parseFloat(engagementSessionPriceElement.textContent.replace('$', '')) || 0;
            }
        }

        let totalServiceCost = packagePrice + additionalPrice + engagementSessionPrice + totalOvertimeCost;

        const totalServiceCostDisplay = document.getElementById(`total-${serviceType.toLowerCase()}-cost`);
        if (totalServiceCostDisplay) {
            totalServiceCostDisplay.textContent = `$${totalServiceCost.toFixed(2)}`;
        }
    },


    savePhotographySection() {
        const contractId = this.getContractId();
        if (!contractId) {
            console.error("Contract ID is undefined.");
            return;
        }

        // Collecting data from the UI
        const formData = new FormData();
        formData.append('photography_package', document.getElementById('id_photography_package').value);
        formData.append('photography_additional', document.getElementById('id_photography_additional').value);
        formData.append('engagement_session', document.getElementById('id_engagement_session').value);
        // Videography fields
        formData.append('videography_package', document.getElementById('id_videography_package').value);
        formData.append('videography_additional', document.getElementById('id_videography_additional').value);
        // DJ fields
        formData.append('dj_package', document.getElementById('id_dj_package').value);
        formData.append('dj_additional', document.getElementById('id_dj_additional').value);

        // Photobooth fields
        formData.append('photobooth_package', document.getElementById('id_photobooth_package').value);
        formData.append('photobooth_additional', document.getElementById('id_photobooth_additional').value);



        // Append CSRF token to the form data
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);

        // AJAX request to submit the form
        fetch(`/contracts/${contractId}/edit_services/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                console.log('Photography section saved successfully');
                // Perform any additional actions on success, such as updating the UI or displaying a success message
            } else {
                console.error('Error saving photography section:', data.message);
                // Handle the error, possibly displaying a message to the user
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Handle network or other unexpected errors
        });
    },

    saveVideographySection() {
        const contractId = this.getContractId();
        if (!contractId) {
            console.error("Contract ID is undefined.");
            return;
        }

                // Collecting data from the UI
        const formData = new FormData();
        formData.append('photography_package', document.getElementById('id_photography_package').value);
        formData.append('photography_additional', document.getElementById('id_photography_additional').value);
        formData.append('engagement_session', document.getElementById('id_engagement_session').value);

        // Videography fields
        formData.append('videography_package', document.getElementById('id_videography_package').value);
        formData.append('videography_additional', document.getElementById('id_videography_additional').value);
        // DJ fields
        formData.append('dj_package', document.getElementById('id_dj_package').value);
        formData.append('dj_additional', document.getElementById('id_dj_additional').value);

        // Photobooth fields
        formData.append('photobooth_package', document.getElementById('id_photobooth_package').value);
        formData.append('photobooth_additional', document.getElementById('id_photobooth_additional').value);


        // Append CSRF token to the form data
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);

        // AJAX request to submit the form
        fetch(`/contracts/${contractId}/edit_services/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                console.log('Videography section saved successfully');
                // Perform any additional actions on success, such as updating the UI or displaying a success message
            } else {
                console.error('Error saving videography section:', data.message);
                // Handle the error, possibly displaying a message to the user
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Handle network or other unexpected errors
        });
    },

    saveDjSection() {
        const contractId = this.getContractId();
        if (!contractId) {
            console.error("Contract ID is undefined.");
            return;
        }

                // Collecting data from the UI
        const formData = new FormData();
        formData.append('photography_package', document.getElementById('id_photography_package').value);
        formData.append('photography_additional', document.getElementById('id_photography_additional').value);
        formData.append('engagement_session', document.getElementById('id_engagement_session').value);
        // Videography fields
        formData.append('videography_package', document.getElementById('id_videography_package').value);
        formData.append('videography_additional', document.getElementById('id_videography_additional').value);
        // DJ fields
        formData.append('dj_package', document.getElementById('id_dj_package').value);
        formData.append('dj_additional', document.getElementById('id_dj_additional').value);

        // Photobooth fields
        formData.append('photobooth_package', document.getElementById('id_photobooth_package').value);
        formData.append('photobooth_additional', document.getElementById('id_photobooth_additional').value);


        // Append CSRF token to the form data
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);

        // AJAX request to submit the form
        fetch(`/contracts/${contractId}/edit_services/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                console.log('DJ section saved successfully');
                // Perform any additional actions on success, such as updating the UI or displaying a success message
            } else {
                console.error('Error saving DJ section:', data.message);
                // Handle the error, possibly displaying a message to the user
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Handle network or other unexpected errors
        });
    },

    savePhotoboothSection() {
        const contractId = this.getContractId();
        if (!contractId) {
            console.error("Contract ID is undefined.");
            return;
        }

                // Collecting data from the UI
        const formData = new FormData();
        formData.append('photography_package', document.getElementById('id_photography_package').value);
        formData.append('photography_additional', document.getElementById('id_photography_additional').value);
        formData.append('engagement_session', document.getElementById('id_engagement_session').value);
        // Videography fields
        formData.append('videography_package', document.getElementById('id_videography_package').value);
        formData.append('videography_additional', document.getElementById('id_videography_additional').value);
        // DJ fields
        formData.append('dj_package', document.getElementById('id_dj_package').value);
        formData.append('dj_additional', document.getElementById('id_dj_additional').value);

        // Photobooth fields
        formData.append('photobooth_package', document.getElementById('id_photobooth_package').value);
        formData.append('photobooth_additional', document.getElementById('id_photobooth_additional').value);

        // Append CSRF token to the form data
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);

        // AJAX request to submit the form
        fetch(`/contracts/${contractId}/edit_services/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                console.log('Photobooth section saved successfully');
                // Perform any additional actions on success, such as updating the UI or displaying a success message
            } else {
                console.error('Error saving Photobooth section:', data.message);
                // Handle the error, possibly displaying a message to the user
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Handle network or other unexpected errors
        });
    },

};
    // After everything is initialized, update the total cost
    PhotographyMgmt.updateTotalServiceCost('Photography');
    PhotographyMgmt.updateTotalServiceCost('Videography');
    PhotographyMgmt.updateTotalServiceCost('Dj');
    PhotographyMgmt.updateTotalServiceCost('Photobooth');


    PhotographyMgmt.init();
});