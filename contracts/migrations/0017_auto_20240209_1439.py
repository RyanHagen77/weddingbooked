from django.db import migrations

def migrate_package_types(apps, schema_editor):
    Package = apps.get_model('contracts', 'Package')
    ServiceType = apps.get_model('contracts', 'ServiceType')
    for package in Package.objects.all():
        # Assuming `name` in `ServiceType` matches the old `package_type` values
        package_type = ServiceType.objects.filter(name=package.package_type).first()
        if package_type:
            package.package_type_new = package_type
            package.save()

class Migration(migrations.Migration):
    dependencies = [
        ('contracts', '0016_package_package_type_new'),
    ]

    operations = [
        migrations.RunPython(migrate_package_types),
    ]

