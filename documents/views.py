
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.conf import settings
from communication.views import send_contract_and_rider_email_to_client
from .forms import ContractAgreementForm, ContractDocumentForm
from .models import ContractDocument, ContractAgreement, RiderAgreement
from contracts.models import Contract
from users.views import ROLE_DISPLAY_NAMES
import os
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.template.defaultfilters import linebreaks
from django.contrib import messages
from collections import defaultdict
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
    domain = 'enet2.com'
    logo_url = f'{settings.MEDIA_URL}logo/Final_Logo.png'

    # Calculate the total discount
    total_discount = contract.calculate_discount()

    # Calculate the due date (60 days before the event date)
    due_date = contract.event_date - timedelta(days=60)

    # Other discounts and their names (assuming you have a method for other discounts or a list)
    other_discounts = contract.other_discounts.all()  # Assuming 'other_discounts' is a related field or a method on the contract

    # Add the individual discount amounts to context
    package_discount = contract.calculate_package_discount()  # Example method for package discount
    sunday_discount = contract.calculate_sunday_discount()  # Example method for Sunday discount
    other_discount_total = sum([discount.amount for discount in other_discounts])  # Summing up all other discounts

    # Calculate the total package discount
    package_discount = contract.calculate_package_discount()

    # Get the selected services for package discounts
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
    num_services = len(selected_services)
    if num_services > 0:
        discount_per_service = package_discount / num_services
    else:
        discount_per_service = Decimal('0.00')


    # Apply the calculated discount to each service
    photography_discount = discount_per_service if contract.photography_package else Decimal('0.00')
    videography_discount = discount_per_service if contract.videography_package else Decimal('0.00')
    dj_discount = discount_per_service if contract.dj_package else Decimal('0.00')
    photobooth_discount = discount_per_service if contract.photobooth_package else Decimal('0.00')

    # Package texts (No linebreaks)
    package_texts = {
        'photography': contract.photography_package.default_text if contract.photography_package else None,
        'videography': contract.videography_package.default_text if contract.videography_package else None,
        'dj': contract.dj_package.default_text if contract.dj_package else None,
        'photobooth': contract.photobooth_package.default_text if contract.photobooth_package else None,
    }

    # Additional services text processing (No linebreaks)
    additional_services_texts = {
        'photography_additional': contract.photography_additional.default_text if contract.photography_additional else None,
        'videography_additional': contract.videography_additional.default_text if contract.videography_additional else None,
        'dj_additional': contract.dj_additional.default_text if contract.dj_additional else None,
        'photobooth_additional': contract.photobooth_additional.default_text if contract.photobooth_additional else None,
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

    # Process overtime options
    overtime_options_by_service_type = {}
    total_overtime_cost = 0
    for contract_overtime in contract.overtimes.all():
        service_type = contract_overtime.overtime_option.service_type.name
        option_data = {
            'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                           contract_overtime.overtime_option.role),
            'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
            'hours': contract_overtime.hours,
        }
        overtime_options_by_service_type.setdefault(service_type, []).append(option_data)
    for options in overtime_options_by_service_type.values():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

        # Add formalwear products with their default text to the context
    formalwear_details = []

    for formalwear_contract in contract.formalwear_contracts.all():
        formalwear_details.append({
            'product_name': formalwear_contract.formalwear_product.name,
            'default_text': formalwear_contract.formalwear_product.default_text,
            'rental_price': formalwear_contract.formalwear_product.rental_price,
            'deposit_amount': formalwear_contract.formalwear_product.deposit_amount,
            'quantity': formalwear_contract.quantity,
        })

    # Calculate totals
    product_subtotal = contract.calculate_product_subtotal()
    formalwear_subtotal = contract.calculate_formalwear_subtotal()
    tax_rate_percentage = float(contract.tax_rate)
    tax_amount = contract.calculate_tax()
    product_subtotal_with_tax = product_subtotal + tax_amount

    total_service_cost = contract.calculate_total_service_cost()
    total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()
    grand_total = contract.calculate_total_cost()

    # Calculate the total deposit for each service
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


    # Pre-calculate payments totals to avoid recursion in templates
    amount_paid = sum(payment.amount for payment in contract.payments.all()) or Decimal('0.00')
    balance_due = max(Decimal('0.00'), grand_total - amount_paid)

    # Get the first and latest agreements and rider agreements
    first_agreement = ContractAgreement.objects.filter(contract=contract).order_by('version_number').first()
    latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
    rider_agreements = RiderAgreement.objects.filter(contract=contract)

    # Build the context with the necessary discount data
    context = {
        'contract': contract,
        'client_info': {
            'primary_contact': contract.client.primary_contact if contract.client else 'N/A',
            'primary_email': contract.client.primary_email if contract.client else 'N/A',
            'primary_phone': contract.client.primary_phone1 if contract.client else 'N/A',
            'partner_contact': contract.client.partner_contact if contract.client else 'N/A',
        },
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'additional_staff': additional_staff,
        'total_overtime_cost': total_overtime_cost,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
        'formalwear_details': formalwear_details,
        'product_subtotal': product_subtotal,
        'formalwear_subtotal': formalwear_subtotal,
        'product_subtotal_with_tax': product_subtotal_with_tax,
        'service_fees': contract.servicefees.all(),
        'service_fees_total': contract.calculate_total_service_fees(),
        'total_service_cost': total_service_cost,
        'tax_rate': tax_rate_percentage,
        'tax_amount': tax_amount,
        'total_discount': total_discount,
        'package_discount': package_discount,
        'sunday_discount': sunday_discount,
        'other_discounts': other_discounts,  # This will include the other discounts' details
        'other_discount_total': other_discount_total,
        'total_cost_after_discounts': total_cost_after_discounts,
        'deposit_due_to_book': deposit_due_to_book,
        'grand_total': grand_total,
        'amount_paid': amount_paid,
        'balance_due': balance_due,
        'due_date': due_date.strftime('%B %d, %Y'),  # Format the due date
        'rider_agreements': rider_agreements,
        'first_agreement': first_agreement,
        'latest_agreement': latest_agreement,
        'photography_discount': photography_discount,
        'videography_discount': videography_discount,
        'dj_discount': dj_discount,
        'photobooth_discount': photobooth_discount,
    }

    # Render HTML to string using your main template
    html_string = render_to_string(
        'documents/contract_agreements/contract_agreement.html',
        context
    )

    # Generate PDF from HTML
    pdf = HTML(string=html_string).write_pdf()

    # Return PDF response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contract_{contract_id}.pdf"'
    return response


@login_required
def contract_agreement(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f'{settings.MEDIA_URL}logo/Final_Logo.png'

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

    # Calculate the total discount
    total_discount = contract.calculate_discount()

    # Calculate the due date (60 days before the event date)
    due_date = contract.event_date - timedelta(days=60)

    # Other discounts and their names (assuming you have a method for other discounts or a list)
    other_discounts = contract.other_discounts.all()  # Assuming 'other_discounts' is a related field or a method on the contract

    # Add the individual discount amounts to context
    package_discount = contract.calculate_package_discount()  # Example method for package discount
    sunday_discount = contract.calculate_sunday_discount()  # Example method for Sunday discount
    other_discount_total = sum([discount.amount for discount in other_discounts])  # Summing up all other discounts

    # Calculate the total package discount
    package_discount = contract.calculate_package_discount()

    # Get the selected services for package discounts
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
    num_services = len(selected_services)
    if num_services > 0:
        discount_per_service = package_discount / num_services
    else:
        discount_per_service = Decimal('0.00')

    # Apply the calculated discount to each service
    photography_discount = discount_per_service if contract.photography_package else Decimal('0.00')
    videography_discount = discount_per_service if contract.videography_package else Decimal('0.00')
    dj_discount = discount_per_service if contract.dj_package else Decimal('0.00')
    photobooth_discount = discount_per_service if contract.photobooth_package else Decimal('0.00')

    # Package texts
    package_texts = {
        'photography': contract.photography_package.default_text if contract.photography_package else None,
        'videography': contract.videography_package.default_text if contract.videography_package else None,
        'dj': contract.dj_package.default_text if contract.dj_package else None,
        'photobooth': contract.photobooth_package.default_text if contract.photobooth_package else None,
    }

    # Additional services text processing
    additional_services_texts = {
        'photography_additional': contract.photography_additional.default_text if contract.photography_additional else None,
        'videography_additional': contract.videography_additional.default_text if contract.videography_additional else None,
        'dj_additional': contract.dj_additional.default_text if contract.dj_additional else None,
        'photobooth_additional': contract.photobooth_additional.default_text if contract.photobooth_additional else None,
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

    # Process overtime options
    overtime_options_by_service_type = {}
    total_overtime_cost = 0
    for contract_overtime in contract.overtimes.all():
        service_type = contract_overtime.overtime_option.service_type.name
        option_data = {
            'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                           contract_overtime.overtime_option.role),
            'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
            'hours': contract_overtime.hours,
        }
        overtime_options_by_service_type.setdefault(service_type, []).append(option_data)
    for options in overtime_options_by_service_type.values():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

        # Add formalwear products with their default text to the context
    formalwear_details = []

    for formalwear_contract in contract.formalwear_contracts.all():
        formalwear_details.append({
            'product_name': formalwear_contract.formalwear_product.name,
            'default_text': formalwear_contract.formalwear_product.default_text,
            'rental_price': formalwear_contract.formalwear_product.rental_price,
            'deposit_amount': formalwear_contract.formalwear_product.deposit_amount,
            'quantity': formalwear_contract.quantity,
        })

    # Calculate totals
    product_subtotal = contract.calculate_product_subtotal()
    formalwear_subtotal = contract.calculate_formalwear_subtotal()
    tax_rate_percentage = float(contract.tax_rate)
    tax_amount = contract.calculate_tax()
    product_subtotal_with_tax = product_subtotal + tax_amount

    total_service_cost = contract.calculate_total_service_cost()
    total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()
    grand_total = contract.calculate_total_cost()

    # Calculate the total deposit for each service
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

    # Pre-calculate payments totals to avoid recursion in templates
    amount_paid = sum(payment.amount for payment in contract.payments.all()) or Decimal('0.00')
    balance_due = max(Decimal('0.00'), grand_total - amount_paid)

    # Get the first and latest agreements and rider agreements
    first_agreement = ContractAgreement.objects.filter(contract=contract).order_by('version_number').first()
    latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
    rider_agreements = RiderAgreement.objects.filter(contract=contract)

    # Build the context with the necessary discount data
    context = {
        'contract': contract,
        'photographer_choices': [
            contract.prospect_photographer1,
            contract.prospect_photographer2,
            contract.prospect_photographer3
        ],

        'rider_texts': {
            'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else '',
            'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else '',
            'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else '',
            'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else '',
        },

        'client_info': {
            'primary_contact': contract.client.primary_contact if contract.client else 'N/A',
            'primary_email': contract.client.primary_email if contract.client else 'N/A',
            'primary_phone': contract.client.primary_phone1 if contract.client else 'N/A',
            'partner_contact': contract.client.partner_contact if contract.client else 'N/A',
        },
        'form': form,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'additional_staff': additional_staff,
        'total_overtime_cost': total_overtime_cost,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
        'formalwear_details': formalwear_details,
        'product_subtotal': product_subtotal,
        'formalwear_subtotal': formalwear_subtotal,
        'product_subtotal_with_tax': product_subtotal_with_tax,
        'service_fees': contract.servicefees.all(),
        'service_fees_total': contract.calculate_total_service_fees(),
        'total_service_cost': total_service_cost,
        'tax_rate': tax_rate_percentage,
        'tax_amount': tax_amount,
        'total_discount': total_discount,
        'package_discount': package_discount,
        'sunday_discount': sunday_discount,
        'other_discounts': other_discounts,  # This will include the other discounts' details
        'other_discount_total': other_discount_total,
        'total_cost_after_discounts': total_cost_after_discounts,
        'deposit_due_to_book': deposit_due_to_book,
        'grand_total': grand_total,
        'amount_paid': amount_paid,
        'balance_due': balance_due,
        'due_date': due_date.strftime('%B %d, %Y'),  # Format the due date
        'rider_agreements': rider_agreements,
        'first_agreement': first_agreement,
        'latest_agreement': latest_agreement,
        'photography_discount': photography_discount,
        'videography_discount': videography_discount,
        'dj_discount': dj_discount,
        'photobooth_discount': photobooth_discount,
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

            # Increment version number
            latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
            agreement.version_number = latest_agreement.version_number + 1 if latest_agreement else 1

            # Save services
            agreement.photography_service = contract.photography_package.service_type if contract.photography_package else None
            agreement.videography_service = contract.videography_package.service_type if contract.videography_package else None
            agreement.dj_service = contract.dj_package.service_type if contract.dj_package else None
            agreement.photobooth_service = contract.photobooth_package.service_type if contract.photobooth_package else None

            agreement.save()

            # Prepare context for PDF generation
            package_texts = {
                'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
                'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
                'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
                'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
            }

            overtime_options_by_service_type = {}
            total_overtime_cost = 0
            for contract_overtime in contract.overtimes.all():
                service_type = contract_overtime.overtime_option.service_type.name
                option = {
                    'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                    'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                    'hours': contract_overtime.hours,
                }
                option['total_cost'] = option['hours'] * option['rate_per_hour']
                total_overtime_cost += option['total_cost']
                overtime_options_by_service_type.setdefault(service_type, []).append(option)

            context = {
                'contract': contract,
                'logo_url': logo_url,
                'package_texts': package_texts,
                'total_service_cost': contract.calculate_total_service_cost(),
                'total_discount': contract.calculate_discount(),
                'total_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
                'overtime_options_by_service_type': overtime_options_by_service_type,
                'total_overtime_cost': total_overtime_cost,
                'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
                'latest_agreement': agreement,
            }

            # Generate PDF
            html_string = render_to_string('documents/client_contract_agreement_pdf.html', context)
            pdf_file = HTML(string=html_string).write_pdf()

            # Save PDF to contract documents
            pdf_name = f"contract_{contract_id}_agreement.pdf"
            path = default_storage.save(f"contract_documents/{pdf_name}", ContentFile(pdf_file))
            ContractDocument.objects.create(contract=contract, document=path, is_client_visible=True)

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

            portal_url = reverse('users:client_portal', args=[contract_id])
            return render(request, 'contracts/status_page.html', {
                'message': 'You\'re all set, thank you!',
                'portal_url': portal_url
            })
        else:
            return render(request, 'contracts/status_page.html', {
                'message': 'There was an error submitting the contract agreement.',
                'portal_url': reverse('users:client_portal', args=[contract_id])
            })

    else:
        form = ContractAgreementForm()
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
    domain = 'enet2.com'
    logo_url = f'{settings.MEDIA_URL}logo/Final_Logo.png'
    company_signature_url = f'{domain}{settings.MEDIA_URL}signatures/company_signature.png'

    # Prepare context for the template (loaded on both GET and POST)
    context = {
        'contract': contract,
        'logo_url': logo_url,
        'company_signature_url': company_signature_url,
        'client_info': {
            'primary_contact': contract.client.primary_contact if contract.client else 'N/A',
            'primary_email': contract.client.primary_email if contract.client else 'N/A',
            'primary_phone': contract.client.primary_phone1 if contract.client else 'N/A',
            'partner_contact': contract.client.partner_contact if contract.client else 'N/A',
        },
    }

    # Calculate the total deposit for each service
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

    # Get service fees and the total amount for the service fees
    service_fees = contract.servicefees.all()
    service_fees_total = contract.calculate_total_service_fees()

    # Get formalwear details
    formalwear_details = []
    for formalwear_contract in contract.formalwear_contracts.all():
        formalwear_details.append({
            'product_name': formalwear_contract.formalwear_product.name,
            'default_text': formalwear_contract.formalwear_product.default_text,
            'rental_price': formalwear_contract.formalwear_product.rental_price,
            'deposit_amount': formalwear_contract.formalwear_product.deposit_amount,
            'quantity': formalwear_contract.quantity,
        })

    # Calculate other contract-related data for use in the template
    total_discount = contract.calculate_discount()
    due_date = contract.event_date - timedelta(days=60)

    # Calculate other discounts and their amounts
    other_discounts = contract.other_discounts.all()
    package_discount = contract.calculate_package_discount()
    sunday_discount = contract.calculate_sunday_discount()
    other_discount_total = sum([discount.amount for discount in other_discounts])

    # Calculate the discount per service for the package discount
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
    num_services = len(selected_services)
    discount_per_service = package_discount / num_services if num_services > 0 else Decimal('0.00')

    # Apply the calculated discount to each service
    photography_discount = discount_per_service if contract.photography_package else Decimal('0.00')
    videography_discount = discount_per_service if contract.videography_package else Decimal('0.00')
    dj_discount = discount_per_service if contract.dj_package else Decimal('0.00')
    photobooth_discount = discount_per_service if contract.photobooth_package else Decimal('0.00')

    context.update({
        'total_discount': total_discount,
        'due_date': due_date.strftime('%B %d, %Y'),
        'photography_discount': photography_discount,
        'videography_discount': videography_discount,
        'dj_discount': dj_discount,
        'photobooth_discount': photobooth_discount,
        'package_discount': package_discount,
        'sunday_discount': sunday_discount,
        'service_fees': service_fees,
        'service_fees_total': service_fees_total,
        'formalwear_details': formalwear_details,
        'deposit_due_to_book': deposit_due_to_book
    })

    if request.method == 'POST':
        form = ContractAgreementForm(request.POST)
        if form.is_valid():
            # Only process the specific fields in the POST request
            agreement = form.save(commit=False)
            agreement.contract = contract
            agreement.signature = form.cleaned_data['main_signature']
            agreement.photographer_choice = form.cleaned_data['photographer_choice']  # Save photographer choice

            # Get the latest contract agreement to increment the version number
            latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
            agreement.version_number = latest_agreement.version_number + 1 if latest_agreement else 1
            agreement.save()

            # Handle Rider Agreements
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

            # After form submission, generate PDF
            html_string = render_to_string('documents/client_contract_and_rider_agreement_pdf.html', context)
            pdf_file = HTML(string=html_string).write_pdf()

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

            # Return status page
            portal_url = reverse('users:client_portal', args=[contract_id])
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

            portal_url = reverse('users:client_portal', args=[contract_id])
            return render(request, 'contracts/status_page.html', {
                'message': 'You\'re all set, thank you!',
                'portal_url': portal_url
            })
        else:
            portal_url = reverse('users:client_portal', args=[contract_id])

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