from django import forms
from django.forms import inlineformset_factory
from formalwear.models import ContractFormalwearProduct, FormalwearProduct
from contracts.models import Contract


class ContractFormalwearProductForm(forms.ModelForm):
    """
    A form for managing individual ContractFormalwearProduct instances.

    This form allows users to:
      - Select a formalwear product from a dropdown.
      - Specify the quantity.
      - Optionally specify rental start and return dates.
      - Mark the item as returned.

    The form applies Bootstrap styling via the 'form-control' and 'form-check-input' classes.
    """

    class Meta:
        model = ContractFormalwearProduct
        fields = ['formalwear_product', 'quantity', 'rental_start_date', 'rental_return_date', 'returned']
        widgets = {
            'formalwear_product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'rental_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'rental_return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'returned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter the formalwear_product dropdown to only include active products.
        self.fields['formalwear_product'].queryset = FormalwearProduct.objects.filter(is_active=True)
        # Set an empty label so that new forms show a placeholder.
        self.fields['formalwear_product'].empty_label = "---------"


# Create an inline formset for ContractFormalwearProduct instances linked to a Contract.
ContractFormalwearProductFormset = inlineformset_factory(
    Contract,  # Parent model
    ContractFormalwearProduct,  # Child model
    form=ContractFormalwearProductForm,
    fields=('formalwear_product', 'quantity', 'rental_start_date', 'rental_return_date', 'returned'),
    extra=0,  # Display one extra blank form (adjust as needed)
    can_delete=True  # Allow deletion of existing items
)
