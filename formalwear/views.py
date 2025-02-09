from django.shortcuts import get_object_or_404
from django.forms import modelformset_factory
from django.http import JsonResponse
from django.template.loader import render_to_string

from formalwear.models import ContractFormalwearProduct, FormalwearProduct
from contracts.models import Contract
from .forms import ContractFormalwearProductForm


def save_formalwear(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    formalwear_products = FormalwearProduct.objects.all()  # ✅ Get all available products

    FormalwearFormset = modelformset_factory(
        ContractFormalwearProduct,
        form=ContractFormalwearProductForm,
        extra=1,
        can_delete=True
    )

    if request.method == "POST":
        formset = FormalwearFormset(request.POST, queryset=ContractFormalwearProduct.objects.filter(contract=contract))

        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.contract = contract
                instance.save()

            for obj in formset.deleted_objects:
                obj.delete()

            # ✅ Make sure this points to the correct template location!
            table_html = render_to_string("contracts/partials/service_tabs/_formalwear_table_partial.html", {
                "formalwear_formset": FormalwearFormset(queryset=ContractFormalwearProduct.objects.filter(contract=contract)),
                "formalwear_products": formalwear_products,
            }, request=request)

            return JsonResponse({"success": True, "table_html": table_html})

        return JsonResponse({"success": False, "errors": formset.errors})

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)
