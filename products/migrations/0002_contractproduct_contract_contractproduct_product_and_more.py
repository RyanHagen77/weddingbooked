from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0011_contract_amount_paid_field_and_more'),  # Ensure this references the latest contracts migration
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractproduct',
            name='contract',
            field=models.ForeignKey(on_delete=models.CASCADE, to='contracts.Contract', related_name='contract_products'),
        ),
        migrations.AddField(
            model_name='contractproduct',
            name='product',
            field=models.ForeignKey(on_delete=models.CASCADE, to='products.AdditionalProduct', related_name='product_contracts'),
        ),
    ]
