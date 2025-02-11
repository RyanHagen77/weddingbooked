import json
import logging
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from contracts.models import Contract
from .models import FormalwearProduct, ContractFormalwearProduct
from .forms import ContractFormalwearProductFormset
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


def get_formalwear_products(request):
    """
    Fetches a list of active formalwear products and returns them as JSON.

    This function retrieves all active products from the FormalwearProduct model
    and serializes the relevant fields to be consumed by the frontend or other APIs.

    Returns:
        JsonResponse: A JSON response containing a list of formalwear products.
    """
    try:
        # Fetch only active formalwear products (assuming you have an is_active field)
        products = FormalwearProduct.objects.filter(is_active=True).values(
            'id', 'name', 'rental_price', 'deposit_amount', 'size'
        )
        logger.info(f"Fetched {len(products)} active formalwear products successfully.")
        return JsonResponse(list(products), safe=False)
    except Exception as e:
        logger.error(f"Error fetching formalwear products: {e}", exc_info=True)
        return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)


@login_required
def save_formalwear(request, id):
    contract = get_object_or_404(Contract, pk=id)
    logger.info(f"Handling save_formalwear request for contract ID {id}.")

    if request.method == "POST":
        if request.content_type.startswith("application/json"):
            try:
                data = json.loads(request.body)
                formalwear_items = data.get("formalwear_items", [])
                logger.info(f"Received formalwear JSON payload: {data}")

                # Build a set of IDs submitted.
                submitted_ids = set()
                for item in formalwear_items:
                    item_id = item.get("id")
                    if item_id and str(item_id).strip():
                        submitted_ids.add(str(item_id))

                # Optionally, delete existing items that are not in the payload.
                existing_items = contract.formalwear_contracts.all()
                for existing in existing_items:
                    if str(existing.pk) not in submitted_ids:
                        logger.info(f"Deleting item with id {existing.pk} not present in payload.")
                        existing.delete()

                for item in formalwear_items:
                    item_id = item.get("id")
                    product_id = item.get("product_id")
                    quantity = item.get("quantity", 1)
                    rental_return_date = item.get("rental_return_date")
                    if not rental_return_date or rental_return_date.strip() == "":
                        rental_return_date = None

                    try:
                        product = FormalwearProduct.objects.get(id=product_id)
                    except FormalwearProduct.DoesNotExist:
                        logger.error(f"Formalwear product with id {product_id} not found.")
                        return JsonResponse({
                            "status": "fail",
                            "error": "Formalwear product not found",
                            "details": f"Product with id {product_id} not found"
                        }, status=400)

                    if item_id and str(item_id).strip():
                        # Update existing record.
                        try:
                            obj = ContractFormalwearProduct.objects.get(pk=item_id, contract=contract)
                            obj.formalwear_product = product
                            obj.quantity = quantity
                            obj.rental_return_date = rental_return_date
                            obj.save()
                            logger.info(f"Updated item with id {item_id}.")
                        except ContractFormalwearProduct.DoesNotExist:
                            # If not found, create a new record.
                            ContractFormalwearProduct.objects.create(
                                contract=contract,
                                formalwear_product=product,
                                quantity=quantity,
                                rental_return_date=rental_return_date,
                            )
                            logger.info(f"Created new item (fallback) for product id {product_id}.")
                    else:
                        # Create new record.
                        ContractFormalwearProduct.objects.create(
                            contract=contract,
                            formalwear_product=product,
                            quantity=quantity,
                            rental_return_date=rental_return_date,
                        )
                        logger.info(f"Created new item for product id {product_id}.")

                logger.info(f"Processed formalwear items for contract ID {id}.")
                # (Optional) Re-render the updated table partial.
                qs = ContractFormalwearProduct.objects.filter(contract=contract)
                formset = ContractFormalwearProductFormset(queryset=qs, prefix='formalwear')
                table_html = render_to_string(
                    "contracts/partials/service_tabs/_formalwear.html",
                    {"contract": contract, "formalwear_formset": formset},
                    request=request
                )
                return JsonResponse({"status": "success", "table_html": table_html})

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON data: {e}")
                return JsonResponse({
                    "status": "fail",
                    "error": "Invalid JSON data",
                    "details": str(e)
                }, status=400)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return JsonResponse({
                    "status": "fail",
                    "error": "An unexpected error occurred",
                    "details": str(e)
                }, status=500)

        # --- Formset-based (standard POST) submission ---
        else:
            logger.info("Handling formset submission for formalwear.")
            formalwear_product_formset = ContractFormalwearProductFormset(
                request.POST,
                queryset=ContractFormalwearProduct.objects.filter(contract=contract),
                prefix='formalwear'
            )
            if formalwear_product_formset.is_valid():
                formalwear_product_formset.save()
                logger.info("Formalwear formset saved successfully.")
                return redirect(
                    reverse('contracts:contract_detail', kwargs={'id': contract.contract_id}) + '#formalwear'
                )
            else:
                logger.warning("Formalwear formset validation failed: %s", formalwear_product_formset.errors)
                context = {
                    'contract': contract,
                    'formalwear_product_formset': formalwear_product_formset,
                }
                return render(request, 'contracts/contract_detail.html', context)

    else:
        qs = ContractFormalwearProduct.objects.filter(contract=contract)
        if not qs.exists():
            qs = ContractFormalwearProduct.objects.none()
        formalwear_product_formset = ContractFormalwearProductFormset(queryset=qs, prefix='formalwear')
        context = {
            'contract': contract,
            'formalwear_product_formset': formalwear_product_formset,
        }
        return render(request, 'contracts/contract_detail.html', context)
