from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0002_contractproduct_contract_contractproduct_product_and_more'),  # Correct dependency
        ('contracts', '0011_contract_amount_paid_field_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='additional_products',
            field=models.ManyToManyField(related_name='contracts', through='products.ContractProduct', to='products.AdditionalProduct'),
        ),
        migrations.RemoveField(
            model_name='contractproduct',
            name='contract',
        ),
        migrations.RemoveField(
            model_name='contractproduct',
            name='product',
        ),
        migrations.DeleteModel(
            name='ContractProduct',
        ),
        migrations.DeleteModel(
            name='AdditionalProduct',
        ),
    ]
