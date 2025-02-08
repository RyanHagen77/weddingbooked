from django.db import models
from django.core.validators import MinValueValidator


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
    is_available = models.BooleanField(default=True)
    version_number = models.PositiveIntegerField(default=1, help_text="Version of the product.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Automatically increments version when price changes.
        """
        if self.pk:
            old_product = FormalwearProduct.objects.get(pk=self.pk)
            if old_product.rental_price != self.rental_price or old_product.deposit_amount != self.deposit_amount:
                self.version_number += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (v{self.version_number}) - {self.get_rental_type_display()} - {self.brand} - {self.size}"


class ContractFormalwearProduct(models.Model):
    contract = models.ForeignKey('contracts.Contract', on_delete=models.CASCADE, related_name="formalwear_contracts")
    formalwear_product = models.ForeignKey('FormalwearProduct', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    rental_start_date = models.DateField()
    rental_return_date = models.DateField()
    returned = models.BooleanField(default=False)

    # Store the version of the product used at the time of contract
    product_version = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        """
        Before saving, ensure the correct version number of the product is stored.
        """
        if not self.product_version:
            self.product_version = self.formalwear_product.version_number
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.formalwear_product.name} (v{self.product_version}) - Qty: {self.quantity} - Contract {self.contract.custom_contract_number}"
