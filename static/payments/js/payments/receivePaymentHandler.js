// receivePaymentHandler.js

import { receivePayment, confirmPayment, updateContractSummary } from "./receivingPayments.js";

export function initializeReceivePaymentHandler() {
  // Ensure global contractData exists.
  window.contractData = window.contractData || {};

  // Update contractData.paymentScheduleId from a data attribute on <body>.
  const paymentScheduleId = document.body.getAttribute('data-payment-schedule-id');
  if (paymentScheduleId) {
    window.contractData.paymentScheduleId = paymentScheduleId;
  } else {
    console.warn("Payment schedule ID not found in the body data attribute.");
  }

  // Attach an event listener to the Receive Payment button.
  const receivePaymentBtn = document.getElementById('receive-payment-button');
  if (receivePaymentBtn) {
    receivePaymentBtn.addEventListener('click', () => {
      receivePayment();
    });
  } else {
    console.warn("Receive Payment button not found.");
  }

  // Attach listener for the "Confirm Payment" button.
  const confirmPaymentBtn = document.getElementById('confirm-payment-button');
  if (confirmPaymentBtn) {
    confirmPaymentBtn.addEventListener('click', () => {
      confirmPayment();
    });
  } else {
    console.warn("Confirm Payment button not found.");
  }
}
