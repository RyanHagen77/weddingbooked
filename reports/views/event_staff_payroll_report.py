
from django.shortcuts import render

from django.conf import settings
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location, ServiceFee
from services.models import ContractOvertime
from django.db.models import Sum
from django.utils.dateparse import parse_date


import logging

# Logging setup
logger = logging.getLogger(__name__)


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


@login_required
def event_staff_payroll_report(request):
    logo_url = f"https://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
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

    if start_date:
        start_date = parse_date(start_date)
    if end_date:
        end_date = parse_date(end_date)

        for contract in contracts:
            travel_fee_exists = ServiceFee.objects.filter(contract=contract, fee_type__name='Travel Charge').exists()
            travel_fee_amount = (
                    ServiceFee.objects.filter(contract=contract, fee_type__name='Travel Charge').aggregate(Sum('amount'))['amount__sum'] or 0)
            print(f"Contract: {contract.custom_contract_number}, Travel Fee Exists: {travel_fee_exists}, Travel Fee Amount: {travel_fee_amount}")

            # Exclude PROSPECT roles from the report
            excluded_roles = {'PROSPECT1', 'PROSPECT2', 'PROSPECT3'}
            for role_key, field_name in SERVICE_ROLE_MAPPING.items():
                if role_key in excluded_roles:
                    continue  # Skip excluded roles

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

    return render(request, 'reports/event_staff_payroll_report.html', context)
