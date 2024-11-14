
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.conf import settings
from communication.views import send_contract_and_rider_email_to_client
from .forms import ContractAgreementForm, ContractDocumentForm
from .models import ContractDocument, ContractAgreement, RiderAgreement
from contracts.models import Contract
from users.views import ROLE_DISPLAY_NAMES
import os
from django.http import HttpResponse, JsonResponse
from django.template.defaultfilters import linebreaks
from django.contrib import messages
from collections import defaultdict
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile

@login_required
def delete_document(request, document_id):
    document = get_object_or_404(ContractDocument, pk=document_id)

    # Check if the user has permission to delete the document
    if request.user.has_perm('contracts.delete_contractdocument') or request.user == document.contract.owner:
        document.delete()
        messages.success(request, "Document removed successfully.")
    else:
        messages.error(request, "You do not have permission to delete this document.")

    # Redirect back to the contract detail page or wherever appropriate
    return redirect('contracts:contract_detail', id=document.contract.contract_id)

@require_GET
def client_documents(request, contract_id):
    try:
        contract = Contract.objects.get(contract_id=contract_id)
        documents = contract.documents.filter(is_client_visible=True)
        document_list = [
            {
                'id': doc.id,
                'url': doc.document.url,
                'name': os.path.basename(doc.document.name),  # Extract the file name
                'badge_class': 'badge-success' if doc.is_client_visible else 'badge-secondary',
                'badge_label': 'Visible to Client' if doc.is_client_visible else 'Internal Use'
            } for doc in documents
        ]
        return JsonResponse(document_list, safe=False)
    except Contract.DoesNotExist:
        return JsonResponse({'error': 'Contract not found'}, status=404)



@login_required
def generate_contract_pdf(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)

    # Constructing full URL for the logo and company signature
    domain = 'enet2.com'
    logo_url = f'http://{domain}{settings.MEDIA_URL}logo/Final_Logo.png'
    company_signature_url = f'http://{domain}{settings.MEDIA_URL}signatures/company_signature.png'

    # Package texts
    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    # Additional services text processing
    additional_services_texts = {
        'photography_additional': linebreaks(
            contract.photography_additional.default_text) if contract.photography_additional else None,
        'videography_additional': linebreaks(
            contract.videography_additional.default_text) if contract.videography_additional else None,
        'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
        'photobooth_additional': linebreaks(
            contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
    }

    # Additional staff
    additional_staff = defaultdict(list)
    for staff_option in [contract.photography_additional, contract.videography_additional, contract.dj_additional,
                         contract.photobooth_additional]:
        if staff_option:
            additional_staff[staff_option.service_type.name].append({
                'name': staff_option.name,
                'service_type': staff_option.service_type.name,
                'price': staff_option.price,
                'hours': staff_option.hours,
                'default_text': staff_option.default_text,
            })

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = 0

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        service_type = contract_overtime.overtime_option.service_type.name
        if service_type in overtime_options_by_service_type:
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                               contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
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

    total_service_cost = contract.calculate_total_service_cost()
    total_discount = contract.calculate_discount()
    total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

    # Get the first contract agreement for the contract
    first_agreement = ContractAgreement.objects.filter(contract=contract).order_by('version_number').first()

    # Get the latest contract agreement for the contract
    latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()

    # Get the rider agreements for the contract
    rider_agreements = RiderAgreement.objects.filter(contract=contract)

    context = {
        'contract': contract,
        'client_info': {
            'primary_contact': contract.client.primary_contact if contract.client else 'N/A',
            'primary_email': contract.client.primary_email if contract.client else 'N/A',
            'primary_phone': contract.client.primary_phone1 if contract.client else 'N/A',
            'partner_contact': contract.client.partner_contact if contract.client else 'N/A',
        },
        'logo_url': logo_url,
        'company_signature_url': company_signature_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'additional_staff': additional_staff,
        'total_overtime_cost': total_overtime_cost,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
        'total_service_cost': total_service_cost,
        'total_discount': total_discount,
        'total_cost_after_discounts': total_cost_after_discounts,
        'rider_agreements': rider_agreements,
        'first_agreement': first_agreement,  # Add first agreement to context
        'latest_agreement': latest_agreement,  # Add latest agreement to context
    }

    # Render HTML to string
    html_string = render_to_string('documents/contract_template.html', context)

    # Generate PDF from HTML
    pdf = HTML(string=html_string).write_pdf()

    # Send response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contract_{contract_id}.pdf"'
    return response


@login_required
def contract_agreement(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    if request.method == 'POST':
        rider_type = request.POST.get('rider_type')
        if rider_type:
            # Handle sending a specific rider email
            send_contract_and_rider_email_to_client(request, contract, rider_type=rider_type)
            return JsonResponse({'status': 'success', 'message': f'{rider_type.replace("_", " ").capitalize()} agreement email sent successfully.'})
        elif 'contract_agreement' in request.POST:
            # Handle sending just the contract agreement email
            send_contract_and_rider_email_to_client(request, contract, only_contract=True)
            return JsonResponse({'status': 'success', 'message': 'Contract agreement email sent successfully.'})
        else:
            # Handle sending the combined contract and rider agreements email
            send_contract_and_rider_email_to_client(request, contract)
            return JsonResponse({'status': 'success', 'message': 'Contract and rider agreements email sent successfully.'})

    form = ContractAgreementForm()

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = 0

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        # Get the service type of the overtime option
        service_type = contract_overtime.overtime_option.service_type.name

        # Check if the service type already exists in the dictionary
        if service_type in overtime_options_by_service_type:
            # If the service type exists, append the overtime option to its list
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
            # If the service type does not exist, create a new list with the overtime option
            overtime_options_by_service_type[service_type] = [{
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            }]

    # Calculate total cost for each overtime option
    for service_type, options in overtime_options_by_service_type.items():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

    context = {
        'contract': contract,
        'logo_url': logo_url,
        'form': form,
        'package_texts': {
            'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else '',
            'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else '',
            'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else '',
            'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else '',
        },
        'additional_services_texts': {
            'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else '',
            'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else '',
            'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else '',
            'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else '',
        },
        'rider_texts': {
            'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else '',
            'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else '',
            'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else '',
            'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else '',
        },
        'total_service_cost': contract.calculate_total_service_cost(),
        'total_discount': contract.calculate_discount(),
        'total_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
        'photographer_choices': [
            contract.prospect_photographer1,
            contract.prospect_photographer2,
            contract.prospect_photographer3
        ],
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'total_overtime_cost': total_overtime_cost,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,  # Add role display names to context
    }

    return render(request, 'documents/contract_agreement_form.html', context)




@login_required
def client_contract_agreement(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    if request.method == 'POST':
        form = ContractAgreementForm(request.POST)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.contract = contract
            agreement.signature = form.cleaned_data['main_signature']

            latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
            agreement.version_number = latest_agreement.version_number + 1 if latest_agreement else 1

            # Save the state of services
            agreement.photography_service = contract.photography_package.service_type if contract.photography_package else None
            agreement.videography_service = contract.videography_package.service_type if contract.videography_package else None
            agreement.dj_service = contract.dj_package.service_type if contract.dj_package else None
            agreement.photobooth_service = contract.photobooth_package.service_type if contract.photobooth_package else None

            agreement.save()

            portal_url = reverse('contracts:client_portal', args=[contract_id])

            # Render the status page upon successful form submission
            return render(request, 'contracts/status_page.html', {
                'message': 'You\'re all set, thank you!',
                'portal_url': portal_url
            })
        else:
            portal_url = reverse('contracts:client_portal', args=[contract_id])

            return render(request, 'contracts/status_page.html', {
                'message': 'There was an error submitting the contract agreement.',
                'portal_url': portal_url
            })

    else:
        form = ContractAgreementForm()

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = 0

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        # Get the service type of the overtime option
        service_type = contract_overtime.overtime_option.service_type.name

        # Check if the service type already exists in the dictionary
        if service_type in overtime_options_by_service_type:
            # If the service type exists, append the overtime option to its list
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
            # If the service type does not exist, create a new list with the overtime option
            overtime_options_by_service_type[service_type] = [{
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            }]

    # Calculate total cost for each overtime option
    for service_type, options in overtime_options_by_service_type.items():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    context = {
        'contract': contract,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'total_service_cost': contract.calculate_total_service_cost(),
        'total_discount': contract.calculate_discount(),
        'total_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
        'photographer_choices': [
            contract.prospect_photographer1,
            contract.prospect_photographer2,
            contract.prospect_photographer3
        ],
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'total_overtime_cost': total_overtime_cost,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,  # Add role display names to context
        'form': form,
    }

    return render(request, 'documents/client_contract_agreement.html', context)

@login_required
def view_submitted_contract(request, contract_id, version_number):
    contract = get_object_or_404(Contract, pk=contract_id)
    contract_agreement = get_object_or_404(ContractAgreement, contract=contract, version_number=version_number)
    rider_agreements = RiderAgreement.objects.filter(contract=contract)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = 0

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        # Get the service type of the overtime option
        service_type = contract_overtime.overtime_option.service_type.name

        # Check if the service type already exists in the dictionary
        if service_type in overtime_options_by_service_type:
            # If the service type exists, append the overtime option to its list
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
            # If the service type does not exist, create a new list with the overtime option
            overtime_options_by_service_type[service_type] = [{
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            }]

    # Calculate total cost for each overtime option
    for service_type, options in overtime_options_by_service_type.items():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    additional_services_texts = {
        'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
        'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
        'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
        'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
    }

    total_service_cost = contract.calculate_total_service_cost()
    total_discount = contract.calculate_discount()
    total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

    context = {
        'contract': contract,
        'contract_agreement': contract_agreement,
        'rider_agreements': rider_agreements,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'total_service_cost': total_service_cost,
        'total_discount': total_discount,
        'total_cost_after_discounts': total_cost_after_discounts,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'total_overtime_cost': total_overtime_cost,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,  # Add role display names to context
    }

    return render(request, 'documents/view_submitted_contract.html', context)

@login_required
def client_contract_and_rider_agreement(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    company_signature_url = f"http://{request.get_host()}{settings.MEDIA_URL}essence_signature/EssenceSignature.png"

    if request.method == 'POST':
        form = ContractAgreementForm(request.POST)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.contract = contract
            agreement.signature = form.cleaned_data['main_signature']
            agreement.photographer_choice = form.cleaned_data['photographer_choice']  # Save photographer choice

            latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
            agreement.version_number = latest_agreement.version_number + 1 if latest_agreement else 1

            agreement.save()

            rider_agreements = []
            for rider in ['photography', 'photography_additional', 'videography', 'videography_additional', 'dj',
                          'dj_additional', 'photobooth', 'photobooth_additional']:
                signature = request.POST.get(f'signature_{rider}')
                client_name = request.POST.get(f'client_name_{rider}')
                agreement_date = request.POST.get(f'agreement_date_{rider}')
                notes = request.POST.get(f'notes_{rider}')
                rider_text = request.POST.get(f'rider_text_{rider}')

                if signature:
                    rider_agreement = RiderAgreement.objects.create(
                        contract=contract,
                        rider_type=rider,
                        signature=signature,
                        client_name=client_name,
                        agreement_date=agreement_date,
                        notes=notes,
                        rider_text=rider_text
                    )
                    rider_agreements.append(rider_agreement)
                else:
                    print(f"Missing signature for {rider}")

            # Initialize an empty dictionary to store overtime options grouped by service type
            overtime_options_by_service_type = {}

            # Initialize total overtime cost
            total_overtime_cost = 0

            # Iterate over each overtime option
            for contract_overtime in contract.overtimes.all():
                service_type = contract_overtime.overtime_option.service_type.name
                if service_type in overtime_options_by_service_type:
                    overtime_options_by_service_type[service_type].append({
                        'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                       contract_overtime.overtime_option.role),
                        'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                        'hours': contract_overtime.hours,
                    })
                else:
                    overtime_options_by_service_type[service_type] = [{
                        'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                       contract_overtime.overtime_option.role),
                        'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                        'hours': contract_overtime.hours,
                    }]

            for service_type, options in overtime_options_by_service_type.items():
                for option in options:
                    option['total_cost'] = option['hours'] * option['rate_per_hour']
                    total_overtime_cost += option['total_cost']

            package_texts = {
                'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
                'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
                'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
                'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
            }

            additional_services_texts = {
                'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
                'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
                'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
                'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
            }

            rider_texts = {
                'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else None,
                'photography_additional': linebreaks(contract.photography_additional.rider_text) if contract.photography_additional else None,
                'engagement_session': linebreaks(contract.engagement_session.rider_text) if contract.engagement_session else None,
                'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else None,
                'videography_additional': linebreaks(contract.videography_additional.rider_text) if contract.videography_additional else None,
                'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else None,
                'dj_additional': linebreaks(contract.dj_additional.rider_text) if contract.dj_additional else None,
                'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else None,
                'photobooth_additional': linebreaks(contract.photobooth_additional.rider_text) if contract.photobooth_additional else None,
            }

            total_service_cost = contract.calculate_total_service_cost()
            total_discount = contract.calculate_discount()
            total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

            context = {
                'contract': contract,
                'logo_url': logo_url,
                'company_signature_url': company_signature_url,
                'latest_agreement': agreement,
                'rider_agreements': rider_agreements,
                'package_texts': package_texts,
                'additional_services_texts': additional_services_texts,
                'rider_texts': rider_texts,
                'total_service_cost': total_service_cost,
                'total_discount': total_discount,
                'total_cost_after_discounts': total_cost_after_discounts,
                'overtime_options_by_service_type': overtime_options_by_service_type,
                'total_overtime_cost': total_overtime_cost,
                'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
            }

            # Generate PDF
            html_string = render_to_string('documents/client_contract_and_rider_agreement_pdf.html', context)
            pdf_file = HTML(string=html_string).write_pdf()

            # Save PDF to the documents section of the contract
            pdf_name = f"contract_{contract_id}_agreement.pdf"
            path = default_storage.save(f"contract_documents/{pdf_name}", ContentFile(pdf_file))

            ContractDocument.objects.create(
                contract=contract,
                document=path,
                is_client_visible=True,
            )

            # Email the PDF to the client
            client_email = contract.client.primary_email
            email = EmailMessage(
                subject="Your Contract Agreement",
                body="Please find attached your signed contract agreement.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[client_email],
            )
            email.attach(pdf_name, pdf_file, 'application/pdf')
            email.send()

            portal_url = reverse('contracts:client_portal', args=[contract_id])
            return render(request, 'contracts/status_page.html', {
                'message': 'You\'re all set, thank you!',
                'portal_url': portal_url
            })
        else:
            portal_url = reverse('client_portal', args=[contract_id])

            return render(request, 'contracts/status_page.html', {
                'message': 'There was an error submitting the agreements.',
                'portal_url': portal_url
            })

    else:
        form = ContractAgreementForm()

        # Initialize an empty dictionary to store overtime options grouped by service type
        overtime_options_by_service_type = {}

        # Initialize total overtime cost
        total_overtime_cost = 0

        # Iterate over each overtime option
        for contract_overtime in contract.overtimes.all():
            service_type = contract_overtime.overtime_option.service_type.name
            if service_type in overtime_options_by_service_type:
                overtime_options_by_service_type[service_type].append({
                    'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                   contract_overtime.overtime_option.role),
                    'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                    'hours': contract_overtime.hours,
                })
            else:
                overtime_options_by_service_type[service_type] = [{
                    'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                   contract_overtime.overtime_option.role),
                    'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                    'hours': contract_overtime.hours,
                }]

        for service_type, options in overtime_options_by_service_type.items():
            for option in options:
                option['total_cost'] = option['hours'] * option['rate_per_hour']
                total_overtime_cost += option['total_cost']

        package_texts = {
            'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
            'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
            'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
            'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
        }

        additional_services_texts = {
            'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
            'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
            'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
            'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
        }

        rider_texts = {
            'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else None,
            'photography_additional': linebreaks(contract.photography_additional.rider_text) if contract.photography_additional else None,
            'engagement_session': linebreaks(contract.engagement_session.rider_text) if contract.engagement_session else None,
            'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else None,
            'videography_additional': linebreaks(contract.videography_additional.rider_text) if contract.videography_additional else None,
            'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else None,
            'dj_additional': linebreaks(contract.dj_additional.rider_text) if contract.dj_additional else None,
            'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else None,
            'photobooth_additional': linebreaks(contract.photobooth_additional.rider_text) if contract.photobooth_additional else None,
        }

        total_service_cost = contract.calculate_total_service_cost()
        total_discount = contract.calculate_discount()
        total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

        photographer_choices = [
            contract.prospect_photographer1,
            contract.prospect_photographer2,
            contract.prospect_photographer3
        ]

        context = {
            'contract': contract,
            'logo_url': logo_url,
            'package_texts': package_texts,
            'additional_services_texts': additional_services_texts,
            'rider_texts': rider_texts,
            'total_service_cost': total_service_cost,
            'total_discount': total_discount,
            'total_cost_after_discounts': total_cost_after_discounts,
            'photographer_choices': photographer_choices,
            'overtime_options_by_service_type': overtime_options_by_service_type,
            'total_overtime_cost': total_overtime_cost,
            'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
            'form': form,
        }

        return render(request, 'documents/client_contract_and_rider_agreement.html', context)


@login_required
def client_rider_agreement(request, contract_id, rider_type):
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    company_signature_url = f"http://{request.get_host()}{settings.MEDIA_URL}essence_signature/EssenceSignature.png"


    if request.method == 'POST':
        form = ContractAgreementForm(request.POST)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.contract = contract
            agreement.signature = form.cleaned_data['main_signature']

            latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
            agreement.version_number = latest_agreement.version_number + 1 if latest_agreement else 1

            agreement.save()

            signature = request.POST.get(f'signature_{rider_type}')
            client_name = request.POST.get(f'client_name_{rider_type}')
            agreement_date = request.POST.get(f'agreement_date_{rider_type}')
            notes = request.POST.get(f'notes_{rider_type}')
            rider_text = request.POST.get(f'rider_text_{rider_type}')

            rider_agreement = None
            if signature:
                try:
                    rider_agreement = RiderAgreement.objects.create(
                        contract=contract,
                        rider_type=rider_type,
                        signature=signature,
                        client_name=client_name,
                        agreement_date=agreement_date,
                        notes=notes,
                        rider_text=rider_text
                    )
                except Exception as e:
                    pass

            # Generate PDF
            rider_agreements = RiderAgreement.objects.filter(contract=contract)
            first_agreement = ContractAgreement.objects.filter(contract=contract).order_by('version_number').first()

            context = {
                'contract': contract,
                'logo_url': logo_url,
                'company_signature_url': company_signature_url,
                'latest_agreement': agreement,
                'rider_agreement': rider_agreement,
                'rider_agreements': rider_agreements,
                'first_agreement': first_agreement,
            }

            # Initialize an empty dictionary to store overtime options grouped by service type
            overtime_options_by_service_type = {}

            # Initialize total overtime cost
            total_overtime_cost = 0

            # Iterate over each overtime option
            for contract_overtime in contract.overtimes.all():
                service_type = contract_overtime.overtime_option.service_type.name
                if service_type in overtime_options_by_service_type:
                    overtime_options_by_service_type[service_type].append({
                        'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                       contract_overtime.overtime_option.role),
                        'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                        'hours': contract_overtime.hours,
                    })
                else:
                    overtime_options_by_service_type[service_type] = [{
                        'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                       contract_overtime.overtime_option.role),
                        'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                        'hours': contract_overtime.hours,
                    }]

            for service_type, options in overtime_options_by_service_type.items():
                for option in options:
                    option['total_cost'] = option['hours'] * option['rate_per_hour']
                    total_overtime_cost += option['total_cost']

            package_texts = {
                'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
                'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
                'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
                'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
            }

            additional_services_texts = {
                'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
                'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
                'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
                'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
            }

            rider_texts = {
                'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else None,
                'photography_additional': linebreaks(contract.photography_additional.rider_text) if contract.photography_additional else None,
                'engagement_session': linebreaks(contract.engagement_session.rider_text) if contract.engagement_session else None,
                'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else None,
                'videography_additional': linebreaks(contract.videography_additional.rider_text) if contract.videography_additional else None,
                'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else None,
                'dj_additional': linebreaks(contract.dj_additional.rider_text) if contract.dj_additional else None,
                'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else None,
                'photobooth_additional': linebreaks(contract.photobooth_additional.rider_text) if contract.photobooth_additional else None,
            }

            total_service_cost = contract.calculate_total_service_cost()
            total_discount = contract.calculate_discount()
            total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

            context.update({
                'overtime_options_by_service_type': overtime_options_by_service_type,
                'total_overtime_cost': total_overtime_cost,
                'package_texts': package_texts,
                'additional_services_texts': additional_services_texts,
                'rider_texts': rider_texts,
                'total_service_cost': total_service_cost,
                'total_discount': total_discount,
                'total_cost_after_discounts': total_cost_after_discounts,
            })

            html_string = render_to_string('documents/client_contract_and_rider_agreement_pdf.html', context)
            pdf_file = HTML(string=html_string).write_pdf()

            # Save PDF to the documents section of the contract
            pdf_name = f"contract_{contract_id}_rider_{rider_type}.pdf"
            path = default_storage.save(f"contract_documents/{pdf_name}", ContentFile(pdf_file))

            ContractDocument.objects.create(
                contract=contract,
                document=path,
                is_client_visible=True,
            )

            # Email the PDF to the client
            client_email = contract.client.primary_email
            email = EmailMessage(
                subject=f"Your {rider_type.replace('_', ' ').capitalize()} Rider Agreement",
                body="Please find attached your signed rider agreement.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[client_email],
            )
            email.attach(pdf_name, pdf_file, 'application/pdf')
            email.send()

            portal_url = reverse('contracts:client_portal', args=[contract_id])
            return render(request, 'contracts/status_page.html', {
                'message': 'You\'re all set, thank you!',
                'portal_url': portal_url
            })
        else:
            portal_url = reverse('contracts:client_portal', args=[contract_id])

            return render(request, 'contracts/status_page.html', {
                'message': 'There was an error submitting the agreements.',
                'portal_url': portal_url
            })
    else:
        form = ContractAgreementForm()

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = 0

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        # Get the service type of the overtime option
        service_type = contract_overtime.overtime_option.service_type.name

        # Check if the service type already exists in the dictionary
        if service_type in overtime_options_by_service_type:
            # If the service type exists, append the overtime option to its list
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
            # If the service type does not exist, create a new list with the overtime option
            overtime_options_by_service_type[service_type] = [{
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            }]

    for service_type, options in overtime_options_by_service_type.items():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    additional_services_texts = {
        'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
        'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
        'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
        'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
    }

    rider_texts = {
        'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else None,
        'photography_additional': linebreaks(contract.photography_additional.rider_text) if contract.photography_additional else None,
        'engagement_session': linebreaks(contract.engagement_session.rider_text) if contract.engagement_session else None,
        'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else None,
        'videography_additional': linebreaks(contract.videography_additional.rider_text) if contract.videography_additional else None,
        'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else None,
        'dj_additional': linebreaks(contract.dj_additional.rider_text) if contract.dj_additional else None,
        'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else None,
        'photobooth_additional': linebreaks(contract.photobooth_additional.rider_text) if contract.photobooth_additional else None,
    }

    total_service_cost = contract.calculate_total_service_cost()
    total_discount = contract.calculate_discount()
    total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

    photographer_choices = [
        contract.prospect_photographer1,
        contract.prospect_photographer2,
        contract.prospect_photographer3
    ]

    context = {
        'contract': contract,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'rider_texts': rider_texts,
        'total_service_cost': total_service_cost,
        'total_discount': total_discount,
        'total_cost_after_discounts': total_cost_after_discounts,
        'photographer_choices': photographer_choices,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'total_overtime_cost': total_overtime_cost,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
        'form': form,
        'rider_text': rider_texts.get(rider_type, ""),
        'rider_type': rider_type,
    }

    return render(request, 'documents/client_rider_agreement.html', context)


def view_rider_agreements(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    rider_agreements = RiderAgreement.objects.filter(contract=contract)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    additional_services_texts = {
        'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
        'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
        'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
        'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
    }

    total_service_cost = contract.calculate_total_service_cost()
    total_discount = contract.calculate_discount()
    total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

    context = {
        'contract': contract,
        'rider_agreements': rider_agreements,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'total_service_cost': total_service_cost,
        'total_discount': total_discount,
        'total_cost_after_discounts': total_cost_after_discounts,
    }

    return render(request, 'documents/view_rider_agreement.html', context)



@login_required
def upload_contract_documents(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    if request.method == 'POST':
        form = ContractDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            contract_document = form.save(commit=False)
            contract_document.contract = contract
            contract_document.save()
            return redirect('contracts:contract_detail', pk=contract_id)
    else:
        form = ContractDocumentForm()

    return render(request, 'documents/upload_contract_documents.html', {'form': form})