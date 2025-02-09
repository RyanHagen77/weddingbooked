from django import forms
from django.forms import modelformset_factory
from formalwear.models import ContractFormalwearProduct

class ContractFormalwearProductForm(forms.ModelForm):
    class Meta:
        model = ContractFormalwearProduct
        fields = ['formalwear_product', 'quantity', 'rental_start_date', 'rental_return_date', 'returned']


# Create a formset for multiple formalwear products in a contract
ContractFormalwearProductFormSet = modelformset_factory(
    ContractFormalwearProduct,
    form=ContractFormalwearProductForm,
    extra=1,  # Allow adding new items dynamically
    can_delete=True
)
