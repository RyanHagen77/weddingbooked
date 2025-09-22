from datetime import timedelta
from django.utils.timezone import now
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from decimal import Decimal, ROUND_HALF_UP
from .forms import PaymentForm, PaymentScheduleForm, SchedulePaymentFormSet
from .models import Payment, PaymentPurpose, PaymentSchedule, SchedulePayment, PaymentLink
from contracts.models import ChangeLog, Contract
from django.db.models import Sum
import json

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
try:
    # if you use SimpleJWT
    from rest_framework_simplejwt.authentication import JWTAuthentication
    AUTH_CLASSES = [JWTAuthentication, SessionAuthentication]
except Exception:
    # fallback: if you use DRF TokenAuth instead of JWT, swap this to TokenAuthentication
    from rest_framework.authentication import TokenAuthentication
    AUTH_CLASSES = [TokenAuthentication, SessionAuthentication]


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
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule, _ = PaymentSchedule.objects.get_or_create(contract=contract)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'GET request not allowed'}, status=405)

    schedule_form = PaymentScheduleForm(request.POST, instance=schedule)
    schedule_payment_formset = SchedulePaymentFormSet(request.POST, instance=schedule)

    if not (schedule_form.is_valid() and schedule_payment_formset.is_valid()):
        errors = {**schedule_form.errors, **schedule_payment_formset.errors}
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    # what the user selected
    new_type = schedule_form.cleaned_data.get('schedule_type', schedule.schedule_type or 'schedule_a')
    # only rebuild if explicitly requested
    recalc_flag = (request.POST.get('recalculate', 'false').lower() == 'true')
    # always rebuild if type changed
    type_changed = (schedule.schedule_type != new_type)
    if type_changed:
        recalc_flag = True

    if recalc_flag:
        if new_type == 'schedule_a':
            schedule = create_schedule_a_payments(contract_id)
        elif new_type == 'custom':
            schedule = create_custom_schedule_payments(contract_id)
        # (add other types here if you introduce them)
    else:
        # just persist edits to existing schedule payments; links stay attached
        schedule_payment_formset.save()

    schedule.schedule_type = new_type
    schedule.save()

    return JsonResponse({'success': True, 'schedule_type': schedule.schedule_type})


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

@login_required
@require_http_methods(["GET"])
def payment_links_for_payment(request, schedule_payment_id):
    sp = get_object_or_404(SchedulePayment, id=schedule_payment_id)
    links = [
        {
            "id": l.id,
            "label": l.label,
            "url": l.url,
            "active": l.active,
            "created_at": l.created_at.isoformat(),
        }
        for l in sp.payment_links.order_by('-created_at')
    ]
    return JsonResponse(links, safe=False)


@login_required
@require_http_methods(["POST"])
def create_payment_link(request, schedule_payment_id):
    sp = get_object_or_404(SchedulePayment, id=schedule_payment_id)
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    url = (data.get("url") or "").strip()
    if not url:
        return JsonResponse({"detail": "URL is required"}, status=400)

    link = PaymentLink.objects.create(
        payment=sp,
        label=(data.get("label") or "").strip(),
        url=url,
        active=bool(data.get("active", True)),
    )
    return JsonResponse(
        {
            "id": link.id,
            "label": link.label,
            "url": link.url,
            "active": link.active,
            "created_at": link.created_at.isoformat(),
        },
        status=201,
    )


@login_required
@require_http_methods(["PATCH", "POST"])  # allow POST if PATCH is awkward in some environments
def update_payment_link(request, link_id):
    link = get_object_or_404(PaymentLink, id=link_id)
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    if "label" in data:
        link.label = (data.get("label") or "").strip()
    if "url" in data:
        new_url = (data.get("url") or "").strip()
        if not new_url:
            return JsonResponse({"detail": "URL cannot be empty"}, status=400)
        link.url = new_url
    if "active" in data:
        link.active = bool(data.get("active"))

    link.save()
    return JsonResponse(
        {
            "id": link.id,
            "label": link.label,
            "url": link.url,
            "active": link.active,
            "created_at": link.created_at.isoformat(),
        }
    )


@login_required
@require_http_methods(["DELETE", "POST"])  # allow POST for easier HTML-only calls
def delete_payment_link(request, link_id):
    link = get_object_or_404(PaymentLink, id=link_id)
    link.delete()
    # 204 with an empty body – browsers sometimes dislike empty JSON, so OK with empty response
    return JsonResponse({}, status=204)


@api_view(['GET'])
@authentication_classes(AUTH_CLASSES)
@permission_classes([IsAuthenticated])
def next_due_payment_link(request, contract_id):
    # identical logic, just return DRF Response instead of JsonResponse
    from django.shortcuts import get_object_or_404
    from .models import PaymentLink, SchedulePayment
    from contracts.models import Contract

    contract = get_object_or_404(Contract, contract_id=contract_id)
    sched = getattr(contract, 'payment_schedule', None)
    if not sched:
        return Response({"url": None})

    sp = sched.schedule_payments.filter(paid=False).order_by('due_date', 'id').first()
    if not sp:
        return Response({"url": None})

    link = sp.payment_links.filter(active=True).order_by('-created_at').first()
    if not link:
        return Response({"url": None})

    return Response({
        "url": link.url,
        "amount": str(sp.amount),
        "due_date": sp.due_date.isoformat(),
        "label": link.label or (sp.purpose.name if sp.purpose else "Payment"),
    })