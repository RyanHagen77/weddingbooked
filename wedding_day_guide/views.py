import logging
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.template.loader import render_to_string
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.response import Response
from rest_framework import status
from weasyprint import HTML

from .forms import WeddingDayGuideForm
from .models import WeddingDayGuide
from contracts.models import Contract
from documents.models import ContractDocument
from .serializers import WeddingDayGuideSerializer

# Initialize logger
logger = logging.getLogger(__name__)


def generate_pdf(guide, contract, logger):
    """
    Helper function to generate PDF from WeddingDayGuide instance.
    """
    try:
        existing_versions = ContractDocument.objects.filter(
            contract=contract,
            document__icontains=f"wedding_day_guide_{guide.pk}_v"
        ).count()
        version_number = existing_versions + 1

        logo_url = f"{settings.MEDIA_URL}logo/Final_Logo.png"
        logger.info("Generating PDF for guide ID: %s with logo URL: %s", guide.pk, logo_url)

        context = {
            'guide': guide,
            'logo_url': logo_url,
        }

        html_string = render_to_string('wedding_day_guide/wedding_day_guide_pdf.html', context)
        pdf_file = HTML(string=html_string).write_pdf()

        pdf_name = f"wedding_day_guide_{guide.pk}_v{version_number}.pdf"
        path = default_storage.save(f"contract_documents/{pdf_name}", ContentFile(pdf_file))

        ContractDocument.objects.create(
            contract=contract,
            document=path,
            is_client_visible=True,
            is_event_staff_visible=True
        )

        logger.info("PDF generated and saved successfully for guide ID: %s, contract ID: %s",
                    guide.pk, contract.contract_id)
    except Exception as e:
        logger.error("Error generating PDF for guide %s: %s", guide.pk, e)
        raise

@login_required
def wedding_day_guide(request, contract_id):
    logger.info("Accessing wedding day guide for contract ID: %s by user: %s", contract_id, request.user)
    is_office_staff = request.user.groups.filter(name='Office Staff').exists()

    try:
        contract = get_object_or_404(Contract, contract_id=contract_id)
        guide = WeddingDayGuide.objects.filter(contract=contract).first()

        if guide and guide.submitted and not is_office_staff:
            logger.warning("Attempt to edit submitted guide by user: %s", request.user)
            return render(request, 'wedding_day_guide/wedding_day_guide_submitted.html', {
                'message': 'This Wedding Day Guide has already been submitted and cannot be edited.',
                'contract': contract,
                'is_office_staff': is_office_staff
            })

        if request.method == 'POST':
            strict_validation = 'submit' in request.POST
            logger.debug("POST data for contract ID %s: %s", contract_id, request.POST)

            # Use WeddingDayGuideForm to validate data, similar to API
            form = WeddingDayGuideForm(
                data=request.POST,
                instance=guide,
                strict_validation=strict_validation,
                contract=contract
            )

            if form.is_valid() or not strict_validation:
                try:
                    # Mimic API's update_or_create logic
                    data = form.cleaned_data if form.is_valid() else request.POST.dict()
                    defaults = {k: v for k, v in data.items() if k in WeddingDayGuide._meta.get_fields() and k != 'contract'}
                    if strict_validation:
                        defaults['submitted'] = True

                    guide, created = WeddingDayGuide.objects.update_or_create(
                        contract=contract,
                        defaults=defaults
                    )

                    logger.info("Guide %s %s for contract ID: %s by user: %s",
                                guide.pk, "created" if created else "updated", contract_id, request.user)

                    if strict_validation:
                        generate_pdf(guide, contract, logger)
                        return redirect(f'/contracts/{contract.contract_id}/#docs')

                    return redirect('wedding_day_guide:wedding_day_guide', contract_id=contract.contract_id)
                except Exception as e:
                    logger.error("Error saving guide for contract ID %s: %s", contract_id, str(e))
                    form.add_error(None, f"Error saving form: {str(e)}")
            else:
                logger.error("Form validation failed for contract ID %s: %s", contract_id, form.errors)

            return render(request, 'wedding_day_guide/wedding_day_guide.html', {
                'form': form,
                'contract': contract,
                'guide': guide,
                'submitted': guide.submitted if guide else False,
                'is_office_staff': is_office_staff,
                'error_message': 'Please correct the errors below.'
            })

        form = WeddingDayGuideForm(instance=guide, strict_validation=False, contract=contract)
        return render(request, 'wedding_day_guide/wedding_day_guide.html', {
            'form': form,
            'contract': contract,
            'guide': guide,
            'submitted': guide.submitted if guide else False,
            'is_office_staff': is_office_staff
        })

    except Contract.DoesNotExist:
        logger.error("Contract not found for contract ID: %s by user: %s", contract_id, request.user)
        return HttpResponse("Contract not found.", status=404)
    except Exception as e:
        logger.error("Unexpected error for contract ID: %s by user: %s - %s", contract_id, request.user, str(e))
        return HttpResponseServerError("An error occurred. Please contact support.")


@login_required
def wedding_day_guide_view(request, pk):
    """
    View a specific Wedding Day Guide in detail.
    """
    logger.info("Accessing wedding day guide view for guide ID: %s by user: %s", pk, request.user)

    try:
        guide = get_object_or_404(WeddingDayGuide, pk=pk, contract__client__user=request.user)
        return render(request, 'wedding_day_guide/wedding_day_guide_view.html', {'guide': guide})
    except WeddingDayGuide.DoesNotExist:
        logger.error("Guide not found for view, ID: %s by user: %s", pk, request.user)
        return HttpResponse("Guide not found.", status=404)
    except Exception as e:
        logger.error("Unexpected error accessing guide ID: %s - %s", pk, e)
        return HttpResponseServerError("An error occurred.")


@login_required
def wedding_day_guide_pdf(request, pk):
    """
    Generate and download a PDF of the Wedding Day Guide.
    """
    try:
        guide = get_object_or_404(WeddingDayGuide, pk=pk, contract__client__user=request.user)
        logo_url = f"{settings.MEDIA_URL}logo/Final_Logo.png"
        logger.info("Rendering PDF for guide ID: %s with logo URL: %s by user: %s", guide.pk, logo_url, request.user)

        html_string = render_to_string('wedding_day_guide_pdf.html', {
            'guide': guide,
            'logo_url': logo_url,
        })
        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="wedding_day_guide_{guide.pk}.pdf"'
        logger.info("PDF downloaded for guide ID: %s by user: %s", guide.pk, request.user)
        return response

    except WeddingDayGuide.DoesNotExist:
        logger.error("Guide not found for ID: %s by user: %s", pk, request.user)
        return HttpResponse("Guide not found.", status=404)
    except Exception as e:
        logger.error("Error generating PDF for guide ID: %s - %s", pk, str(e))
        return HttpResponseServerError("Error generating PDF.")

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def wedding_day_guide_api(request, contract_id):
    """
    API endpoint to manage Wedding Day Guide for a specific contract.
    """
    logger.info("API accessed for wedding day guide, contract ID: %s by user: %s", contract_id, request.user)

    try:
        contract = Contract.objects.get(contract_id=contract_id)

        if request.method == 'GET':
            guide = WeddingDayGuide.objects.filter(contract=contract).first()
            if not guide:
                logger.warning("Guide not found for API GET, contract ID: %s", contract_id)
                return Response({"error": "Guide not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = WeddingDayGuideSerializer(guide)
            return Response(serializer.data)

        elif request.method == 'POST':
            data = request.data.copy()
            data['contract'] = contract.contract_id
            strict_validation_raw = request.data.get('strict_validation', False)
            strict_validation = strict_validation_raw in [True, 'true', 'True', 1, '1']

            serializer = WeddingDayGuideSerializer(data=data, context={'strict_validation': strict_validation})
            if serializer.is_valid():
                guide, created = WeddingDayGuide.objects.update_or_create(
                    contract=contract,
                    defaults=serializer.validated_data
                )
                if strict_validation:
                    guide.submitted = True
                    guide.save()
                    generate_pdf(guide, contract, logger)
                return Response(WeddingDayGuideSerializer(guide).data, status=status.HTTP_201_CREATED)
            else:
                logger.warning("Validation errors for API POST, contract ID: %s - %s", contract_id, serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Contract.DoesNotExist:
        logger.error("Contract not found for API request, contract ID: %s", contract_id)
        return Response({"error": "Contract not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("Unexpected error for API request, contract ID: %s - %s", contract_id, e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
