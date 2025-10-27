from django.db import migrations, models
from django.db.models import Q

class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0018_rename_bypass_package_discounts_contract_bypass_manual_discounts_and_more"),  # ← update to your latest
    ]

    operations = [
        migrations.AddConstraint(
            model_name="contract",
            constraint=models.CheckConstraint(
                check=Q(tax_rate__gte=0) & Q(tax_rate__lte=100),
                name="contracts_tax_rate_0_100",
            ),
        ),
    ]