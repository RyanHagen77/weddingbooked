# wedding_day_guide/views.py
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from rest_framework import status
from django.template.loader import render_to_string
from weasyprint import HTML
from .forms import WeddingDayGuideForm
from .models import WeddingDayGuide
from contracts.models import Contract, ContractDocument
from .serializers import WeddingDayGuideSerializer
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response





@login_required
def wedding_day_guide(request, contract_id):
    # Check if the user is part of the "Office Staff" group
    is_office_staff = request.user.groups.filter(name='Office Staff').exists()

    if is_office_staff:
        # Office Staff can access any contract
        contract = get_object_or_404(Contract, contract_id=contract_id)
    else:
        # Clients can only access their own contracts
        contract = get_object_or_404(Contract, contract_id=contract_id, client__user=request.user)

    try:
        guide = WeddingDayGuide.objects.get(contract=contract)
    except WeddingDayGuide.DoesNotExist:
        guide = None

    if guide and guide.submitted and not is_office_staff:
        # If the guide has been submitted and the user is not Office Staff, show a message
        return render(request, 'wedding_day_guide/wedding_day_guide_submitted.html', {
            'message': 'This Wedding Day Guide has already been submitted and cannot be edited.',
        })

    if request.method == 'POST':
        strict_validation = 'submit' in request.POST
        form = WeddingDayGuideForm(request.POST, instance=guide, strict_validation=strict_validation, contract=contract)
        if form.is_valid() or not strict_validation:
            guide = form.save(commit=False)
            guide.contract = contract
            if 'submit' in request.POST:
                guide.submitted = True
            guide.save()

            # Generate PDF if submitted
            if 'submit' in request.POST:
                # Determine the version number
                existing_versions = ContractDocument.objects.filter(contract=contract, document__icontains=f"wedding_day_guide_{guide.pk}_v").count()
                version_number = existing_versions + 1

                # Generate the PDF
                context = {
                    'guide': guide,
                }
                html_string = render_to_string('wedding_day_guide/wedding_day_guide_pdf.html', context)
                pdf_file = HTML(string=html_string).write_pdf()

                # Save PDF with versioned filename
                pdf_name = f"wedding_day_guide_{guide.pk}_v{version_number}.pdf"
                path = default_storage.save(f"contract_documents/{pdf_name}", ContentFile(pdf_file))

                ContractDocument.objects.create(
                    contract=contract,
                    document=path,
                    is_client_visible=True,
                )

                # Redirect to the contract page with the documents section
                return redirect(f'/contracts/{contract.contract_id}/#docs')

            return redirect('wedding_day_guide:wedding_day_guide', contract_id=contract.contract_id)
    else:
        form = WeddingDayGuideForm(instance=guide, strict_validation=False, contract=contract)

    return render(request, 'wedding_day_guide/wedding_day_guide.html', {
        'form': form,
        'submitted': guide.submitted if guide else False,
    })


@login_required
def wedding_day_guide_view(request, pk):
    guide = get_object_or_404(WeddingDayGuide, pk=pk, contract__client__user=request.user)
    return render(request, 'wedding_day_guide_view.html', {'guide': guide})


@login_required
def wedding_day_guide_pdf(request, pk):
    guide = get_object_or_404(WeddingDayGuide, pk=pk, contract__client__user=request.user)
    html_string = render_to_string('wedding_day_guide_pdf.html', {'guide': guide})
    html = HTML(string=html_string)

    try:
        pdf = html.write_pdf()
    except Exception as e:
        return HttpResponse(f'Error generating PDF: {e}', status=500)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="wedding_day_guide_{guide.pk}.pdf"'
    return response


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def wedding_day_guide_api(request, contract_id):
    try:
        contract = Contract.objects.get(contract_id=contract_id)

        if request.method == 'GET':
            try:
                guide = WeddingDayGuide.objects.get(contract_id=contract_id)
            except WeddingDayGuide.DoesNotExist:
                return Response({"error": "Guide not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = WeddingDayGuideSerializer(guide)
            return Response(serializer.data)

        elif request.method == 'POST':
            data = request.data.copy()
            data['contract'] = contract.contract_id  # Ensure the contract is correctly set

            # Determine if this is a submit action (strict validation)
            strict_validation = request.data.get('strict_validation', False)

            serializer = WeddingDayGuideSerializer(data=data, context={'strict_validation': strict_validation})
            if serializer.is_valid():
                guide, created = WeddingDayGuide.objects.update_or_create(
                    contract=contract,
                    defaults=serializer.validated_data
                )

                # Mark the guide as submitted if strict_validation is True (i.e., the form was submitted)
                if strict_validation:
                    guide.submitted = True
                    guide.save()

                return Response(WeddingDayGuideSerializer(guide).data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Contract.DoesNotExist:
        return Response({"error": "Contract not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)