document.addEventListener('DOMContentLoaded', () => {
    const ServiceMgmt = {
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

            const serviceTypes = ['Photography', 'Videography', 'Dj', 'Photobooth'];

            serviceTypes.forEach(serviceType => {
                const serviceTypeLower = serviceType.toLowerCase();

                this[`saved${serviceType}PackageId`] = document.getElementById(`hiddenSaved${serviceType}PackageId`) ? document.getElementById(`hiddenSaved${serviceType}PackageId`).value : null;
                this[`saved${serviceType}AdditionalStaffId`] = document.getElementById(`hiddenSaved${serviceType}AdditionalStaffId`) ? document.getElementById(`hiddenSaved${serviceType}AdditionalStaffId`).value : null;

                this[`${serviceTypeLower}PackageDropdown`] = document.getElementById(`id_${serviceTypeLower}_package`);
                this[`${serviceTypeLower}PackageHoursDisplayElement`] = document.getElementById(`${serviceTypeLower}-package-hours`);
                this[`${serviceTypeLower}AdditionalStaffHoursDisplayElement`] = document.getElementById(`additional-${serviceTypeLower}-hours`);
                this[`${serviceTypeLower}PriceDisplayElement`] = document.getElementById(`${serviceTypeLower}-package-price`);
                this[`${serviceTypeLower}AdditionalStaffPriceDisplayElement`] = document.getElementById(`additional-${serviceTypeLower}-price`);
            });

            this.savedEngagementSessionId = document.getElementById('hiddenSavedEngagementSessionId') ? document.getElementById('hiddenSavedEngagementSessionId').value : null;
        },

        bindEvents() {
            const serviceTypes = ['Photography', 'Videography', 'Dj', 'Photobooth'];

            serviceTypes.forEach(serviceType => {
                const serviceTypeLower = serviceType.toLowerCase();

                // Handle package dropdown changes
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

                // Handle additional staff dropdown changes
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

                // Handle engagement session changes (specific to Photography)
                if (serviceType === 'Photography') {
                    const engagementDropdown = document.getElementById('id_engagement_session');
                    if (engagementDropdown) {
                        engagementDropdown.addEventListener('change', () => {
                            this.updatePriceAndHoursDisplay(
                                'id_engagement_session',
                                'engagement-session-price',
                                null,
                                'Photography'
                            );
                        });
                    }
                }

                // Bind save button for each service type
                const saveSectionButton = document.getElementById(`save${serviceType}Section`);
                if (saveSectionButton) {
                    saveSectionButton.addEventListener('click', (event) => {
                        event.preventDefault(); // Prevent default form submission
                        this.saveSection(serviceType);
                    });
                }

                // Handle overtime dropdown changes
                const overtimeDropdown = document.getElementById(`id_${serviceTypeLower}_overtime`);
                const overtimeHoursInput = document.getElementById(`id_${serviceTypeLower}_overtime_hours`);
                if (overtimeDropdown) {
                    overtimeDropdown.addEventListener('change', () => {
                        this.updateOvertimePriceDisplay(serviceType);
                        this.updateTotalServiceCost(serviceType);
                    });
                }
                if (overtimeHoursInput) {
                    overtimeHoursInput.addEventListener('input', () => {
                        this.updateOvertimePriceDisplay(serviceType);
                        this.updateTotalServiceCost(serviceType);
                    });
                }

                // Bind add overtime entry button
                const addOvertimeEntryButton = document.getElementById(`add${serviceType}OvertimeEntryButton`);
                if (addOvertimeEntryButton) {
                    addOvertimeEntryButton.addEventListener('click', () => {
                        this.showOvertimeForm('', serviceType);
                    });
                }

                // Bind save overtime entry button
                const saveOvertimeEntryButton = document.getElementById(`save${serviceType}OvertimeEntryButton`);
                if (saveOvertimeEntryButton) {
                    saveOvertimeEntryButton.addEventListener('click', () => {
                        this.saveOvertimeEntry(serviceType);
                    });
                }
            });


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
            const contractIdElement = document.getElementById('contractId');
            return contractIdElement ? contractIdElement.value : null;
        },

        fetchAndPopulatePackages(serviceType) {
            const url = `/services/api/package_options/?service_type=${serviceType}`;
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
        },

        getHoursDisplayElementId(serviceType, category) {
            const serviceTypeLower = serviceType.toLowerCase();
            const categoryLower = category.toLowerCase();
            if (categoryLower === 'package') {
                return `${serviceTypeLower}-package-hours`;
            } else if (categoryLower === 'additionalstaff') {
                return `additional-${serviceTypeLower}-hours`;
            }
        },

        populateDropdown(packages, defaultOptionText, serviceType) {
            let dropdown;
            let savedPackageId;
            const serviceTypeLower = serviceType.toLowerCase();

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

            let optionsHtml = `<option value="">${defaultOptionText}</option>`;
            packages.forEach(pkg => {
                let isSelected = pkg.id.toString() === savedPackageId;
                optionsHtml += `<option value="${pkg.id}" data-price="${parseFloat(pkg.price).toFixed(2)}" data-hours="${pkg.hours}"${isSelected ? ' selected' : ''}>${pkg.name} - $${parseFloat(pkg.price).toFixed(2)} - ${pkg.hours} hours</option>`;
            });
            dropdown.innerHTML = optionsHtml;

            const priceDisplayElementId = this.getPriceDisplayElementId(serviceType, 'Package');
            const hoursDisplayElementId = this.getHoursDisplayElementId(serviceType, 'Package');
            this.updatePriceAndHoursDisplay(dropdown.id, priceDisplayElementId, hoursDisplayElementId, serviceType);
        },

        updatePriceAndHoursDisplay(dropdownId, priceDisplayElementId, hoursDisplayElementId = null, serviceType) {
            const dropdown = document.getElementById(dropdownId);
            if (dropdown) {
                const selectedOption = dropdown.options[dropdown.selectedIndex];
                let price = selectedOption ? selectedOption.getAttribute('data-price') : '0.00';
                let hours = selectedOption ? selectedOption.getAttribute('data-hours') : '0';

                if (price === null || isNaN(parseFloat(price))) {
                    price = '';
                } else {
                    price = `$${parseFloat(price).toFixed(2)}`;
                }

                if (hours === null || isNaN(parseFloat(hours))) {
                    hours = '';
                } else {
                    hours = `${hours} hours`;
                }

                if (priceDisplayElementId) {
                    const priceDisplayElement = document.getElementById(priceDisplayElementId);
                    priceDisplayElement.textContent = price;
                }

                if (hoursDisplayElementId) {
                    const hoursDisplayElement = document.getElementById(hoursDisplayElementId);
                    hoursDisplayElement.textContent = hours;
                }

                this.updateTotalServiceCost(serviceType);
            }
        },

        fetchAndPopulateAdditionalStaff(serviceType) {
            const url = `/services/api/additional_staff_options/?service_type=${serviceType}`;
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    this.populateAdditionalStaffDropdown(data.staff_options, `Select Additional ${serviceType} Staff`, serviceType);
                })
                .catch(error => console.error(`Error fetching additional staff options for ${serviceType}:`, error));
        },

        populateAdditionalStaffDropdown(options, defaultOptionText, serviceType) {
            const serviceTypeLower = serviceType.toLowerCase();
            const dropdownId = `id_${serviceTypeLower}_additional`;
            const savedStaffId = this[`saved${serviceType}AdditionalStaffId`];
            const dropdown = document.getElementById(dropdownId);

            let optionsHtml = `<option value="">${defaultOptionText}</option>`;
            options.forEach(option => {
                let isSelected = option.id.toString() === savedStaffId;
                optionsHtml += `<option value="${option.id}" data-price="${parseFloat(option.price).toFixed(2)}" data-hours="${option.hours}"${isSelected ? ' selected' : ''}>${option.name} - $${parseFloat(option.price).toFixed(2)} - ${option.hours} hours</option>`;
            });
            dropdown.innerHTML = optionsHtml;

            this.updatePriceAndHoursDisplay(dropdownId, `additional-${serviceTypeLower}-price`, `additional-${serviceTypeLower}-hours`, serviceType);
        },

        fetchAndPopulateEngagementSessions() {
            const url = `/services/api/engagement_session_options`;
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (Array.isArray(data.sessions)) {
                        this.populateEngagementSessionDropdown(data.sessions, 'Select an Engagement Session');
                    } else {
                        console.error('Error: Expected an array of sessions, but received:', data);
                    }
                })
                .catch(error => console.error('Error fetching engagement session options:', error));
        },

        populateEngagementSessionDropdown(sessions, defaultOptionText) {
            let optionsHtml = `<option value="">${defaultOptionText}</option>`;
            sessions.forEach(session => {
                let isSelected = session.id.toString() === this.savedEngagementSessionId;
                optionsHtml += `<option value="${session.id}" data-price="${parseFloat(session.price).toFixed(2)}"${isSelected ? ' selected' : ''}>${session.name} - $${parseFloat(session.price).toFixed(2)}</option>`;
            });
            const dropdown = document.getElementById('id_engagement_session');
            dropdown.innerHTML = optionsHtml;

            this.updatePriceAndHoursDisplay('id_engagement_session', 'engagement-session-price', null, 'Photography');
        },

        showOvertimeForm(entryId, serviceType) {
            const entryIdInput = document.getElementById(`${serviceType.toLowerCase()}OvertimeEntryId`);
            const optionSelect = document.getElementById(`${serviceType.toLowerCase()}OvertimeOptionSelect`);
            const hoursInput = document.getElementById(`${serviceType.toLowerCase()}OvertimeHours`);
            const form = document.getElementById(`${serviceType.toLowerCase()}OvertimeEntryForm`);

            if (entryIdInput && optionSelect && hoursInput && form) {
                entryIdInput.value = entryId || '';
                optionSelect.value = '';
                hoursInput.value = '';
                form.style.display = 'block';
            }
        },


        getCSRFToken() {
            const csrfTokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
            if (csrfTokenElement) {
                return csrfTokenElement.value;
            } else {
                console.error('CSRF token element not found');
                return null;
            }
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

            fetch(`/services/${contractId}/save_overtime_entry/`, {
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
                    this.clearFormFields(serviceType);
                    return this.fetchAndUpdateOvertimeEntries(contractId, serviceType);
                } else {
                    console.error('Error saving overtime entry:', data.message);
                }
            })
            .then(() => {
                this.updateTotalOvertimeCost(serviceType);
                this.updateTotalServiceCost(serviceType);
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
                entryIdInput.value = '';
            }
        },

        appendOvertimeEntry(entry, serviceType) {
            const displayId = serviceType.toLowerCase() + 'OvertimeEntriesDisplay';
            const display = document.getElementById(displayId);
            if (!display) {
                console.error(`Display element with ID ${displayId} not found.`);
                return;
            }

            let overtimeOptionDisplay = '';
            if (typeof entry.overtime_option === 'object' && entry.overtime_option.role) {
                overtimeOptionDisplay = entry.overtime_option.role;
            } else if (typeof entry.overtime_option === 'string') {
                overtimeOptionDisplay = entry.overtime_option;
            } else {
                overtimeOptionDisplay = 'Unknown Option';
            }

            const row = document.createElement('tr');
            row.setAttribute('data-id', entry.id);

            row.innerHTML = `
                <td>${overtimeOptionDisplay}</td>
                <td>${entry.hours} hours</td>
                <td>$${parseFloat(entry.cost).toFixed(2)}</td>
                <td><!-- Assigned Staff --></td>
                <td>
                    <button type="button" class="edit-overtime-button" data-id="${entry.id}" data-service="${serviceType}">Edit</button>
                    <button type="button" class="remove-overtime-button" data-id="${entry.id}" data-service="${serviceType}">Remove</button>
                </td>
            `;
            display.appendChild(row);
        },

        fetchAndPopulateOvertimeOptions(serviceType) {
            const url = `/services/api/overtime_options?service_type=${serviceType}`;
            fetch(url)
                .then(response => response.json())
                .then(overtimeOptions => {
                    const dropdownId = serviceType.toLowerCase() + 'OvertimeOptionSelect';
                    const savedOptionId = this['saved' + serviceType + 'OvertimeOptionId'];
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
            fetch(`/services/${contractId}/overtime_entries/?service_type=${serviceType}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        const displayId = serviceType.toLowerCase() + 'OvertimeEntriesDisplay';
                        const display = document.getElementById(displayId);
                        display.innerHTML = '';

                        data.entries.forEach(entry => {
                            this.appendOvertimeEntry(entry, serviceType);
                        });

                        this.updateTotalOvertimeCost(serviceType);
                        this.updateOvertimePriceDisplay(serviceType);
                        this.updateTotalServiceCost(serviceType);
                    } else {
                        console.error('Failed to fetch overtime entries:', data.message);
                    }
                })
                .catch(error => console.error('Error fetching overtime entries:', error));
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
            fetch(`/services/${entryId}/get_overtime_entry/`)
            .then(response => response.json())
            .then(data => {
                const entryFormId = serviceType.toLowerCase() + 'OvertimeEntryForm';
                const entryIdInputId = serviceType.toLowerCase() + 'OvertimeEntryId';
                const optionSelectId = serviceType.toLowerCase() + 'OvertimeOptionSelect';
                const hoursInputId = serviceType.toLowerCase() + 'OvertimeHours';

                document.getElementById(entryIdInputId).value = data.id;
                document.getElementById(optionSelectId).value = data.overtime_option_id;
                document.getElementById(hoursInputId).value = data.hours;
                document.getElementById(entryFormId).style.display = 'block';
            })
            .catch(error => console.error('Error:', error));

            this.updateOvertimePriceDisplay(serviceType);
            this.updateTotalOvertimeCost(serviceType);
            this.updateTotalServiceCost(serviceType);
        },

        removeOvertimeEntry(entryId, serviceType) {
            fetch(`/services/${entryId}/delete_overtime_entry/`, {
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
                    document.querySelector(`tr[data-id="${entryId}"]`).remove();
                    this.updateTotalOvertimeCost(serviceType);
                    this.updateTotalServiceCost(serviceType);
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

        saveSection(serviceType) {
            const contractId = this.getContractId();
            if (!contractId) {
                console.error("Contract ID is undefined.");
                return;
            }

            const serviceTypeLower = serviceType.toLowerCase();
            const formSelector = `#${serviceTypeLower} form`; // Dynamically target the form for the specific tab
            const formElement = document.querySelector(formSelector);

            if (!formElement) {
                console.error(`Form not found for ${serviceType} section.`);
                return;
            }

            const formData = new FormData(formElement);

            const csrfToken = this.getCSRFToken();
            formData.append('csrfmiddlewaretoken', csrfToken);

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
                    console.log(`${serviceType} section saved successfully`);
                    window.location.href = `/contracts/${contractId}/#services`;
                    window.location.reload();
                } else {
                    console.error(`Error saving ${serviceType} section:`, data.message);
                }
            })
            .catch(error => console.error('Error:', error));
        }

    };
    ServiceMgmt.init();
});
