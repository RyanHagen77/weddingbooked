class OvertimeManagement {
    constructor(serviceTypes) {
        this.serviceTypes = serviceTypes;
        this.overtimeOptions = {}; // Object to store overtime options by service type
        this.overtimeEntries = []; // Array to store overtime entries
    }

    init() {
        this.setupOvertimeManagement();
        this.setupFormSubmissionPrevention();
        this.setupAddOvertimeEntryButton();

        // Setup event listeners for forms
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            this.setupFormEventListeners(form);
        });
    }

    setupAddOvertimeEntryButton() {
        const addButton = document.getElementById('addOvertimeEntryButton');
        if (addButton) {
            addButton.addEventListener('click', () => this.addOvertimeEntry());
        }
    }

    addOvertimeEntry() {
        const container = document.getElementById('photographyOvertimeEntriesDisplay'); // Adjust if necessary for dynamic serviceType
        const totalFormsElement = document.querySelector('input[name$="TOTAL_FORMS"]');
        let totalForms = parseInt(totalFormsElement.value);
        let newFormIndex = totalForms;

        // Logic to clone the last form and update its index here...
        // This example assumes you have a way to clone or create a new form. Adjust accordingly.
        let newForm = this.createFormElement(newFormIndex); // Implement createFormElement to generate your new form HTML

        container.appendChild(newForm);
        totalFormsElement.value = totalForms + 1; // Increment the TOTAL_FORMS count
    }

    createFormElement(index) {
        // Create and return a new form DOM element with updated indices
        // This is a placeholder function. You need to implement it based on your form structure.
        let formElement = document.createElement('div');
        // Populate formElement with necessary fields, updating names and IDs to include the correct index
        return formElement;
    }

    fetchAndPopulateOvertimeOptions(serviceType) {
        const url = `/contracts/api/overtime_options?service_type=${serviceType}`;
        fetch(url)
            .then(response => response.json())
            .then(options => {
                // This block needs to be directly inside the .then()
                const selectElement = document.getElementById(`${serviceType.toLowerCase()}OvertimeOption`);
                let optionsHtml = '<option value="">Select Overtime Option</option>';
                options.forEach(({id, role, rate_per_hour, description}) => {
                    // Excluding 'type' from the option text
                    optionsHtml += `<option value="${id}" title="${description}">${role} - $${rate_per_hour}/hr</option>`;
                });
                selectElement.innerHTML = optionsHtml;
            })
            .catch(error => console.error('Error fetching overtime options:', error));
    }

    showOvertimeForm(serviceType) {
        // Check if the container for the form exists
        const formContainerId = `${serviceType.toLowerCase()}OvertimeEntriesDisplay`;
        const formContainer = document.getElementById(formContainerId);

        if (formContainer) {
            // Create a new form element
            const newForm = document.createElement('form');
            newForm.addEventListener('submit', event => {
                event.preventDefault(); // Prevent default form submission
                const form = event.target;
                this.saveOvertimeEntry(form); // Save the overtime entry
                this.showOvertimeForm(serviceType); // Create a new form after submission
            });

            // Add necessary HTML for the form
            newForm.innerHTML = `
                <select id="${serviceType.toLowerCase()}OvertimeOption" name="overtimeOption">
                    <!-- Options will be dynamically populated here -->
                </select>
                <label for="${serviceType.toLowerCase()}OvertimeHours">Hours:</label>
                <input type="number" id="${serviceType.toLowerCase()}OvertimeHours" name="overtimeHours" min="0" step="0.5">
                <button type="submit">Add Overtime</button>
            `;

            // Populate the select element with options
            const selectElement = newForm.querySelector(`#${serviceType.toLowerCase()}OvertimeOption`);
            this.populateOvertimeOptions(selectElement, serviceType);

            // Append the new form to the container
            formContainer.appendChild(newForm);
        } else {
            console.error(`Form container for ${serviceType} not found.`);
        }
    }

    setupFormSubmissionPrevention() {
        // Ensure that `this` is properly scoped within the forEach loop
        this.serviceTypes.forEach(serviceType => {
            document.querySelectorAll(`.${serviceType.toLowerCase()}-overtime-save`).forEach(button => {
                button.addEventListener('click', (event) => {
                    event.preventDefault(); // Stop the form from submitting traditionally
                    const form = button.closest('form');
                    this.saveOvertimeEntry(form); // Assuming saveOvertimeEntry handles AJAX or form processing
                    this.showOvertimeForm(serviceType); // Create a new form after submission
                });
            });
        });
    }

    // Dynamically adds a new overtime entry form

    populateOvertimeOptions(selectElement, serviceType) {
        // Assuming you have overtime options stored in this.overtimeOptions object
        const options = this.overtimeOptions[serviceType] || [];
        let optionsHtml = '<option value="">Select Overtime Option</option>';
        options.forEach(({id, role, rate_per_hour}) => {
            optionsHtml += `<option value="${id}">${role} - $${rate_per_hour}</option>`;
        });
        selectElement.innerHTML = optionsHtml;
    }

    setupFormEventListeners(formElement) {
        const submitButton = formElement.querySelector('button[type="submit"]');
        submitButton.addEventListener('click', (event) => {
            event.preventDefault(); // Prevent the default form submission that causes page refresh
            const serviceType = formElement.dataset.serviceType; // Assuming serviceType is stored in a data attribute
            this.saveOvertimeEntry(formElement, serviceType); // Call saveOvertimeEntry with serviceType when the button is clicked
        });
    }

    function; saveOvertimeEntry(entryElement) {
        console.log('Entry element:', entryElement);

        const selectedOption = entryElement.querySelector('select[name="overtimeOption"]');
        const hoursInput = entryElement.querySelector('input[name="overtimeHours"]');

        console.log('Selected option:', selectedOption);
        console.log('Hours input:', hoursInput);

        // If either the selected option or hours input field is not found, log an error and return
        if (!selectedOption) {
            console.error('Selected option not found.');
            return;
        }

        if (!hoursInput) {
            console.error('Hours input field not found.');
            return;
        }

        // Get the value and text of the selected option
        const optionText = selectedOption.options[selectedOption.selectedIndex].text;
        const optionValue = selectedOption.value;

        // Get the hours entered by the user
        const hours = hoursInput.value;

        // If both the selected option and hours input field are empty, log a warning and return
        if (!optionValue && !hours) {
            console.warn('Empty overtime entry. No action taken.');
            return;
        }

        // If the selected option is empty but hours are provided, log a warning
        if (!optionValue && hours) {
            console.warn('Selected option is empty but hours are provided.');
        }

        // Proceed with saving the non-empty overtime entry
        const overtimeEntry = {
            optionText: optionText,
            optionValue: optionValue,
            hours: parseFloat(hours) // Convert hours to a float (assuming it represents a numerical value)
        };

        // Log the overtime entry to the console for testing
        console.log('Overtime entry:', overtimeEntry);

        // Save the overtime entry to a data structure (e.g., an array)
        this.saveOvertimeData(overtimeEntry);

        // Display the saved entry
        this.displayOvertimeEntry(overtimeEntry);

        // Reset the form fields
        selectedOption.selectedIndex = 0;
        hoursInput.value = '';
    }


    // Function to save the overtime entry data to a data structure
    saveOvertimeData(entry) {
        // Store the overtime entry in an array (you can use another data structure if needed)
        this.overtimeEntries.push(entry);
    }

    // Function to display the overtime entry in the DOM
    displayOvertimeEntry(entry) {
        const displayContainer = document.getElementById('photographyOvertimeEntriesDisplay');
        const entryDisplay = document.createElement('div');
        entryDisplay.textContent = `${entry.optionText}, Hours: ${entry.hours}`;
        const removeButton = document.createElement('button');
        removeButton.textContent = 'Remove';
        removeButton.onclick = () => {
            // Remove the entry from the display and from the data structure
            entryDisplay.remove();
            this.removeOvertimeData(entry);
        };
        entryDisplay.appendChild(removeButton);
        displayContainer.appendChild(entryDisplay);

        // Update total overtime cost display whenever a new entry is displayed
        this.updateTotalOvertimeCostDisplay();
    }



    // Function to calculate total overtime cost and update the corresponding HTML element
    calculateTotalOvertimeCost() {
        const overtimeEntries = document.querySelectorAll('#photographyOvertimeEntriesDisplay select[name="overtimeOption"]');
        console.log('Overtime entries:', overtimeEntries);
        let totalCost = 0;
        overtimeEntries.forEach(selectElement => {
            // Get the selected option within the <select> element
            const selectedOption = selectElement.querySelector('option:checked');
            if (selectedOption) {
                // Log the selected option's value to check if it's correctly parsed
                console.log('Selected option value:', selectedOption.value);

                // Get the value of the selected option and parse it as a float
                const cost = parseFloat(selectedOption.value);
                if (!isNaN(cost)) {
                    totalCost += cost;
                }
            }
        });
        console.log('Total cost:', totalCost);
        return totalCost.toFixed(2);
    }


    // Function to update the HTML element with the total overtime cost
    updateTotalOvertimeCostDisplay() {
        const totalCost = this.calculateTotalOvertimeCost();
        const totalCostElement = document.querySelector('#totalOvertimeCost');
        if (totalCostElement) {
            totalCostElement.textContent = `$${totalCost}`;
        }
    }

    // Function to remove the overtime entry data from the data structure
    removeOvertimeData(entry) {
        const index = this.overtimeEntries.indexOf(entry);
        if (index !== -1) {
            this.overtimeEntries.splice(index, 1);
        }

        // Update total overtime cost display whenever an entry is removed
        this.updateTotalOvertimeCostDisplay();
    }
    // Other functions within the class...

}

// Create an instance of OvertimeManagement and initialize it
document.addEventListener('DOMContentLoaded', () => {
    const overtimeManager = new OvertimeManagement(['Photography', 'Videography', 'DJ', 'Photobooth']);
        overtimeManager.init();

        // Example: Show the overtime form for Photography
        overtimeManager.showOvertimeForm('Photography');


        // Setup form submission prevention for overtime entries
        overtimeManager.setupFormSubmissionPrevention();

        // Setup event listeners for saving overtime entries using form submission
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            overtimeManager.setupFormEventListeners(form);
        });
});