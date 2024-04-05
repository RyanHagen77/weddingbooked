from django.db import migrations

def migrate_event_staff_types(apps, schema_editor):
    AdditionalEventStaffOption = apps.get_model('contracts', 'AdditionalEventStaffOption')
    ServiceType = apps.get_model('contracts', 'ServiceType')
    for event_staff_option in AdditionalEventStaffOption.objects.all():
        # Find the ServiceType instance that matches the old 'type' value
        # Assuming event_staff_option.type is the name of the ServiceType we're looking for
        service_type = ServiceType.objects.filter(name=event_staff_option.type).first()
        if service_type:
            event_staff_option.type = service_type
            event_staff_option.save()

class Migration(migrations.Migration):
    dependencies = [
        ('contracts', '0021_additionaleventstaffoption_service_type'),
    ]

    operations = [
        migrations.RunPython(migrate_event_staff_types),
    ]
