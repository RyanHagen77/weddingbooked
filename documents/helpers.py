from decimal import Decimal
from contracts.models import Contract
from users.views import ROLE_DISPLAY_NAMES
from django.template.defaultfilters import linebreaks


def calculate_overtime_cost(contract_id):
    contract = Contract.objects.get(pk=contract_id)

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = Decimal('0.00')

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        # Get the service type of the overtime option
        service_type = contract_overtime.overtime_option.service_type.name

        # Check if the service type already exists in the dictionary
        if service_type in overtime_options_by_service_type:
            # If the service type exists, append the overtime option to its list
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                               contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
            # If the service type does not exist, create a new list with the overtime option
            overtime_options_by_service_type[service_type] = [{
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                               contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            }]

    # Calculate total cost for each overtime option
    for service_type, options in overtime_options_by_service_type.items():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

    return overtime_options_by_service_type, total_overtime_cost


def calculate_service_discounts(contract_id):
    contract = Contract.objects.get(pk=contract_id)

    # Calculate the total package discount
    selected_services = []
    if contract.photography_package:
        selected_services.append('photography')
    if contract.videography_package:
        selected_services.append('videography')
    if contract.dj_package:
        selected_services.append('dj')
    if contract.photobooth_package:
        selected_services.append('photobooth')

    # Calculate the discount per service for the package discount
    discount_per_service = Decimal('0.00')
    num_services = len(selected_services)
    if num_services > 0:
        discount_per_service = contract.calculate_package_discount() / num_services

    # Apply the calculated discount to each service
    service_discounts = {
        'photography': discount_per_service if contract.photography_package else Decimal('0.00'),
        'videography': discount_per_service if contract.videography_package else Decimal('0.00'),
        'dj': discount_per_service if contract.dj_package else Decimal('0.00'),
        'photobooth': discount_per_service if contract.photobooth_package else Decimal('0.00')
    }

    return service_discounts


# utils.py

def get_discount_details(contract):
    # Fetch other discounts
    other_discounts = contract.other_discounts.all()

    # Calculate discounts
    package_discount = contract.calculate_package_discount()  # Example method for package discount
    sunday_discount = contract.calculate_sunday_discount()  # Example method for Sunday discount
    other_discount_total = sum([discount.amount for discount in other_discounts])  # Summing up all other discounts
    total_discount = contract.calculate_discount()  # Calculate total discount (if any)


    return {
        'other_discounts': other_discounts,
        'package_discount': package_discount,
        'sunday_discount': sunday_discount,
        'other_discount_total': other_discount_total,
        'total_discount': total_discount,

    }


def calculate_total_deposit(contract):
    deposit_due_to_book = Decimal('0.00')

    if contract.photography_package:
        deposit_due_to_book += contract.photography_package.deposit
    if contract.videography_package:
        deposit_due_to_book += contract.videography_package.deposit
    if contract.dj_package:
        deposit_due_to_book += contract.dj_package.deposit
    if contract.photobooth_package:
        deposit_due_to_book += contract.photobooth_package.deposit
    if contract.photography_additional:
        deposit_due_to_book += contract.photography_additional.deposit
    if contract.videography_additional:
        deposit_due_to_book += contract.videography_additional.deposit
    if contract.dj_additional:
        deposit_due_to_book += contract.dj_additional.deposit
    if contract.photobooth_additional:
        deposit_due_to_book += contract.photobooth_additional.deposit
    if contract.engagement_session:
        deposit_due_to_book += contract.engagement_session.deposit

    return deposit_due_to_book


def get_package_and_service_texts(contract):
    package_texts = {
        'photography': contract.photography_package.default_text if contract.photography_package else None,
        'videography': contract.videography_package.default_text if contract.videography_package else None,
        'dj': contract.dj_package.default_text if contract.dj_package else None,
        'photobooth': contract.photobooth_package.default_text if contract.photobooth_package else None,
    }

    additional_services_texts = {
        'photography_additional': contract.photography_additional.default_text if contract.photography_additional else None,
        'videography_additional': contract.videography_additional.default_text if contract.videography_additional else None,
        'dj_additional': contract.dj_additional.default_text if contract.dj_additional else None,
        'photobooth_additional': contract.photobooth_additional.default_text if contract.photobooth_additional else None,
    }

    return package_texts, additional_services_texts


def get_rider_texts(contract):
    rider_texts = {
        'photography': linebreaks(
            contract.photography_package.rider_text) if contract.photography_package else None,
        'photography_additional': linebreaks(
            contract.photography_additional.rider_text) if contract.photography_additional else None,
        'engagement_session': linebreaks(
            contract.engagement_session.rider_text) if contract.engagement_session else None,
        'videography': linebreaks(
            contract.videography_package.rider_text) if contract.videography_package else None,
        'videography_additional': linebreaks(
            contract.videography_additional.rider_text) if contract.videography_additional else None,
        'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else None,
        'dj_additional': linebreaks(contract.dj_additional.rider_text) if contract.dj_additional else None,
        'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else None,
        'photobooth_additional': linebreaks(
            contract.photobooth_additional.rider_text) if contract.photobooth_additional else None,
    }