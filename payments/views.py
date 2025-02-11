from datetime import timedelta
from django.utils.timezone import now
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from decimal import Decimal, ROUND_HALF_UP
from .forms import PaymentForm, PaymentScheduleForm, SchedulePaymentFormSet
from .models import Payment, PaymentPurpose, PaymentSchedule, SchedulePayment
from contracts.models import ChangeLog, Contract
from django.urls import reverse
from django.db.models import Sum

import logging
# Logging setup
logger = logging.getLogger(__name__)

def create_schedule_a_payments(contract_id):
    """
    Creates a 'Schedule A' payment schedule for a contract.
    This includes:
      - A deposit payment (50% of the contract total, rounded up to the nearest 100).
      - A balance payment (remaining amount due 60 days before the event date).
    """
    contract = get_object_or_404(Contract, contract_id=contract_id)

    # Get or create the PaymentSchedule with schedule_type 'schedule_a'
    schedule, created = PaymentSchedule.objects.get_or_create(
        contract=contract,
        defaults={'schedule_type': 'schedule_a'}
    )

    # Remove any existing payments
    SchedulePayment.objects.filter(schedule=schedule).delete()

    # Retrieve (or create) the payment purposes
    deposit_purpose, _ = PaymentPurpose.objects.get_or_create(name='Deposit')
    balance_payment_purpose, _ = PaymentPurpose.objects.get_or_create(name='Balance Payment')

    # Calculate deposit amount: 50% of total cost, rounded up to the nearest 100
    raw_deposit_amount = contract.final_total * Decimal('0.50')
    deposit_amount = (
        (raw_deposit_amount / Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        * Decimal('100')
    )

    # Set due dates
    balance_due_date = contract.event_date - timedelta(days=60)

    # Create the deposit payment (due immediately)
    SchedulePayment.objects.create(
        schedule=schedule,
        purpose=deposit_purpose,
        due_date=now().date(),
        amount=deposit_amount,
        paid=contract.amount_paid >= deposit_amount
    )

    # Create the balance payment
    balance_amount = contract.final_total - deposit_amount
    SchedulePayment.objects.create(
        schedule=schedule,
        purpose=balance_payment_purpose,
        due_date=balance_due_date,
        amount=balance_amount,
        paid=contract.amount_paid >= contract.final_total
    )

    return schedule


def create_custom_schedule_payments(contract_id):
    """
    Creates a 'Custom' payment schedule for a contract that uses the sum of the deposit amounts
    from service packages, additional options, staff bookings, and formalwear rentals.
    """
    contract = get_object_or_404(Contract, contract_id=contract_id)

    # Get or create the PaymentSchedule with schedule_type 'custom'
    schedule, created = PaymentSchedule.objects.get_or_create(
        contract=contract,
        defaults={'schedule_type': 'custom'}
    )
    if schedule.schedule_type != 'custom':
        schedule.schedule_type = 'custom'
        schedule.save()

    # Force re-creation of payments
    schedule.schedule_payments.all().delete()

    deposit_total = Decimal('0.00')

    # Sum deposits from individual service package fields
    if contract.photography_package:
        deposit_total += contract.photography_package.deposit
    if contract.videography_package:
        deposit_total += contract.videography_package.deposit
    if contract.dj_package:
        deposit_total += contract.dj_package.deposit
    if contract.photobooth_package:
        deposit_total += contract.photobooth_package.deposit

    # Include additional option deposits if applicable
    if contract.photography_additional:
        deposit_total += contract.photography_additional.deposit
    if contract.videography_additional:
        deposit_total += contract.videography_additional.deposit
    if contract.dj_additional:
        deposit_total += contract.dj_additional.deposit
    if contract.photobooth_additional:
        deposit_total += contract.photobooth_additional.deposit

    # Include formalwear deposits (deposit amount multiplied by quantity)
    for cf in contract.formalwear_contracts.all():
        deposit_total += cf.formalwear_product.deposit_amount * cf.quantity

    # Include staff booking deposits (if your Contract has a related manager 'staff_bookings')
    if hasattr(contract, 'staff_bookings'):
        for sb in contract.staff_bookings.all():
            deposit_total += sb.deposit  # Ensure that the StaffBooking model has a deposit attribute

    # Retrieve or create payment purposes
    deposit_purpose, _ = PaymentPurpose.objects.get_or_create(name='Deposit')
    balance_payment_purpose, _ = PaymentPurpose.objects.get_or_create(name='Balance Payment')

    # Create the deposit payment (due immediately)
    SchedulePayment.objects.create(
        schedule=schedule,
        purpose=deposit_purpose,
        due_date=now().date(),  # Payment due upon booking
        amount=deposit_total,
        paid=contract.amount_paid >= deposit_total
    )

    # Create the balance payment (due 60 days before the event)
    balance_amount = contract.final_total - deposit_total
    balance_due_date = contract.event_date - timedelta(days=60)
    SchedulePayment.objects.create(
        schedule=schedule,
        purpose=balance_payment_purpose,
        due_date=balance_due_date,
        amount=balance_amount,
        paid=contract.amount_paid >= contract.final_total
    )

    return schedule


@login_required
def create_or_update_schedule(request, contract_id):
    """
    AJAX view to create or update a payment schedule for a contract.

    - For "schedule_a": Uses fixed logic.
    - For "custom":
       - If the user requests recalculation (or if no schedule payments exist), the default deposit-based schedule is created.
       - Otherwise, custom changes made via the formset are saved.

    This view always updates the PaymentSchedule.schedule_type based on the modal dropdown selection.
    """
    contract = get_object_or_404(Contract, contract_id=contract_id)
    # Get or create the existing schedule
    schedule, created = PaymentSchedule.objects.get_or_create(contract=contract)

    if request.method == 'POST':
        schedule_form = PaymentScheduleForm(request.POST, instance=schedule)
        schedule_payment_formset = SchedulePaymentFormSet(request.POST, instance=schedule)

        if schedule_form.is_valid() and schedule_payment_formset.is_valid():
            # Retrieve the chosen schedule type from the cleaned form data.
            new_schedule_type = schedule_form.cleaned_data.get('schedule_type', 'schedule_a')

            # Delegate based on the new schedule type:
            if new_schedule_type == 'schedule_a':
                schedule = create_schedule_a_payments(contract_id)
            elif new_schedule_type == 'custom':
                # Check for a recalculation flag from the form (e.g., a hidden input named "recalculate")
                recalc_flag = request.POST.get('recalculate', 'true').lower() == 'true'
                if recalc_flag or not schedule.schedule_payments.exists():
                    schedule = create_custom_schedule_payments(contract_id)
                else:
                    # Save the custom changes from the formset without recalculation.
                    schedule_payment_formset.save()
            else:
                # If other schedule types are supported, update them directly.
                schedule_payment_formset.save()

            # *** Force update the schedule type based on the modal dropdown ***
            # This ensures that even if helper functions override some values, the dropdown selection is preserved.
            schedule.schedule_type = new_schedule_type
            schedule.save()

            return JsonResponse({
                'success': True,
                'schedule_type': schedule.schedule_type
            })
        else:
            errors = {**schedule_form.errors, **schedule_payment_formset.errors}
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
    else:
        return JsonResponse({
            'success': False,
            'message': 'GET request not allowed'
        }, status=405)


def get_schedule_payments_due(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule = getattr(contract, 'payment_schedule', None)

    # If no schedule exists, return a default value.
    if not schedule:
        return JsonResponse({'next_payment_amount': '0.00', 'next_payment_due_date': 'N/A'})

    # For Schedule A, assume the next payment is the balance due on event_date - 60 days.
    if schedule.schedule_type == 'schedule_a':
        next_payment_due_date = contract.event_date - timedelta(days=60)
        next_payment_amount = contract.balance_due

    # For Schedule B or custom schedules, look for the next unpaid payment.
    elif schedule.schedule_type in ['schedule_b', 'custom']:
        schedule_payments = schedule.schedule_payments.filter(paid=False).order_by('due_date')
        if schedule_payments.exists():
            next_payment = schedule_payments.first()
            next_payment_due_date = next_payment.due_date
            next_payment_amount = next_payment.amount
        else:
            next_payment_due_date = 'N/A'
            next_payment_amount = '0.00'
    else:
        next_payment_due_date = 'N/A'
        next_payment_amount = '0.00'

    # Prepare and return the JSON response.
    payment_details = {
        'next_payment_amount': str(next_payment_amount),
        'next_payment_due_date': (
            next_payment_due_date.strftime('%Y-%m-%d')
            if next_payment_due_date != 'N/A'
            else 'N/A'
        )
    }

    return JsonResponse(payment_details)


def get_custom_schedule(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule = contract.payment_schedule
    if schedule.schedule_type in ['custom', 'schedule_b']:
        schedule_payments = schedule.schedule_payments.all()
        data = [
            {
                'purpose': payment.purpose.name if payment.purpose else '',
                'due_date': payment.due_date.strftime('%Y-%m-%d'),
                'amount': str(payment.amount),
                'paid': payment.paid
            }
            for payment in schedule_payments
        ]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


@login_required
def add_payment(request, schedule_id):
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    contract = schedule.contract  # Get the associated contract

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.contract = contract  # Set the contract for the payment
            payment.save()

            # Update payment status
            update_payment_status(schedule)

            # Return JSON with update_schedule flag
            return JsonResponse({
                'success': True,
                'payment_id': payment.id,
                'update_schedule': True
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'GET request not allowed'}, status=405)


def update_payment_status(schedule):
    total_payments_made = Payment.objects.filter(contract=schedule.contract).aggregate(Sum('amount'))['amount__sum'] or 0

    for payment in schedule.schedule_payments.all():
        if total_payments_made >= payment.amount:
            payment.paid = True
            total_payments_made -= payment.amount
        else:
            payment.paid = False
        payment.save()


@login_required
def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    original_amount = payment.amount  # Capture the original amount for logging

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.modified_by_user = request.user
            payment.save()  # Save the payment

            # Log changes if the amount is updated
            if original_amount != payment.amount:
                ChangeLog.objects.create(
                    user=request.user,
                    description=f"Payment updated from {original_amount} to {payment.amount} for payment ID {payment.id}",
                    contract=payment.contract
                )

            # Update payment status after editing the payment
            schedule = payment.contract.payment_schedule  # Adjust as needed.
            update_payment_status(schedule)

            # Return JSON with update_schedule flag
            return JsonResponse({
                'success': True,
                'payment_id': payment.id,
                'update_schedule': True
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'GET request not allowed'}, status=405)


@login_required
def delete_payment(request, payment_id):
    if request.method == 'POST':  # Only allow POST for deletion.
        payment = get_object_or_404(Payment, id=payment_id)
        contract = payment.contract  # Get the contract directly

        # Log the payment deletion
        ChangeLog.objects.create(
            user=request.user,
            description=f"Deleted payment of {payment.amount} for payment ID {payment.id}",
            contract=contract
        )

        payment.delete()

        # Update payment status after deletion
        if contract.payment_schedule:
            update_payment_status(contract.payment_schedule)

        # Return JSON with update_schedule flag
        return JsonResponse({
            'success': True,
            'payment_id': payment_id,
            'update_schedule': True
        })
    else:
        return JsonResponse({'success': False, 'message': 'GET request not allowed'}, status=405)


@login_required
def get_existing_payments(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    payments = contract.payments.all()  # Related name 'payments'
    data = [
        {
            'id': payment.id,
            'date': payment.date.isoformat(),  # Ensure the date is in ISO format
            'amount': float(payment.amount),  # Convert amount to float
            'method': payment.payment_method,  # Correct field name
            'purpose': payment.payment_purpose.name if payment.payment_purpose else '',  # Get purpose name
            'reference': payment.payment_reference if payment.payment_reference else '',
            'memo': payment.memo if payment.memo else '',
        }
        for payment in payments
    ]
    return JsonResponse(data, safe=False)