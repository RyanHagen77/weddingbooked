from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.conf import settings
from communication.utils import send_contract_and_rider_email_to_client
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

from .helpers import (calculate_overtime_cost, calculate_service_discounts, get_package_and_service_texts,
                      get_rider_texts, calculate_total_deposit, get_discount_details)

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
def contract_agreement_preview(request, contract_id):
    # Fetch contract object
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f'{settings.MEDIA_URL}logo/Final_Logo.png'


    # Initialize the form
    form = ContractAgreementForm()

    # Handle POST request
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

    # Fetch other discounts
    discount_details = get_discount_details(contract)

    # Calculate service discounts
    service_discounts = calculate_service_discounts(contract_id)

    # Get package and additional services text
    package_texts, additional_services_texts = get_package_and_service_texts(contract)

    # Process overtime options
    overtime_options_by_service_type, total_overtime_cost = calculate_overtime_cost(contract_id)

    # Calculate totals
    formalwear_subtotal = contract.calculate_formalwear_subtotal()

    product_subtotal = contract.calculate_product_subtotal()
    tax_rate_percentage = float(contract.tax_rate)
    tax_amount = contract.calculate_tax()
    product_subtotal_with_tax = product_subtotal + tax_amount

    # Calculate total deposit due to book
    deposit_due_to_book = calculate_total_deposit(contract)

    # Pre-calculate payments totals to avoid recursion in templates
    amount_paid = sum(payment.amount for payment in contract.payments.all()) or Decimal('0.00')
    balance_due = max(Decimal('0.00'), contract.calculate_total_cost() - amount_paid)

    # Calculate the due date (60 days before the event date)
    due_date = contract.event_date - timedelta(days=60)

    # Add contract products to the context
    contract_products = contract.contract_products.all()

    # Build the context
    context = {
        'contract': contract,
        'form': form,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'total_overtime_cost': total_overtime_cost,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'formalwear_contracts': contract.formalwear_contracts.all(),  # Directly pass formalwear contracts to template
        'formalwear_subtotal': formalwear_subtotal,
        'product_subtotal': product_subtotal,
        'tax_rate': tax_rate_percentage,
        'tax_amount': tax_amount,
        'product_subtotal_with_tax': product_subtotal_with_tax,
        'service_fees': contract.servicefees.all(),
        'service_fees_total': contract.calculate_total_service_fees(),
        'total_service_cost': contract.calculate_total_service_cost(),
        'package_discount': discount_details['package_discount'],
        'sunday_discount': discount_details['sunday_discount'],
        'other_discount_total': discount_details['other_discount_total'],
        'total_discount': discount_details['total_discount'],
        'other_discounts': discount_details['other_discounts'],
        'total_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
        'deposit_due_to_book': deposit_due_to_book,
        'grand_total': contract.calculate_total_cost(),
        'amount_paid': amount_paid,
        'balance_due': balance_due,
        'due_date': due_date.strftime('%B %d, %Y'),
        'photography_discount': service_discounts['photography'],
        'videography_discount': service_discounts['videography'],
        'dj_discount': service_discounts['dj'],
        'photobooth_discount': service_discounts['photobooth'],
        'contract_products': contract_products,  # Add products to context
        'photographer_choices': [
            contract.prospect_photographer1,
            contract.prospect_photographer2,
            contract.prospect_photographer3
        ]
    }

    return render(request, 'documents/contract_agreement_preview.html', context)



@login_required
def generate_contract_pdf(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f'{settings.MEDIA_URL}logo/Final_Logo.png'

    # Fetch other discounts
    discount_details = get_discount_details(contract)

    # Calculate service discounts
    service_discounts = calculate_service_discounts(contract_id)

    # Get package and additional services text
    package_texts, additional_services_texts = get_package_and_service_texts(contract)

    # Process overtime options
    overtime_options_by_service_type, total_overtime_cost = calculate_overtime_cost(contract_id)

    # Calculate totals
    formalwear_subtotal = contract.calculate_formalwear_subtotal()

    product_subtotal = contract.calculate_product_subtotal()
    tax_rate_percentage = float(contract.tax_rate)
    tax_amount = contract.calculate_tax()
    product_subtotal_with_tax = product_subtotal + tax_amount

    # Calculate total deposit due to book
    deposit_due_to_book = calculate_total_deposit(contract)

    # Pre-calculate payments totals to avoid recursion in templates
    amount_paid = sum(payment.amount for payment in contract.payments.all()) or Decimal('0.00')
    balance_due = max(Decimal('0.00'), contract.calculate_total_cost() - amount_paid)

    # Calculate the due date (60 days before the event date)
    due_date = contract.event_date - timedelta(days=60)

    # Add contract products to the context
    contract_products = contract.contract_products.all()

    # Build the context
    context = {
        'contract': contract,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'total_overtime_cost': total_overtime_cost,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'formalwear_contracts': contract.formalwear_contracts.all(),  # Directly pass formalwear contracts to template
        'formalwear_subtotal': formalwear_subtotal,
        'product_subtotal': product_subtotal,
        'tax_rate': tax_rate_percentage,
        'tax_amount': tax_amount,
        'product_subtotal_with_tax': product_subtotal_with_tax,
        'service_fees': contract.servicefees.all(),
        'service_fees_total': contract.calculate_total_service_fees(),
        'total_service_cost': contract.calculate_total_service_cost(),
        'package_discount': discount_details['package_discount'],
        'sunday_discount': discount_details['sunday_discount'],
        'other_discount_total': discount_details['other_discount_total'],
        'total_discount': discount_details['total_discount'],
        'other_discounts': discount_details['other_discounts'],
        'total_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
        'deposit_due_to_book': deposit_due_to_book,
        'grand_total': contract.calculate_total_cost(),
        'amount_paid': amount_paid,
        'balance_due': balance_due,
        'due_date': due_date.strftime('%B %d, %Y'),
        'photography_discount': service_discounts['photography'],
        'videography_discount': service_discounts['videography'],
        'dj_discount': service_discounts['dj'],
        'photobooth_discount': service_discounts['photobooth'],
        'contract_products': contract_products,  # Add products to context
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
def view_submitted_contract(request, contract_id, version_number):
    contract = get_object_or_404(Contract, pk=contract_id)
    contract_agreement = get_object_or_404(ContractAgreement, contract=contract, version_number=version_number)
    logo_url = f'{settings.MEDIA_URL}logo/Final_Logo.png'

    # Fetch other discounts
    discount_details = get_discount_details(contract)

    # Calculate service discounts
    service_discounts = calculate_service_discounts(contract_id)

    # Get package and additional services text
    package_texts, additional_services_texts = get_package_and_service_texts(contract)

    # Process overtime options
    overtime_options_by_service_type, total_overtime_cost = calculate_overtime_cost(contract_id)

    # Calculate totals
    formalwear_subtotal = contract.calculate_formalwear_subtotal()

    product_subtotal = contract.calculate_product_subtotal()
    tax_rate_percentage = float(contract.tax_rate)
    tax_amount = contract.calculate_tax()
    product_subtotal_with_tax = product_subtotal + tax_amount

    # Calculate total deposit due to book
    deposit_due_to_book = calculate_total_deposit(contract)

    # Pre-calculate payments totals to avoid recursion in templates
    amount_paid = sum(payment.amount for payment in contract.payments.all()) or Decimal('0.00')
    balance_due = max(Decimal('0.00'), contract.calculate_total_cost() - amount_paid)

    # Calculate the due date (60 days before the event date)
    due_date = contract.event_date - timedelta(days=60)

    # Add contract products to the context
    contract_products = contract.contract_products.all()

    # Build the context
    context = {
        'contract': contract,
        'contract_agreement': contract_agreement,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'total_overtime_cost': total_overtime_cost,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'formalwear_contracts': contract.formalwear_contracts.all(),  # Directly pass formalwear contracts to template
        'formalwear_subtotal': formalwear_subtotal,
        'product_subtotal': product_subtotal,
        'tax_rate': tax_rate_percentage,
        'tax_amount': tax_amount,
        'product_subtotal_with_tax': product_subtotal_with_tax,
        'service_fees': contract.servicefees.all(),
        'service_fees_total': contract.calculate_total_service_fees(),
        'total_service_cost': contract.calculate_total_service_cost(),
        'package_discount': discount_details['package_discount'],
        'sunday_discount': discount_details['sunday_discount'],
        'other_discount_total': discount_details['other_discount_total'],
        'total_discount': discount_details['total_discount'],
        'other_discounts': discount_details['other_discounts'],
        'total_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
        'deposit_due_to_book': deposit_due_to_book,
        'grand_total': contract.calculate_total_cost(),
        'amount_paid': amount_paid,
        'balance_due': balance_due,
        'due_date': due_date.strftime('%B %d, %Y'),
        'photography_discount': service_discounts['photography'],
        'videography_discount': service_discounts['videography'],
        'dj_discount': service_discounts['dj'],
        'photobooth_discount': service_discounts['photobooth'],
        'contract_products': contract_products,  # Add products to context
        'photographer_choices': [
            contract.prospect_photographer1,
            contract.prospect_photographer2,
            contract.prospect_photographer3
        ]
    }

    return render(request, 'documents/view_submitted_contract.html', context)


@login_required
def contract_and_rider_agreement(request, contract_id):
    # Fetch contract object
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f"{settings.MEDIA_URL}logo/Final_Logo.png"
    company_signature_url = f"{settings.MEDIA_URL}contract_signatures/EssenceSignature.png"

    if request.method == 'POST':
        form = ContractAgreementForm(request.POST)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.contract = contract
            agreement.signature = form.cleaned_data['main_signature']
            agreement.photographer_choice = form.cleaned_data['photographer_choice']

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

        discount_details = get_discount_details(contract)
        service_discounts = calculate_service_discounts(contract_id)
        package_texts, additional_services_texts = get_package_and_service_texts(contract)
        rider_texts = get_rider_texts(contract)
        overtime_options_by_service_type, total_overtime_cost = calculate_overtime_cost(contract_id)
        formalwear_subtotal = contract.calculate_formalwear_subtotal()
        product_subtotal = contract.calculate_product_subtotal()
        tax_rate_percentage = float(contract.tax_rate)
        tax_amount = contract.calculate_tax()
        product_subtotal_with_tax = product_subtotal + tax_amount
        deposit_due_to_book = calculate_total_deposit(contract)
        amount_paid = sum(payment.amount for payment in contract.payments.all()) or Decimal('0.00')
        balance_due = max(Decimal('0.00'), contract.calculate_total_cost() - amount_paid)
        due_date = contract.event_date - timedelta(days=60)
        contract_products = contract.contract_products.all()

        first_agreement = ContractAgreement.objects.filter(contract=contract).order_by('version_number').first()
        latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
        rider_agreements = RiderAgreement.objects.filter(contract=contract)

        context = {
            'contract': contract,
            'logo_url': logo_url,
            'company_signature_url': company_signature_url,
            'first_agreement': first_agreement,
            'latest_agreement': latest_agreement,
            'rider_agreements': rider_agreements,
            'package_texts': package_texts,
            'additional_services_texts': additional_services_texts,
            'rider_texts': rider_texts,
            'total_overtime_cost': total_overtime_cost,
            'overtime_options_by_service_type': overtime_options_by_service_type,
            'formalwear_contracts': contract.formalwear_contracts.all(),
            'formalwear_subtotal': formalwear_subtotal,
            'product_subtotal': product_subtotal,
            'tax_rate': tax_rate_percentage,
            'tax_amount': tax_amount,
            'product_subtotal_with_tax': product_subtotal_with_tax,
            'service_fees': contract.servicefees.all(),
            'service_fees_total': contract.calculate_total_service_fees(),
            'total_service_cost': contract.calculate_total_service_cost(),
            'package_discount': discount_details['package_discount'],
            'sunday_discount': discount_details['sunday_discount'],
            'other_discount_total': discount_details['other_discount_total'],
            'total_discount': discount_details['total_discount'],
            'other_discounts': discount_details['other_discounts'],
            'total_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
            'deposit_due_to_book': deposit_due_to_book,
            'grand_total': contract.calculate_total_cost(),
            'amount_paid': amount_paid,
            'balance_due': balance_due,
            'due_date': due_date.strftime('%B %d, %Y'),
            'photography_discount': service_discounts['photography'],
            'videography_discount': service_discounts['videography'],
            'dj_discount': service_discounts['dj'],
            'photobooth_discount': service_discounts['photobooth'],
            'contract_products': contract_products,
            'photographer_choices': [
                contract.prospect_photographer1,
                contract.prospect_photographer2,
                contract.prospect_photographer3
            ],
            'show_riders': request.POST.get('contract_agreement') != 'true'
        }

        latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
        html_string = render_to_string('documents/client_contract_and_rider_agreement_pdf.html', context)
        pdf_file = HTML(string=html_string).write_pdf()
        pdf_name = f"contract_{contract_id}_agreement_v{latest_agreement.version_number}.pdf"
        path = default_storage.save(f"contract_documents/{pdf_name}", ContentFile(pdf_file))

        ContractDocument.objects.create(
            contract=contract,
            document=path,
            is_client_visible=True,
        )

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
        return render(request, 'documents/status_page.html', {
            'message': 'You\'re all set, thank you!',
            'portal_url': portal_url
        })
    else:
        discount_details = get_discount_details(contract)
        service_discounts = calculate_service_discounts(contract_id)
        package_texts, additional_services_texts = get_package_and_service_texts(contract)
        overtime_options_by_service_type, total_overtime_cost = calculate_overtime_cost(contract_id)
        formalwear_subtotal = contract.calculate_formalwear_subtotal()
        product_subtotal = contract.calculate_product_subtotal()
        tax_rate_percentage = float(contract.tax_rate)
        tax_amount = contract.calculate_tax()
        product_subtotal_with_tax = product_subtotal + tax_amount
        deposit_due_to_book = calculate_total_deposit(contract)
        amount_paid = sum(payment.amount for payment in contract.payments.all()) or Decimal('0.00')
        balance_due = max(Decimal('0.00'), contract.calculate_total_cost() - amount_paid)
        due_date = contract.event_date - timedelta(days=60)
        contract_products = contract.contract_products.all()

        first_agreement = ContractAgreement.objects.filter(contract=contract).order_by('version_number').first()
        latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
        rider_agreements = RiderAgreement.objects.filter(contract=contract)

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

        context = {
            'contract': contract,
            'logo_url': logo_url,
            'company_signature_url': company_signature_url,
            'first_agreement': first_agreement,
            'latest_agreement': latest_agreement,
            'rider_agreements': rider_agreements,
            'package_texts': package_texts,
            'additional_services_texts': additional_services_texts,
            'rider_texts': rider_texts,
            'total_overtime_cost': total_overtime_cost,
            'overtime_options_by_service_type': overtime_options_by_service_type,
            'formalwear_contracts': contract.formalwear_contracts.all(),
            'formalwear_subtotal': formalwear_subtotal,
            'product_subtotal': product_subtotal,
            'tax_rate': tax_rate_percentage,
            'tax_amount': tax_amount,
            'product_subtotal_with_tax': product_subtotal_with_tax,
            'service_fees': contract.servicefees.all(),
            'service_fees_total': contract.calculate_total_service_fees(),
            'total_service_cost': contract.calculate_total_service_cost(),
            'package_discount': discount_details['package_discount'],
            'sunday_discount': discount_details['sunday_discount'],
            'other_discount_total': discount_details['other_discount_total'],
            'total_discount': discount_details['total_discount'],
            'other_discounts': discount_details['other_discounts'],
            'total_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
            'deposit_due_to_book': deposit_due_to_book,
            'grand_total': contract.calculate_total_cost(),
            'amount_paid': amount_paid,
            'balance_due': balance_due,
            'due_date': due_date.strftime('%B %d, %Y'),
            'photography_discount': service_discounts['photography'],
            'videography_discount': service_discounts['videography'],
            'dj_discount': service_discounts['dj'],
            'photobooth_discount': service_discounts['photobooth'],
            'contract_products': contract_products,
            'photographer_choices': [
                contract.prospect_photographer1,
                contract.prospect_photographer2,
                contract.prospect_photographer3
            ],
            'show_riders': True
        }

        return render(request, 'documents/client_contract_and_rider_agreement.html', context)



def view_rider_agreements(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    rider_agreements = RiderAgreement.objects.filter(contract=contract)
    logo_url = f"{settings.MEDIA_URL}logo/Final_Logo.png"

    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    additional_services_texts = {
        'photography_additional': linebreaks(
            contract.photography_additional.default_text) if contract.photography_additional else None,
        'videography_additional': linebreaks(
            contract.videography_additional.default_text) if contract.videography_additional else None,
        'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
        'photobooth_additional': linebreaks(
            contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
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
