// paymentScheduleHandlers.js
import { handleScheduleChange } from "./paymentScheduleManager.js";
window.handleScheduleChange = handleScheduleChange;

// paymentScheduleHandlers.js
import { initializeScheduleEvents } from "./paymentScheduleEvents.js";

document.addEventListener("DOMContentLoaded", () => {
    initializeScheduleEvents();
});
