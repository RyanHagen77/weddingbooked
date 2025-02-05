// formsetUtils.js
export function addPaymentScheduleFormsetEntry(containerId, totalFormsId, formClass) {
    const container = document.getElementById(containerId);
    const totalForms = document.getElementById(totalFormsId);
    let emptyTemplateSelector = '';

    // Decide which empty template to use based on the formClass parameter.
    if (formClass === '.schedule-payment-form') {
        emptyTemplateSelector = '.empty-schedule-payment-form';
    } else {
        console.error("Unknown form class:", formClass);
        return;
    }

    const emptyFormTemplate = document.querySelector(emptyTemplateSelector).cloneNode(true);

    emptyFormTemplate.style.display = '';
    emptyFormTemplate.classList.remove(emptyTemplateSelector.substring(1)); // remove leading dot

    const formIndex = parseInt(totalForms.value);
    emptyFormTemplate.innerHTML = emptyFormTemplate.innerHTML.replace(/__prefix__/g, formIndex);

    container.appendChild(emptyFormTemplate);
    totalForms.value = formIndex + 1;
}
