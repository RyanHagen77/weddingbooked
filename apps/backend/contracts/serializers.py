from rest_framework import serializers
from contracts.models import Contract, Location, ServiceFee
from users.models import CustomUser

# --- Existing serializer (keep it) ---
class ContractSerializer(serializers.ModelSerializer):
    primary_contact = serializers.CharField(source='client.primary_contact', read_only=True)
    primary_email = serializers.EmailField(source='client.primary_email', read_only=True)
    primary_phone = serializers.CharField(source='client.primary_phone1', read_only=True)
    partner_contact = serializers.CharField(source='client.partner_contact', read_only=True)
    partner_email = serializers.EmailField(source='client.partner_email', read_only=True)
    partner_phone = serializers.CharField(source='client.partner_phone1', read_only=True)

    class Meta:
        model = Contract
        fields = [
            'event_date',
            'primary_contact',
            'primary_email',
            'primary_phone',
            'partner_contact',
            'partner_email',
            'partner_phone',
            'ceremony_site',
            'reception_site',
        ]


# --- New DRF API serializer for React Contract Detail ---
class BasicUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ("id", "name")

    def get_name(self, obj):
        return obj.get_full_name() or f"{obj.first_name} {obj.last_name}".strip()


class BasicLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "name")


class ContractCoreSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="contract_id", read_only=True)
    location = BasicLocationSerializer()
    client = serializers.SerializerMethodField()
    csr = BasicUserSerializer()
    services = serializers.SerializerMethodField()
    sites = serializers.SerializerMethodField()
    staffing = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id",
            "custom_contract_number",
            "status",
            "contract_date",
            "event_date",
            "location",
            "client",
            "csr",
            "services",
            "sites",
            "staffing",
        ]

    def get_client(self, obj):
        c = obj.client
        if not c:
            return None
        return {
            "id": c.id,
            "primary_contact": c.primary_contact,
            "email": c.primary_email,
            "phone": c.primary_phone1,
        }

    def get_services(self, obj):
        return {
            "photography": bool(obj.photography_package_id),
            "videography": bool(obj.videography_package_id),
            "dj": bool(obj.dj_package_id),
            "photobooth": bool(obj.photobooth_package_id),
        }

    def get_sites(self, obj):
        return {
            "ceremony": getattr(obj, "ceremony_site", ""),
            "reception": getattr(obj, "reception_site", ""),
        }

    def get_staffing(self, obj):
        staffing_data = {}
        staff_roles = {
            "photography": ["PHOTOGRAPHER1", "PHOTOGRAPHER2"],
            "videography": ["VIDEOGRAPHER1", "VIDEOGRAPHER2"],
            "dj": ["DJ1", "DJ2"],
            "photobooth": ["PHOTOBOOTH_OP1", "PHOTOBOOTH_OP2"],
        }

        for service, roles in staff_roles.items():
            bookings = obj.eventstaffbooking_set.filter(role__in=roles).select_related("staff")
            staffing_data[service] = [
                {"id": b.staff.id, "name": b.staff.get_full_name() or str(b.staff)}
                for b in bookings if b.staff
            ]
        return staffing_data


# --- Service Fee serializer stays as-is ---
class ServiceFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFee
        fields = ['applied_date', 'description', 'fee_type', 'amount']
