
from datetime import timedelta
from django.utils.timezone import now
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from decimal import Decimal, ROUND_HALF_UP
from .forms import PaymentForm, PaymentScheduleForm, SchedulePaymentFormSet
from .models import Payment, PaymentPurpose, PaymentSchedule, SchedulePayment
from contracts.models import ChangeLog
from contracts.models import Contract
from django.urls import reverse
from django.db.models import Sum


def add_schedule_a(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    if not hasattr(contract, 'payment_schedule'):
        contract.schedule = create_schedule_a_payments(contract_id)
        contract.status = 'booked'  # Optionally update contract status
        contract.save()
    return redirect(request,'contract_detail', id=contract_id) + '#payments'

def create_schedule_a_payments(contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule, created = PaymentSchedule.objects.get_or_create(contract=contract, defaults={'schedule_type': 'schedule_a'})

    # Clear existing Schedule A payments
    SchedulePayment.objects.filter(schedule=schedule).delete()

    # Change the purpose name from 'Down Payment' to 'Deposit'
    deposit_purpose, _ = PaymentPurpose.objects.get_or_create(name='Deposit')
    balance_payment_purpose, _ = PaymentPurpose.objects.get_or_create(name='Balance Payment')

    # Calculate the deposit amount (50% of the total contract cost, rounded up to the nearest 100)
    raw_deposit_amount = contract.final_total * Decimal('0.50')
    deposit_amount = (raw_deposit_amount / Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * Decimal('100')

    # Calculate the balance due date (60 days before the event date)
    balance_due_date = contract.event_date - timedelta(days=60)

    # Create the deposit payment with a note indicating its due upon booking
    SchedulePayment.objects.create(
        schedule=schedule,
        purpose=deposit_purpose,
        due_date=now(),  # Use the current date
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

def check_payment_schedule_for_contract(contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    try:
        payment_schedule = contract.payment_schedule
        print(f'Payment schedule ID for contract {contract_id} is {payment_schedule.id}')
    except PaymentSchedule.DoesNotExist:
        print(f'No payment schedule exists for contract {contract_id}')

@login_required
def create_or_update_schedule(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule, created = PaymentSchedule.objects.get_or_create(contract=contract)

    if request.method == 'POST':
        schedule_form = PaymentScheduleForm(request.POST, instance=schedule)
        schedule_payment_formset = SchedulePaymentFormSet(request.POST, instance=schedule)

        if schedule_form.is_valid() and schedule_payment_formset.is_valid():
            saved_schedule = schedule_form.save(commit=False)
            saved_schedule.schedule_type = request.POST.get('schedule_type', 'schedule_a')
            saved_schedule.save()
            schedule_payment_formset.save()

            # Create or update service fees in the custom schedule
            service_fees = request.POST.getlist('service_fees')
            if service_fees:
                for fee in service_fees:
                    fee_data = fee.split(',')
                    fee_purpose, _ = PaymentPurpose.objects.get_or_create(name=fee_data[0])
                    SchedulePayment.objects.create(
                        schedule=schedule,
                        purpose=fee_purpose,
                        due_date=contract.event_date,
                        amount=Decimal(fee_data[1])
                    )

            return HttpResponseRedirect(reverse('contracts:contract_detail', kwargs={'id': contract_id}) + '#financial')

    else:
        schedule_form = PaymentScheduleForm(instance=schedule)
        schedule_payment_formset = SchedulePaymentFormSet(instance=schedule)

    return render(request, 'contracts/schedule_form.html', {
        'contract': contract,
        'schedule_form': schedule_form,
        'schedule_payment_formset': schedule_payment_formset,
    })



def get_schedule_payments_due(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule = contract.payment_schedule

    if not schedule:
        return JsonResponse({'next_payment_amount': '0.00', 'next_payment_due_date': 'N/A'})

    if schedule.schedule_type == 'schedule_a':
        next_payment_due_date = contract.event_date - timedelta(days=60)
        next_payment_amount = contract.balance_due
    else:
        schedule_payments = schedule.schedule_payments.filter(paid=False).order_by('due_date')
        if schedule_payments.exists():
            next_payment = schedule_payments.first()
            next_payment_due_date = next_payment.due_date
            next_payment_amount = next_payment.amount
        else:
            next_payment_due_date = 'N/A'
            next_payment_amount = '0.00'

    payment_details = {
        'next_payment_amount': str(next_payment_amount),
        'next_payment_due_date': next_payment_due_date.strftime('%Y-%m-%d') if next_payment_due_date != 'N/A' else 'N/A'
    }

    return JsonResponse(payment_details)


def get_custom_schedule(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule = contract.payment_schedule
    if schedule.schedule_type == 'custom':
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

            return JsonResponse({'success': True, 'payment_id': payment.id})
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
                    contract=payment.contract  # Pass the associated contract
                )

            # Update payment status after editing the payment
            update_payment_status(payment.contract.payment_schedule)

            return JsonResponse({'success': True, 'payment_id': payment.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'GET request not allowed'}, status=405)


@login_required
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    contract = payment.contract  # Get the contract directly

    # Log the payment deletion
    ChangeLog.objects.create(
        user=request.user,
        description=f"Deleted payment of {payment.amount} for payment ID {payment.id}",
        contract=contract  # Ensure the contract is associated with the log
    )

    payment.delete()

    # Update payment status after deletion
    if contract.payment_schedule:
        update_payment_status(contract.payment_schedule)

    return redirect('contracts:contract_detail', id=contract.contract_id)  # Make sure to use `id` or `pk`

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