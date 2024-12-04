import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import (AdditionalEventStaffOption, ContractOvertime, EngagementSessionOption,
                     OvertimeOption, Package, ServiceType)

from contracts.models import Contract
from django.http import JsonResponse
def get_package_options(request):
    # Get the service type name from request query parameters
    service_type_name = request.GET.get('service_type', None)

    # Initialize the response data
    response_data = {'packages': []}

    # Check if a service type name is provided and exists
    if service_type_name:
        service_type = ServiceType.objects.filter(name=service_type_name).first()
        if service_type:
            # Filter packages by the found service type
            packages = Package.objects.filter(service_type=service_type, is_active=True).order_by('name')
            # Prepare the package data for the response
            response_data['packages'] = [
                {
                    'id': package.id,
                    'name': package.name,
                    'price': str(package.price),
                    'hours': package.hours,
                    'default_text': package.default_text  # Make sure this attribute exists in your model
                }
                for package in packages
            ]
        else:
            # Optionally, include an error message if the service type is not found
            response_data['error'] = 'Service type not found'

    return JsonResponse(response_data)

def get_additional_staff_options(request):
    # Get the service type name from request query parameters
    service_type_name = request.GET.get('service_type', None)

    # Initialize the base queryset
    queryset = AdditionalEventStaffOption.objects.filter(is_active=True)

    # If a service type name is provided, filter the queryset by that service type
    if service_type_name:
        service_type = ServiceType.objects.filter(name=service_type_name).first()
        if service_type:
            queryset = queryset.filter(service_type=service_type)

    # Fetch the filtered or unfiltered staff options
    staff_options = queryset.values('id', 'name', 'price', 'hours')

    return JsonResponse({'staff_options': list(staff_options)})

def get_engagement_session_options(request):
    # Query your EngagementSessionOption model for active sessions
    sessions = EngagementSessionOption.objects.filter(is_active=True).values('id', 'name', 'price')
    # Convert the QuerySet to a list to make it JSON serializable
    sessions_list = list(sessions)
    # Wrap the list in an object with a 'sessions' key
    return JsonResponse({'sessions': sessions_list})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_overtime_entry(request, id):
    try:
        contract = Contract.objects.get(pk=id)
    except Contract.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Contract not found'}, status=404)

    try:
        data = json.loads(request.body.decode('utf-8'))
        option_id = data.get('optionId')
        hours = data.get('hours')
        entry_id = data.get('entryId')
    except (ValueError, KeyError):
        return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

    try:
        overtime_option = OvertimeOption.objects.get(pk=option_id)
        if entry_id:
            overtime_entry = ContractOvertime.objects.get(pk=entry_id, contract=contract)
            overtime_entry.overtime_option = overtime_option
            overtime_entry.hours = hours
        else:
            overtime_entry = ContractOvertime(contract=contract, overtime_option=overtime_option, hours=hours)
        overtime_entry.save()
        return JsonResponse({'status': 'success', 'message': 'Overtime entry saved successfully'})
    except (OvertimeOption.DoesNotExist, ContractOvertime.DoesNotExist, ValueError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_overtime_entry(request, entry_id):
    try:
        overtime_entry = ContractOvertime.objects.get(id=entry_id)
        response_data = {
            'id': overtime_entry.id,
            'overtime_option_id': overtime_entry.overtime_option.id,
            'hours': float(overtime_entry.hours),
        }
        return JsonResponse(response_data)
    except ContractOvertime.DoesNotExist:
        return JsonResponse({'error': 'Entry not found'}, status=404)

@require_POST
def edit_overtime_entry(request, entry_id):
    data = json.loads(request.body)
    try:
        entry = ContractOvertime.objects.get(pk=entry_id)
        entry.overtime_option_id = data['overtime_option']
        entry.hours = data['hours']
        entry.save()

        return JsonResponse({'status': 'success', 'message': 'Entry updated successfully'})
    except ContractOvertime.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Entry not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
def delete_overtime_entry(request, entry_id):
    try:
        entry = ContractOvertime.objects.get(pk=entry_id)
        entry.delete()
        return JsonResponse({'status': 'success', 'message': 'Entry deleted successfully'})
    except ContractOvertime.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Entry not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def get_overtime_entries(request, contract_id):
    service_type = request.GET.get('service_type')
    try:
        entries = ContractOvertime.objects.filter(
            contract_id=contract_id,
            overtime_option__service_type__name=service_type
        ).select_related('overtime_option')

        entries_data = [{
            'id': entry.id,
            'overtime_option': entry.overtime_option.role,
            'hours': entry.hours,
            'cost': entry.overtime_option.rate_per_hour * entry.hours
        } for entry in entries]

        return JsonResponse({'status': 'success', 'entries': entries_data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'Error retrieving overtime entries'}, status=500)

def get_overtime_options(request):
    service_type_name = request.GET.get('service_type', None)
    options_list = []

    if service_type_name:
        try:
            service_type = ServiceType.objects.get(name=service_type_name)
            options = OvertimeOption.objects.filter(is_active=True, service_type=service_type)
        except ServiceType.DoesNotExist:
            return JsonResponse({'error': 'ServiceType not found'}, status=404)
    else:
        options = OvertimeOption.objects.filter(is_active=True)

    options_list = options.values('id', 'role', 'rate_per_hour', 'service_type__name', 'description')
    return JsonResponse(list(options_list), safe=False)
