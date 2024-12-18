from django import forms
from django.forms import inlineformset_factory
from .models import ContractProduct, AdditionalProduct
from contracts.models import Contract

ContractProductFormset = inlineformset_factory(
    Contract,  # Parent model
    ContractProduct,  # Child model
    fields=('product', 'quantity', 'special_notes'),  # Removed 'post_event'
    extra=0,  # Do not display empty forms for additional ContractProduct entries
    can_delete=True  # Allow deletion of ContractProduct entries
)


# Create an inline formset for managing ContractProduct instances linked to a Contract
ContractProductFormset = inlineformset_factory(
    Contract,  # Parent model
    ContractProduct,  # Child model
    fields=('product', 'quantity', 'special_notes'),  # Removed 'post_event'
    extra=0,  # Do not display empty forms for additional ContractProduct entries
    can_delete=True  # Allow deletion of ContractProduct entries
)
