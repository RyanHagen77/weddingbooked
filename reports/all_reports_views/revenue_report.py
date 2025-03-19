from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location
from payments.models import Payment

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import calendar
import logging

# Logging setup
logger = logging.getLogger(__name__)

@login_required
def revenue_report(request):
    today = datetime.today()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_location = request.GET.get('location', 'all')
    group_by = request.GET.get('group_by', 'month')  # Default to 'month'

    # Determine date range based on filter
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        if group_by == "week":
            start_date = today - timedelta(days=today.weekday())  # Start of the current week (Monday)
            end_date = start_date + timedelta(days=6)  # End of the week (Sunday)
        else:  # Default to 'month'
            start_date = today.replace(day=1)  # Start of the current month
            end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])  # End of the month

    # Filter contracts based on date range and location
    contracts = Contract.objects.filter(status="booked", contract_date__lte=end_date)
    if selected_location != 'all':
        contracts = contracts.filter(location_id=selected_location)

    # Fetch all payments within the selected range
    payments = Payment.objects.filter(
        date__gte=start_date,
        date__lte=end_date,
        contract__in=contracts
    ).select_related('contract__location')

    # Totals initialization
    total_deposits_received = Decimal('0.00')
    total_other_payments = Decimal('0.00')
    total_tax_collected = Decimal('0.00')

    report_data = []

    # If weekly view, break data into weeks
    if group_by == "week":
        current_week_start = start_date
        while current_week_start <= end_date:
            current_week_end = current_week_start + timedelta(days=6)

            week_payments = payments.filter(
                date__gte=current_week_start,
                date__lte=current_week_end
            )

            week_deposits = sum([p.amount for p in week_payments if p.payment_purpose and p.payment_purpose.name == 'Deposit'], Decimal('0.00'))
            week_other_payments = sum([p.amount for p in week_payments if not (p.payment_purpose and p.payment_purpose.name == 'Deposit')], Decimal('0.00'))
            week_tax_collected = sum([
                (Decimal(p.contract.location.tax_rate or 0) / Decimal('100.00') * sum(
                    Decimal(cp.quantity) * Decimal(cp.product.price) for cp in p.contract.contract_products.filter(added_on__lte=p.date) if cp.product.is_taxable
                )).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                for p in week_payments
            ], Decimal('0.00'))

            week_total_revenue = week_deposits + week_other_payments - week_tax_collected

            report_data.append({
                'period_start': current_week_start.strftime('%Y-%m-%d'),
                'period_end': current_week_end.strftime('%Y-%m-%d'),
                'deposits_received': week_deposits,
                'other_payments': week_other_payments,
                'tax_collected': week_tax_collected,
                'total_revenue': week_total_revenue,
            })

            current_week_start += timedelta(days=7)

    else:  # Monthly view (single row)
        for payment in payments:
            payment_taxable_amount = Decimal('0.00')

            relevant_products = payment.contract.contract_products.filter(added_on__lte=payment.date)
            for cp in relevant_products:
                if cp.product.is_taxable:
                    product_total = Decimal(cp.quantity) * Decimal(cp.product.price)
                    payment_taxable_amount += product_total

            tax_rate = Decimal(payment.contract.location.tax_rate or 0)
            tax_collected_for_payment = (payment_taxable_amount * tax_rate / Decimal('100.00')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            total_tax_collected += tax_collected_for_payment

            if payment.payment_purpose and payment.payment_purpose.name == 'Deposit':
                total_deposits_received += payment.amount
            else:
                total_other_payments += payment.amount

        total_revenue = total_deposits_received + total_other_payments - total_tax_collected

        report_data.append({
            'period_start': start_date.strftime('%Y-%m-%d'),
            'period_end': end_date.strftime('%Y-%m-%d'),
            'deposits_received': total_deposits_received.quantize(Decimal('0.01')),
            'other_payments': total_other_payments.quantize(Decimal('0.01')),
            'tax_collected': total_tax_collected.quantize(Decimal('0.01')),
            'total_revenue': total_revenue.quantize(Decimal('0.01')),
        })

    locations = Location.objects.all()

    context = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'selected_location': selected_location,
        'locations': locations,
        'report_data': report_data,
        'group_by': group_by,
    }

    return render(request, 'reports/revenue_report.html', context)
