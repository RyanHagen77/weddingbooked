from django.db import models


class FormalwearProduct(models.Model):
    RENTAL_TYPE_CHOICES = [
        ('TUXEDO', 'Tuxedo'),
        ('DRESS', 'Dress'),
        ('SHOES', 'Shoes'),
        ('ACCESSORIES', 'Accessories'),
    ]

    name = models.CharField(max_length=100)
    rental_type = models.CharField(max_length=20, choices=RENTAL_TYPE_CHOICES)
    brand = models.CharField(max_length=100, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    rental_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    version_number = models.PositiveIntegerField(default=1, help_text="Version of the product.")

    # 🔹 Keep default text at the product level (applies to all rentals)
    default_text = models.TextField(blank=True, null=True, help_text="Default instructions for rental.")

    # 🔹 Keep rider at the product level (applies to all rentals)
    rider = models.TextField(blank=True, null=True, help_text="Contract-specific rider terms.")


    def save(self, *args, **kwargs):
        """
        Automatically increments version when price or deposit changes.
        """
        if self.pk:
            old_product = FormalwearProduct.objects.get(pk=self.pk)
            if (
                old_product.rental_price != self.rental_price or
                old_product.deposit_amount != self.deposit_amount
            ):
                self.version_number += 1  # Auto-increment version

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - ${self.price}"


class ContractFormalwearProduct(models.Model):
    """
    Represents a formalwear product rental associated with a contract.

    This model links a formalwear product (`FormalwearProduct`) to a contract, capturing details such as
    the rental period, quantity, and return status. This allows the same formalwear item to be tracked
    across multiple contracts with varying rental details.
    """
    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.CASCADE,
        related_name="formalwear_contracts",  # ✅ Make sure this matches what `calculate_formalwear_subtotal` is using
        help_text="The contract associated with this formalwear product rental."
    )
    formalwear_product = models.ForeignKey(
        FormalwearProduct,
        on_delete=models.CASCADE,
        related_name='formalwear_product',
        help_text="The formalwear product being rented within the contract."
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="The number of units of the formalwear product being rented."
    )
    rental_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="The date when the rental period starts for this formalwear product."
    )
    rental_return_date = models.DateField(
        null=True,
        blank=True,
        help_text="The date by which the formalwear product is expected to be returned."
    )
    returned = models.BooleanField(
        default=False,
        help_text="Indicates whether the formalwear product has been returned."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this formalwear product rental was created."
    )

    def __str__(self):
        return f"{self.contract} - {self.formalwear_product} (Qty: {self.quantity})"
