import json
import logging

from .models import AdditionalProduct, ContractProduct
from contracts.models import Contract
from .forms import ContractProductFormset
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# Set up logging
logger = logging.getLogger(__name__)

def get_additional_products(request):
    """
    Fetches a list of active additional products and returns them as JSON.

    This function retrieves all active products from the `AdditionalProduct` model
    and serializes the relevant fields to be consumed by the frontend or other APIs.

    Returns:
        JsonResponse: A JSON response containing a list of additional products.
    """
    try:
        # Fetch only active products
        products = AdditionalProduct.objects.filter(is_active=True).values(
            'id', 'name', 'price', 'description', 'is_taxable', 'notes'
        )
        logger.info(f"Fetched {len(products)} active additional products successfully.")
        return JsonResponse(list(products), safe=False)
    except Exception as e:
        # Log the error and return a fail response
        logger.error(f"Error fetching additional products: {e}", exc_info=True)
        return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

@login_required
def save_products(request, id):
    """
    Saves the products associated with a contract.

    Handles both JSON-based and formset-based submissions to update the `ContractProduct` objects
    linked to a specific `Contract`. If products are sent via JSON, the function validates and updates
    the products and recalculates the tax for the contract.

    Args:
        request: The HTTP request object.
        id (int): The primary key of the contract to update.

    Returns:
        JsonResponse or HttpResponseRedirect: A JSON response for AJAX requests or a redirect for form submissions.
    """
    contract = get_object_or_404(Contract, pk=id)
    logger.info(f"Handling save_products request for contract ID {id}.")

    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                products = data.get('products', [])

                logger.info(f"Received JSON payload: {data}")

                # Clear existing products
                contract.contract_products.all().delete()
                logger.info("Cleared existing contract products.")

                # Add updated products
                for product_data in products:
                    product_id = product_data['product_id']
                    quantity = product_data['quantity']
                    product = AdditionalProduct.objects.get(id=product_id)

                    # Determine if the product is added post-event
                    post_event = now().date() > contract.event_date

                    # Create the ContractProduct with the post_event flag
                    ContractProduct.objects.create(
                        contract=contract,
                        product=product,
                        quantity=quantity,
                        post_event=post_event  # Set the post_event flag
                    )

                logger.info(f"Updated contract products for contract ID {id}.")

                # Recalculate the tax
                tax_amount = contract.calculate_tax()
                contract.tax_amount = tax_amount
                contract.save()

                logger.info(f"Tax recalculated and saved: {tax_amount}")
                return JsonResponse({'status': 'success', 'tax_amount': tax_amount})

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON data: {e}")
                return JsonResponse({'status': 'fail', 'error': 'Invalid JSON data', 'details': str(e)}, status=400)
            except AdditionalProduct.DoesNotExist as e:
                logger.error(f"Product not found: {e}")
                return JsonResponse({'status': 'fail', 'error': 'Product not found', 'details': str(e)}, status=400)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return JsonResponse({'status': 'fail', 'error': 'An unexpected error occurred', 'details': str(e)}, status=500)
        else:
            # Handle formset submissions
            logger.info("Handling formset submission.")
            product_formset = ContractProductFormset(request.POST, instance=contract, prefix='contract_products')
            if product_formset.is_valid():
                product_formset.save()
                logger.info("Formset saved successfully.")
                return redirect(reverse('contracts:contract_detail', kwargs={'id': contract.contract_id}) + '#products')
            else:
                logger.warning("Formset validation failed.")
                context = {
                    'contract': contract,
                    'product_formset': product_formset,
                }
                return render(request, 'contracts/contract_detail.html', context)
    else:
        # Handle GET requests
        logger.info(f"Rendering product formset for contract ID {id}.")
        product_formset = ContractProductFormset(instance=contract, prefix='contract_products')
        context = {
            'contract': contract,
            'product_formset': product_formset,
        }
        return render(request, 'contracts/contract_detail.html', context)

