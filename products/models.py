#products/models.py

from django.db import models

class AdditionalProduct(models.Model):
    """
    Represents a reusable product or service that can be added to multiple contracts.

    This model acts as a product catalog, defining the core details of a product or service,
    such as its name, description, price, taxability, and other default settings. These products
    are not tied to a specific contract but can be linked through the `ContractProduct` model.
    """
    name = models.CharField(max_length=100, help_text="Name of the product or service.")
    description = models.TextField(blank=True, null=True, help_text="Optional description of the product.")
    price = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Price charged to the customer for this product."
    )
    cost = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, help_text="Internal cost of the product."
    )
    is_taxable = models.BooleanField(default=False, help_text="Indicates whether this product is taxable.")
    notes = models.TextField(blank=True, null=True, help_text="Additional internal notes about the product.")
    default_text = models.TextField(
        blank=True,
        help_text="Default text or instructions associated with this product. This can be used for contracts."
    )
    is_active = models.BooleanField(default=True, verbose_name="Active", help_text="Indicates if this product is active.")

    def __str__(self):
        return f"{self.name} - ${self.price}"


class ContractProduct(models.Model):
    """
    Represents a specific product or service added to a contract.

    This model links a product (`AdditionalProduct`) to a contract, allowing for customization of product details
    like quantity and special notes specific to that contract. This enables the same product to be reused across
    multiple contracts with different configurations.
    """
    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.CASCADE,
        related_name='contract_products',
        help_text="The contract to which this product is associated."
    )
    product = models.ForeignKey(
        AdditionalProduct,
        on_delete=models.CASCADE,
        related_name='product_contracts',
        help_text="The product being added to the contract."
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="The quantity of the product being added to the contract."
    )
    special_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional notes or instructions specific to this product within this contract."
    )
    added_on = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this product was added to the contract."
    )

    def get_product_price(self):
        """
        Returns the price of the product from the `AdditionalProduct` model.

        This is useful for calculating totals or displaying product details in the context of a contract.
        """
        return self.product.price

    def __str__(self):
        return f"{self.contract} - {self.product} - Qty: {self.quantity}"
