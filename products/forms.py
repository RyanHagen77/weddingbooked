from django import forms
from django.forms import inlineformset_factory
from .models import ContractProduct, AdditionalProduct
from contracts.models import Contract


class ContractProductForm(forms.ModelForm):
    """
    A form for managing individual ContractProduct instances.

    This form allows users to:
    - Select a product from a dropdown (`product`).
    - Specify the quantity of the selected product (`quantity`).
    - Add any special notes for the product (`special_notes`).
    - Indicate if the product was added post-event (`post_event`).

    Attributes:
        Meta:
            model: The model linked to this form is `ContractProduct`.
            fields: Specifies the fields to be displayed in the form.
            widgets: Adds custom styling (via `form-control` classes) to the fields.
    """
    class Meta:
        model = ContractProduct
        fields = ['product', 'quantity', 'special_notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'special_notes': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and filter the product dropdown to include only active products.
        """
        super().__init__(*args, **kwargs)
        # Filter products to only include active ones
        self.fields['product'].queryset = AdditionalProduct.objects.filter(is_active=True)

    def get_product_description(self):
        """
        Retrieve the description of the product linked to the current form instance.

        Returns:
            str: The product description if available, otherwise a default message.
        """
        if self.instance and self.instance.product:
            return self.instance.product.description
        return "No description provided"

# Create an inline formset for managing ContractProduct instances linked to a Contract


ContractProductFormset = inlineformset_factory(
    Contract,  # Parent model
    ContractProduct,  # Child model
    fields=('product', 'quantity', 'special_notes'),
    extra=0,  # Do not display empty forms for additional ContractProduct entries
    can_delete=True  # Allow deletion of ContractProduct entries
)
