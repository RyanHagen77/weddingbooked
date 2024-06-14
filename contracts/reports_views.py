from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import Contract, LeadSourceCategory, Location, Payment, ServiceFee, ContractOvertime, SchedulePayment
from django.db.models import Sum, F
from decimal import Decimal
from datetime import datetime, timedelta, date
from django.utils.dateparse import parse_date
import calendar
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def reports(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    context = {
        'logo_url': logo_url,
        'reports': [

            # Add more reports as needed
        ],
    }

    return render(request, 'contracts/reports.html', context)

@login_required
def lead_source_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Get date range, location, and period from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    location_id = request.GET.get('location', 'all')
    period = request.GET.get('period', 'monthly')

    # Default date range to current month if not provided
    today = datetime.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    if not start_date_str:
        start_date = first_day_of_month
        start_date_str = start_date.strftime('%Y-%m-%d')
    else:
        start_date = parse_date(start_date_str)

    if not end_date_str:
        end_date = last_day_of_month
        end_date_str = end_date.strftime('%Y-%m-%d')
    else:
        end_date = parse_date(end_date_str)

    # Filter contracts based on location
    if location_id == 'all':
        contracts = Contract.objects.filter(event_date__range=(start_date, end_date))
    else:
        contracts = Contract.objects.filter(event_date__range=(start_date, end_date), location_id=location_id)

    # Function to generate a list of months in the date range
    def month_range(start_date, end_date):
        start_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        current_month = start_month
        while current_month <= end_month:
            yield current_month
            next_month = current_month + timedelta(days=calendar.monthrange(current_month.year, current_month.month)[1])
            current_month = next_month.replace(day=1)

    # Function to generate a list of weeks in the date range
    def week_range(start_date, end_date):
        start_week = start_date - timedelta(days=start_date.weekday())
        end_week = end_date - timedelta(days=end_date.weekday())
        current_week = start_week
        while current_week <= end_week:
            yield current_week
            current_week += timedelta(days=7)

    # Gather statistics based on the selected period
    report_data = []
    if period == 'monthly':
        for month_start in month_range(start_date, end_date):
            month_end = month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1])
            month_contracts = contracts.filter(event_date__range=(month_start, month_end))

            for category in LeadSourceCategory.objects.all():
                total_count = month_contracts.filter(lead_source_category=category).count()
                booked_count = month_contracts.filter(lead_source_category=category, status='booked').count()
                report_data.append({
                    'period': month_start.strftime('%b %Y'),
                    'category': category.name,
                    'total_count': total_count,
                    'booked_count': booked_count,
                })
    elif period == 'weekly':
        for week_start in week_range(start_date, end_date):
            week_end = week_start + timedelta(days=6)
            week_contracts = contracts.filter(event_date__range=(week_start, week_end))

            for category in LeadSourceCategory.objects.all():
                total_count = week_contracts.filter(lead_source_category=category).count()
                booked_count = week_contracts.filter(lead_source_category=category, status='booked').count()
                report_data.append({
                    'period': f"{week_start.strftime('%b %d, %Y')} - {week_end.strftime('%b %d, %Y')}",
                    'category': category.name,
                    'total_count': total_count,
                    'booked_count': booked_count,
                })

    # Get all locations for the dropdown
    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'report_data': report_data,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'locations': locations,
        'selected_location': location_id,
        'selected_period': period,
    }

    return render(request, 'contracts/lead_source_report.html', context)

@login_required
def appointments_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Get date range, location, and period from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    location_id = request.GET.get('location', 'all')
    period = request.GET.get('period', 'monthly')

    # Default date range to current month if not provided
    today = datetime.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    if not start_date_str:
        start_date = first_day_of_month
        start_date_str = start_date.strftime('%Y-%m-%d')
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

    if not end_date_str:
        end_date = last_day_of_month
        end_date_str = end_date.strftime('%Y-%m-%d')
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    # Filter contracts based on location
    if location_id == 'all':
        contracts = Contract.objects.filter(contract_date__range=(start_date, end_date))
    else:
        contracts = Contract.objects.filter(contract_date__range=(start_date, end_date), location_id=location_id)

    # Function to generate a list of months in the date range
    def month_range(start_date, end_date):
        start_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        current_month = start_month
        while current_month <= end_month:
            yield current_month
            next_month = current_month + timedelta(days=calendar.monthrange(current_month.year, current_month.month)[1])
            current_month = next_month.replace(day=1)

    # Function to generate a list of weeks in the date range
    def week_range(start_date, end_date):
        start_week = start_date - timedelta(days=start_date.weekday())
        end_week = end_date - timedelta(days=end_date.weekday())
        current_week = start_week
        while current_week <= end_week:
            yield current_week
            current_week += timedelta(days=7)

    # Gather statistics based on the selected period
    report_data = []
    if period == 'monthly':
        for month_start in month_range(start_date, end_date):
            month_end = month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1])
            month_contracts = contracts.filter(contract_date__range=(month_start, month_end))

            photo_count = month_contracts.filter(photography_package__isnull=False).count()
            photo_booked_count = month_contracts.filter(photography_package__isnull=False, status='booked').count()
            video_count = month_contracts.filter(videography_package__isnull=False).count()
            video_booked_count = month_contracts.filter(videography_package__isnull=False, status='booked').count()
            dj_count = month_contracts.filter(dj_package__isnull=False).count()
            dj_booked_count = month_contracts.filter(dj_package__isnull=False, status='booked').count()
            photobooth_count = month_contracts.filter(photobooth_package__isnull=False).count()
            photobooth_booked_count = month_contracts.filter(photobooth_package__isnull=False, status='booked').count()
            total_appointments = month_contracts.count()

            report_data.append({
                'logo_url': logo_url,
                'period': month_start.strftime('%b %Y'),
                'photo_count': photo_count,
                'photo_booked_count': photo_booked_count,
                'video_count': video_count,
                'video_booked_count': video_booked_count,
                'dj_count': dj_count,
                'dj_booked_count': dj_booked_count,
                'photobooth_count': photobooth_count,
                'photobooth_booked_count': photobooth_booked_count,
                'total_appointments': total_appointments,
            })
    elif period == 'weekly':
        for week_start in week_range(start_date, end_date):
            week_end = week_start + timedelta(days=6)
            week_contracts = contracts.filter(contract_date__range=(week_start, week_end))

            photo_count = week_contracts.filter(photography_package__isnull=False).count()
            photo_booked_count = week_contracts.filter(photography_package__isnull=False, status='booked').count()
            video_count = week_contracts.filter(videography_package__isnull=False).count()
            video_booked_count = week_contracts.filter(videography_package__isnull=False, status='booked').count()
            dj_count = week_contracts.filter(dj_package__isnull=False).count()
            dj_booked_count = week_contracts.filter(dj_package__isnull=False, status='booked').count()
            photobooth_count = week_contracts.filter(photobooth_package__isnull=False).count()
            photobooth_booked_count = week_contracts.filter(photobooth_package__isnull=False, status='booked').count()
            total_appointments = week_contracts.count()

            report_data.append({
                'period': f"{week_start.strftime('%b %d, %Y')} - {week_end.strftime('%b %d, %Y')}",
                'photo_count': photo_count,
                'photo_booked_count': photo_booked_count,
                'video_count': video_count,
                'video_booked_count': video_booked_count,
                'dj_count': dj_count,
                'dj_booked_count': dj_booked_count,
                'photobooth_count': photobooth_count,
                'photobooth_booked_count': photobooth_booked_count,
                'total_appointments': total_appointments,
            })

    # Gather statistics for each salesperson
    sales_data = []
    salespeople = User.objects.filter(contracts_managed__in=contracts).distinct()

    for salesperson in salespeople:
        sales_contracts = contracts.filter(csr=salesperson)
        total_sales = sales_contracts.count()
        booked_sales = sales_contracts.filter(status='booked').count()
        closed_percentage = (booked_sales / total_sales * 100) if total_sales > 0 else 0

        sales_data.append({
            'name': salesperson.get_full_name(),
            'total_sales': total_sales,
            'booked_sales': booked_sales,
            'closed_percentage': round(closed_percentage, 2),
        })

    # Get all locations for the dropdown
    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'report_data': report_data,
        'sales_data': sales_data,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'locations': locations,
        'selected_location': location_id,
        'selected_period': period,
    }

    return render(request, 'contracts/appointments_report.html', context)

@login_required
def reception_venues_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Get date range, location, and period from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    location_id = request.GET.get('location', 'all')
    period = request.GET.get('period', 'monthly')

    # Default date range to current month if not provided
    today = datetime.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    if not start_date_str:
        start_date = first_day_of_month
        start_date_str = start_date.strftime('%Y-%m-%d')
    else:
        start_date = parse_date(start_date_str)

    if not end_date_str:
        end_date = last_day_of_month
        end_date_str = end_date.strftime('%Y-%m-%d')
    else:
        end_date = parse_date(end_date_str)

    # Filter contracts based on location
    if location_id == 'all':
        contracts = Contract.objects.filter(event_date__range=(start_date, end_date))
    else:
        contracts = Contract.objects.filter(event_date__range=(start_date, end_date), location_id=location_id)

    # Function to generate a list of months in the date range
    def month_range(start_date, end_date):
        start_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        current_month = start_month
        while current_month <= end_month:
            yield current_month
            next_month = current_month + timedelta(days=calendar.monthrange(current_month.year, current_month.month)[1])
            current_month = next_month.replace(day=1)

    # Function to generate a list of weeks in the date range
    def week_range(start_date, end_date):
        start_week = start_date - timedelta(days=start_date.weekday())
        end_week = end_date - timedelta(days=end_date.weekday())
        current_week = start_week
        while current_week <= end_week:
            yield current_week
            current_week += timedelta(days=7)

    # Gather statistics based on the selected period
    report_data = []
    if period == 'monthly':
        for month_start in month_range(start_date, end_date):
            month_end = month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1])
            month_contracts = contracts.filter(event_date__range=(month_start, month_end))

            reception_venues = month_contracts.values('reception_site').annotate(
                event_date=F('event_date'),
                custom_contract_number=F('custom_contract_number'),
                status=F('status'),
                primary_contact=F('client__primary_contact'),
                partner_contact=F('client__partner_contact'),
            ).order_by('reception_site')

            for venue in reception_venues:
                report_data.append({
                    'reception_site': venue['reception_site'],
                    'event_date': venue['event_date'],
                    'custom_contract_number': venue['custom_contract_number'],
                    'status': venue['status'],
                    'primary_contact': venue['primary_contact'],
                    'partner_contact': venue['partner_contact'],
                })
    elif period == 'weekly':
        for week_start in week_range(start_date, end_date):
            week_end = week_start + timedelta(days=6)
            week_contracts = contracts.filter(event_date__range=(week_start, week_end))

            reception_venues = week_contracts.values('reception_site').annotate(
                event_date=F('event_date'),
                custom_contract_number=F('custom_contract_number'),
                status=F('status'),
                primary_contact=F('client__primary_contact'),
                partner_contact=F('client__partner_contact'),
            ).order_by('reception_site')

            for venue in reception_venues:
                report_data.append({
                    'reception_site': venue['reception_site'],
                    'event_date': venue['event_date'],
                    'custom_contract_number': venue['custom_contract_number'],
                    'status': venue['status'],
                    'primary_contact': venue['primary_contact'],
                    'partner_contact': venue['partner_contact'],
                })

    # Get all locations for the dropdown
    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'report_data': report_data,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'locations': locations,
        'selected_location': location_id,
        'selected_period': period,
    }

    return render(request, 'contracts/reception_venues_report.html', context)

def revenue_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_location = request.GET.get('location', 'all')
    group_by = request.GET.get('group_by', 'week')  # Default to grouping by week

    # Initialize filters
    filters = {}
    if start_date:
        filters['payments__date__gte'] = start_date
    if end_date:
        filters['payments__date__lte'] = end_date
    if selected_location != 'all':
        filters['location_id'] = selected_location

    # Filter contracts based on the provided filters
    contracts = Contract.objects.filter(**filters).distinct()

    report_data = []

    if start_date and end_date:
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        current_date = start_date_dt

        total_deposits_received = Decimal('0.00')
        total_other_payments = Decimal('0.00')
        total_tax_collected = Decimal('0.00')
        total_revenue = Decimal('0.00')

        while current_date <= end_date_dt:
            if group_by == 'week':
                period_end_date = current_date + timedelta(days=6)
            else:
                # Move to the end of the month
                next_month = current_date.replace(day=28) + timedelta(days=4)
                period_end_date = next_month - timedelta(days=next_month.day)

            deposits_received = Decimal('0.00')
            other_payments = Decimal('0.00')
            tax_collected = Decimal('0.00')

            payments = Payment.objects.filter(
                contract__in=contracts,
                date__date__gte=current_date,
                date__date__lte=period_end_date
            )

            for payment in payments:
                if payment.contract.balance_due == Decimal('0.00'):
                    tax_collected += payment.contract.calculate_tax()

                if payment.payment_purpose and payment.payment_purpose.name == 'Deposit':
                    deposits_received += payment.amount
                else:
                    other_payments += payment.amount

            period_total_revenue = deposits_received + other_payments

            # Update totals
            total_deposits_received += deposits_received
            total_other_payments += other_payments
            total_tax_collected += tax_collected
            total_revenue += period_total_revenue

            report_data.append({
                'period_start': current_date,
                'period_end': period_end_date,
                'deposits_received': deposits_received.quantize(Decimal('0.00')),
                'other_payments': other_payments.quantize(Decimal('0.00')),
                'tax_collected': tax_collected.quantize(Decimal('0.00')),
                'total_revenue': period_total_revenue.quantize(Decimal('0.00')),
                'original_start_date': start_date,
                'original_end_date': end_date,
            })

            if group_by == 'week':
                current_date = period_end_date + timedelta(days=1)
            else:
                current_date = period_end_date + timedelta(days=1)

        # Append totals row
        report_data.append({
            'period_start': 'Totals',
            'period_end': '',
            'deposits_received': total_deposits_received.quantize(Decimal('0.00')),
            'other_payments': total_other_payments.quantize(Decimal('0.00')),
            'tax_collected': total_tax_collected.quantize(Decimal('0.00')),
            'total_revenue': total_revenue.quantize(Decimal('0.00')),
            'original_start_date': '',
            'original_end_date': '',
        })

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'start_date': start_date,
        'end_date': end_date,
        'selected_location': selected_location,
        'locations': locations,
        'report_data': report_data,
        'group_by': group_by
    }

    return render(request, 'contracts/revenue_report.html', context)

def revenue_by_contract(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    original_start_date = request.GET.get('original_start_date', start_date)
    original_end_date = request.GET.get('original_end_date', end_date)
    selected_location = request.GET.get('location', 'all')
    group_by = request.GET.get('group_by', 'week')  # Default to grouping by week

    # Initialize filters
    filters = {}
    if start_date:
        filters['payments__date__gte'] = start_date
    if end_date:
        filters['payments__date__lte'] = end_date
    if selected_location != 'all':
        filters['location_id'] = selected_location

    # Filter contracts based on the provided filters
    contracts = Contract.objects.filter(**filters).distinct()

    contracts_data = []

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        for contract in contracts:
            contract_payments = Payment.objects.filter(
                contract=contract,
                date__date__gte=start_date,
                date__date__lte=end_date
            )

            payments_data = [
                {
                    'date': payment.date.date(),
                    'amount': payment.amount,
                    'purpose': payment.payment_purpose.name if payment.payment_purpose else 'Unknown',
                }
                for payment in contract_payments
            ]

            contract_data = {
                'contract_id': contract.contract_id,
                'custom_contract_number': contract.custom_contract_number,
                'location': contract.location.name if contract.location else 'N/A',
                'payments': payments_data,
            }

            contracts_data.append(contract_data)

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'contracts_data': contracts_data,
        'start_date': start_date.strftime('%B %d, %Y') if start_date else '',
        'end_date': end_date.strftime('%B %d, %Y') if end_date else '',
        'original_start_date': original_start_date,
        'original_end_date': original_end_date,
        'selected_location': selected_location,
        'group_by': group_by,
        'locations': locations,
    }
    return render(request, 'contracts/revenue_by_contract.html', context)

def deferred_revenue_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    report_date = request.GET.get('report_date')
    selected_location = request.GET.get('location', 'all')

    # Initialize filters for contracts
    filters = {}
    if selected_location != 'all':
        filters['location_id'] = selected_location

    # Filter contracts based on the provided filters
    contracts = Contract.objects.filter(**filters).distinct()

    report_data = []

    if report_date:
        report_date_dt = datetime.strptime(report_date, '%Y-%m-%d')

        locations = Location.objects.all()
        total_deferred_revenue = Decimal('0.00')

        for location in locations:
            location_deferred_revenue = Decimal('0.00')

            payments = Payment.objects.filter(
                contract__in=contracts,
                date__lte=report_date_dt,
                contract__event_date__gt=report_date_dt,  # Only include payments for future events
                contract__location=location
            )

            for payment in payments:
                location_deferred_revenue += payment.amount

            total_deferred_revenue += location_deferred_revenue

            report_data.append({
                'location': location.name,
                'deferred_revenue': location_deferred_revenue.quantize(Decimal('0.00')),
            })

        # Append the total row
        report_data.append({
            'location': 'Total',
            'deferred_revenue': total_deferred_revenue.quantize(Decimal('0.00')),
        })

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'report_date': report_date,
        'selected_location': selected_location,
        'locations': locations,
        'report_data': report_data
    }

    return render(request, 'contracts/deferred_revenue_report.html', context)


SERVICE_ROLE_MAPPING = {
    'PHOTOGRAPHER1': 'photographer1',
    'PHOTOGRAPHER2': 'photographer2',
    'VIDEOGRAPHER1': 'videographer1',
    'VIDEOGRAPHER2': 'videographer2',
    'DJ1': 'dj1',
    'DJ2': 'dj2',
    'PHOTOBOOTH_OP1': 'photobooth_op1',
    'PHOTOBOOTH_OP2': 'photobooth_op2',
    'PROSPECT1': 'prospect_photographer1',  # Updated
    'PROSPECT2': 'prospect_photographer2',  # Updated
    'PROSPECT3': 'prospect_photographer3',
    'ENGAGEMENT': 'engagement'
}

PACKAGE_FIELD_MAPPING = {
    'PHOTOGRAPHER1': 'photography_package',
    'PHOTOGRAPHER2': 'photography_additional',
    'VIDEOGRAPHER1': 'videography_package',
    'VIDEOGRAPHER2': 'videography_additional',
    'DJ1': 'dj_package',
    'DJ2': 'dj_additional',
    'PHOTOBOOTH_OP1': 'photobooth_package',
    'PHOTOBOOTH_OP2': 'photobooth_additional'
}

ROLE_DISPLAY_NAMES = {
    'PHOTOGRAPHER1': 'Photographer 1',
    'PHOTOGRAPHER2': 'Photographer 2',
    'VIDEOGRAPHER1': 'Videographer 1',
    'VIDEOGRAPHER2': 'Videographer 2',
    'DJ1': 'DJ 1',
    'DJ2': 'DJ 2',
    'PHOTOBOOTH_OP1': 'Photobooth Operator 1',
    'PHOTOBOOTH_OP2': 'Photobooth Operator 2'
}

def event_staff_payroll_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_location = request.GET.get('location', 'all')

    filters = {}
    if start_date:
        filters['event_date__gte'] = start_date
    if end_date:
        filters['event_date__lte'] = end_date
    if selected_location != 'all':
        filters['location_id'] = selected_location

    contracts = Contract.objects.filter(**filters).distinct().order_by('event_date')

    report_data = []

    if start_date and end_date:
        start_date_dt = parse_date(start_date)
        end_date_dt = parse_date(end_date)

        for contract in contracts:
            travel_fee_exists = ServiceFee.objects.filter(contract=contract, fee_type__name='Travel Charge').exists()
            travel_fee_amount = ServiceFee.objects.filter(contract=contract, fee_type__name='Travel Charge').aggregate(Sum('amount'))['amount__sum'] or 0
            print(f"Contract: {contract.custom_contract_number}, Travel Fee Exists: {travel_fee_exists}, Travel Fee Amount: {travel_fee_amount}")

            for role_key, field_name in SERVICE_ROLE_MAPPING.items():
                staff_member = getattr(contract, field_name, None)
                if staff_member:
                    regular_hours = 0
                    overtime_role_hours = 0

                    # Calculate total regular hours (package + additional)
                    package_field = PACKAGE_FIELD_MAPPING[role_key]
                    package = getattr(contract, package_field, None)
                    print(f"Contract: {contract.custom_contract_number}, Role: {role_key}, Package: {package}")
                    if package:
                        regular_hours += package.hours
                    print(f"Regular Hours after Package: {regular_hours}")

                    additional = getattr(contract, f'{package_field}_additional', None)
                    print(f"Contract: {contract.custom_contract_number}, Role: {role_key}, Additional: {additional}")
                    if additional:
                        regular_hours += additional.hours
                    print(f"Regular Hours after Additional: {regular_hours}")

                    # Calculate overtime hours by role
                    overtime_entries = ContractOvertime.objects.filter(contract=contract, overtime_option__role=role_key)
                    overtime_role_hours = overtime_entries.aggregate(total_overtime=Sum('hours'))['total_overtime'] or 0
                    print(f"Contract: {contract.custom_contract_number}, Role: {role_key}, Overtime Role Hours: {overtime_role_hours}")

                    report_data.append({
                        'custom_contract_number': contract.custom_contract_number,
                        'event_date': contract.event_date,
                        'role': ROLE_DISPLAY_NAMES[role_key],
                        'staff_name': f"{staff_member.first_name} {staff_member.last_name}",
                        'regular_hours': regular_hours,
                        'overtime_hours': overtime_role_hours,
                        'travel_fee_exists': travel_fee_exists,
                        'travel_fee_amount': travel_fee_amount,
                    })
                    print(f"Report Data Entry: {report_data[-1]}")

    # Group report data by custom contract number
    grouped_report_data = {}
    for entry in report_data:
        contract_number = entry['custom_contract_number']
        if contract_number not in grouped_report_data:
            grouped_report_data[contract_number] = {
                'event_date': entry['event_date'],
                'travel_fee_exists': entry['travel_fee_exists'],
                'travel_fee_amount': entry['travel_fee_amount'],
                'roles': []
            }
        grouped_report_data[contract_number]['roles'].append({
            'role': entry['role'],
            'staff_name': entry['staff_name'],
            'regular_hours': entry['regular_hours'],
            'overtime_hours': entry['overtime_hours']
        })

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'start_date': start_date,
        'end_date': end_date,
        'selected_location': selected_location,
        'locations': locations,
        'grouped_report_data': grouped_report_data
    }

    return render(request, 'contracts/event_staff_payroll_report.html', context)

def sales_detail_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_location = request.GET.get('location', 'all')
    group_by = request.GET.get('group_by', 'week')  # Default to grouping by week

    # Filter contracts by date and location
    contracts = Contract.objects.all()
    if start_date:
        contracts = contracts.filter(contract_date__gte=start_date)
    if end_date:
        contracts = contracts.filter(contract_date__lte=end_date)
    if selected_location != 'all':
        contracts = contracts.filter(location_id=selected_location)

    report_data = []

    if start_date and end_date:
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        current_date = start_date_dt

        while current_date <= end_date_dt:
            if group_by == 'week':
                period_end_date = current_date + timedelta(days=6)
            else:
                # Move to the end of the month
                next_month = current_date.replace(day=28) + timedelta(days=4)
                period_end_date = next_month - timedelta(days=next_month.day)

            period_contracts = contracts.filter(contract_date__gte=current_date, contract_date__lte=period_end_date)

            service_revenue = sum(contract.calculate_total_service_cost() for contract in period_contracts)
            products_revenue = Decimal('0.00')
            taxable_products_revenue = Decimal('0.00')
            other_revenue = sum(contract.calculate_total_service_fees() for contract in period_contracts)
            tax_collected = Decimal('0.00')

            for contract in period_contracts:
                contract_taxable_amount = Decimal('0.00')
                for cp in contract.contract_products.all():
                    product_revenue = cp.quantity * cp.product.price
                    products_revenue += product_revenue
                    if cp.product.is_taxable:
                        taxable_products_revenue += product_revenue
                        contract_taxable_amount += product_revenue

                tax_collected += contract_taxable_amount * contract.tax_rate / 100

            total_revenue = service_revenue + products_revenue + other_revenue

            report_data.append({
                'period_start': current_date.strftime('%Y-%m-%d'),
                'period_end': period_end_date.strftime('%Y-%m-%d'),
                'service_revenue': service_revenue,
                'products_revenue': products_revenue,
                'taxable_products_revenue': taxable_products_revenue,
                'other_revenue': other_revenue,
                'tax_collected': tax_collected,
                'total_revenue': total_revenue,
            })

            if group_by == 'week':
                current_date = period_end_date + timedelta(days=1)
            else:
                current_date = period_end_date + timedelta(days=1)

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'start_date': start_date,
        'end_date': end_date,
        'selected_location': selected_location,
        'locations': locations,
        'report_data': report_data,
        'group_by': group_by
    }

    return render(request, 'contracts/sales_detail_report.html', context)

def sales_detail_by_contract(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_location = request.GET.get('location', 'all')
    group_by = request.GET.get('group_by', 'week')

    contracts = Contract.objects.all()
    if start_date:
        contracts = contracts.filter(contract_date__gte=start_date)
    if end_date:
        contracts = contracts.filter(contract_date__lte=end_date)
    if selected_location != 'all':
        contracts = contracts.filter(location_id=selected_location)

    contract_data = []

    total_service_revenue = Decimal('0.00')
    total_products_revenue = Decimal('0.00')
    total_taxable_products_revenue = Decimal('0.00')
    total_other_revenue = Decimal('0.00')
    total_tax_collected = Decimal('0.00')
    total_revenue = Decimal('0.00')

    if start_date and end_date:
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')

        filtered_contracts = contracts.filter(contract_date__gte=start_date_dt, contract_date__lte=end_date_dt)

        for contract in filtered_contracts:
            service_revenue = contract.calculate_total_service_cost()
            products_revenue = Decimal('0.00')
            taxable_products_revenue = Decimal('0.00')
            other_revenue = contract.calculate_total_service_fees()

            for cp in contract.contract_products.all():
                product_revenue = cp.quantity * cp.product.price
                products_revenue += product_revenue
                if cp.product.is_taxable:
                    taxable_products_revenue += product_revenue

            current_tax_rate = contract.location.tax_rate
            tax_collected = taxable_products_revenue * Decimal(current_tax_rate) / Decimal('100.00')

            total_revenue_per_contract = service_revenue + products_revenue + other_revenue

            contract_data.append({
                'contract_id': contract.contract_id,
                'custom_contract_number': contract.custom_contract_number,
                'location': contract.location.name,
                'service_revenue': service_revenue,
                'products_revenue': products_revenue,
                'taxable_products_revenue': taxable_products_revenue,
                'other_revenue': other_revenue,
                'tax_collected': tax_collected,
                'total_revenue': total_revenue_per_contract,
            })

            total_service_revenue += service_revenue
            total_products_revenue += products_revenue
            total_taxable_products_revenue += taxable_products_revenue
            total_other_revenue += other_revenue
            total_tax_collected += tax_collected
            total_revenue += total_revenue_per_contract

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'start_date': start_date,
        'end_date': end_date,
        'selected_location': selected_location,
        'locations': locations,
        'contract_data': contract_data,
        'group_by': group_by,
        'total_service_revenue': total_service_revenue,
        'total_products_revenue': total_products_revenue,
        'total_taxable_products_revenue': total_taxable_products_revenue,
        'total_other_revenue': total_other_revenue,
        'total_tax_collected': total_tax_collected,
        'total_revenue': total_revenue,
    }

    return render(request, 'contracts/sales_detail_by_contract.html', context)


DATE_RANGE_DISPLAY = {
    'current_quarter': 'Current Quarter',
    'last_quarter': 'Last Quarter',
    'this_month': 'This Month',
    'last_month': 'Last Month',
    'this_year': 'This Year',
    'last_year': 'Last Year',
}

def get_date_range(date_range):
    today = datetime.today()
    if date_range == 'current_quarter':
        quarter = (today.month - 1) // 3 + 1
        start_month = 3 * quarter - 2
        start_date = datetime(today.year, start_month, 1)
        end_month = start_month + 2
        end_date = datetime(today.year, end_month, calendar.monthrange(today.year, end_month)[1])
    elif date_range == 'last_quarter':
        quarter = (today.month - 1) // 3
        if quarter == 0:
            start_date = datetime(today.year - 1, 10, 1)
            end_date = datetime(today.year - 1, 12, 31)
        else:
            start_month = 3 * quarter - 2
            start_date = datetime(today.year, start_month, 1)
            end_month = start_month + 2
            end_date = datetime(today.year, end_month, calendar.monthrange(today.year, end_month)[1])
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
        end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    elif date_range == 'last_month':
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        start_date = last_day_of_last_month.replace(day=1)
        end_date = last_day_of_last_month
    elif date_range == 'this_year':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31)
    elif date_range == 'last_year':
        start_date = datetime(today.year - 1, 1, 1)
        end_date = datetime(today.year - 1, 12, 31)
    else:
        start_date = None
        end_date = None
    return start_date, end_date

def sales_tax_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    date_range = request.GET.get('date_range', 'current_quarter')
    start_date, end_date = get_date_range(date_range)

    if not start_date or not end_date:
        custom_start_date = request.GET.get('start_date')
        custom_end_date = request.GET.get('end_date')
        if custom_start_date and custom_end_date:
            start_date = datetime.strptime(custom_start_date, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end_date, '%Y-%m-%d')

    contracts = Contract.objects.filter(contract_date__gte=start_date, contract_date__lte=end_date)

    report_data = []

    locations = Location.objects.all()
    for location in locations:
        location_contracts = contracts.filter(location=location)
        taxable_products_revenue = Decimal('0.00')
        tax_collected = Decimal('0.00')

        for contract in location_contracts:
            for cp in contract.contract_products.all():
                product_revenue = cp.quantity * cp.product.price
                if cp.product.is_taxable:
                    taxable_products_revenue += product_revenue
                    tax_collected += product_revenue * contract.tax_rate / 100

        report_data.append({
            'location': location.name,
            'taxable_products_revenue': taxable_products_revenue,
            'tax_collected': tax_collected,
        })

    context = {
        'logo_url': logo_url,
        'date_range': DATE_RANGE_DISPLAY.get(date_range, date_range),
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
        'report_data': report_data,
    }

    return render(request, 'contracts/sales_tax_report.html', context)


def payments_due_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Get date range and location from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    location_id = request.GET.get('location', 'all')

    # Default date range to current month if not provided
    today = date.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    if not start_date_str:
        start_date = first_day_of_month
        start_date_str = start_date.strftime('%Y-%m-%d')
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

    if not end_date_str:
        end_date = last_day_of_month
        end_date_str = end_date.strftime('%Y-%m-%d')
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Filter contracts based on location
    contract_filters = {
        'event_date__range': (start_date, end_date)
    }
    if location_id != 'all':
        contract_filters['location_id'] = location_id

    contracts = Contract.objects.filter(**contract_filters)

    # Calculate due payments
    report_data = []
    for contract in contracts:
        client = contract.client
        if contract.payment_schedule.schedule_type == 'schedule_a':
            due_date = contract.event_date - timedelta(days=60)

            # Ensure balance_due is a property access
            balance_due = contract.balance_due

            # Include contracts with a balance due and due date within the selected range
            if balance_due > 0 and start_date <= due_date <= end_date:
                report_data.append({
                    'event_date': contract.event_date,
                    'amount_due': balance_due,
                    'date_due': due_date,
                    'primary_contact': client.primary_contact,
                    'primary_phone1': client.primary_phone1,
                    'custom_contract_number': contract.custom_contract_number,
                    'contract_link': f"/contracts/{contract.contract_id}/"  # Link to the contract details page
                })
        elif contract.payment_schedule.schedule_type == 'custom':
            # Get custom schedule payments
            schedule_payments = SchedulePayment.objects.filter(schedule=contract.payment_schedule,
                                                               due_date__range=(start_date, end_date), paid=False)
            for payment in schedule_payments:
                if payment.amount > 0:
                    report_data.append({
                        'event_date': contract.event_date,
                        'amount_due': payment.amount,
                        'date_due': payment.due_date,
                        'primary_contact': client.primary_contact,
                        'primary_phone1': client.primary_phone1,
                        'custom_contract_number': contract.custom_contract_number,
                        'contract_link': f"/contracts/{contract.contract_id}/"  # Link to the contract details page
                    })

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'report_data': report_data,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'locations': locations,
        'selected_location': location_id,
    }

    return render(request, 'contracts/payments_due_report.html', context)

def formal_wear_deposit_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_location = request.GET.get('location', 'all')

    filters = {}
    if start_date:
        filters['event_date__gte'] = start_date
    if end_date:
        filters['event_date__lte'] = end_date
    if selected_location != 'all':
        filters['location_id'] = selected_location

    report_data = []
    if start_date or end_date or selected_location != 'all':
        contracts = Contract.objects.filter(**filters).distinct().order_by('event_date')

        for contract in contracts:
            formal_wear_deposit_exists = ServiceFee.objects.filter(contract=contract, fee_type__name='Formal Wear Deposit').exists()

            if formal_wear_deposit_exists:
                report_data.append({
                    'event_date': contract.event_date,
                    'custom_contract_number': contract.custom_contract_number,
                    'contract_link': f"/contracts/{contract.contract_id}/",  # Link to the contract details page
                    'primary_contact': contract.client.primary_contact,
                    'primary_email': contract.client.primary_email,
                    'primary_phone1': contract.client.primary_phone1,
                })

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'report_data': sorted(report_data, key=lambda x: x['event_date']),
        'start_date': start_date,
        'end_date': end_date,
        'selected_location': selected_location,
        'locations': locations,
    }

    return render(request, 'contracts/formal_wear_deposit_report.html', context)