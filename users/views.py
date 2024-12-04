
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from django.conf import settings
from django.views.generic import ListView, CreateView, UpdateView



from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, get_user_model, login, logout
from .models import CustomUser, Role
from .forms import OfficeStaffForm
from documents.models import ContractAgreement, RiderAgreement
from communication.models import UnifiedCommunication
from communication.forms import TaskForm, CommunicationForm
from communication.views import send_contract_message_email
from contracts.models import Contract, Client
from bookings.models import EventStaffBooking, Availability
from communication.models import Task
from django.db import transaction
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods
import json

from django.contrib import messages

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

import logging

ROLE_DISPLAY_NAMES = {
    'PHOTOGRAPHER1': 'Photographer 1',
    'PHOTOGRAPHER2': 'Photographer 2',
    'VIDEOGRAPHER1': 'Videographer 1',
    'VIDEOGRAPHER2': 'Videographer 2',
    'DJ1': 'DJ 1',
    'DJ2': 'DJ 2',
    'PHOTOBOOTH_OP1': 'Photobooth Operator 1',
    'PHOTOBOOTH_OP2': 'Photobooth Operator 2'
}

def user_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.groups.filter(name='Event Staff').exists():
                return redirect('users:event_staff_dashboard', pk=user.pk)
            elif user.groups.filter(name='Office Staff').exists():
                return redirect('users:office_staff_dashboard', pk=user.pk)


    # Render the login template if the request is not a POST request or if authentication failed
    return render(request, 'users/login.html')

def user_logout_view(request):
    logout(request)
    return redirect('users:login')

def custom_login(request):
    user = get_user_model()  # Use the custom user model

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, 'users/client_portal_login.html', {'next': request.POST.get('next')})
        except User.MultipleObjectsReturned:
            users = User.objects.filter(email=email)
            user = None
            for u in users:
                if u.check_password(password):
                    user = u
                    break
            if user is None:
                messages.error(request, "Invalid email or password.")
                return render(request, 'users/client_portal_login.html', {'next': request.POST.get('next')})

        if user is not None and user.check_password(password):
            login(request, user)
            next_url = request.POST.get('next')
            print(f"Next URL after login: {next_url}")  # Debugging
            if next_url:
                return redirect(next_url)
            else:
                contract = Contract.objects.filter(client=user.client).first()
                if contract:
                    return redirect('users:client_portal', contract_id=contract.contract_id)
                else:
                    messages.error(request, "No associated contract found.")
                    return render(request, 'users/client_portal_login.html', {'next': next_url})
        else:
            messages.error(request, "Invalid email or password.")

    next_url = request.GET.get('next', '')
    print(f"Next URL on GET: {next_url}")  # Debugging
    return render(request, 'users/client_portal_login.html', {'next': next_url})

def custom_logout(request):
    logout(request)
    response = redirect('users:client_portal_login')  # Redirect to the login page or any other page
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        try:
            client = Client.objects.get(user=user)
            contract = Contract.objects.get(client=client)
            token['contract_id'] = contract.contract_id
        except (Client.DoesNotExist, Contract.DoesNotExist):
            token['contract_id'] = None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['contract_id'] = refresh['contract_id']
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@login_required
def client_portal(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)

    # Fetch 'contract' type notes related to this contract
    contract_notes = UnifiedCommunication.objects.filter(
        contract=contract,
        note_type=UnifiedCommunication.PORTAL
    ).order_by('-created_at')

    # Fetch documents visible to the client
    client_documents = contract.documents.filter(is_client_visible=True)

    # Fetch contract agreements and rider agreements
    contract_agreements = ContractAgreement.objects.filter(contract=contract).order_by('-version_number')
    rider_agreements = RiderAgreement.objects.filter(contract=contract)

    if request.method == 'POST':
        form = CommunicationForm(request.POST)
        if form.is_valid():
            message = UnifiedCommunication.objects.create(
                content=form.cleaned_data['message'],
                note_type=UnifiedCommunication.PORTAL,
                created_by=request.user,
                contract=contract
            )

            # Send an email notification to the coordinator
            if contract.coordinator:
                send_contract_message_email(request, message, contract)

            return redirect('users:client_portal', contract_id=contract.contract_id)

    form = CommunicationForm()

    context = {
        'contract': contract,
        'contract_notes': contract_notes,
        'client_documents': client_documents,
        'contract_agreements': contract_agreements,
        'rider_agreements': rider_agreements,
        'form': form,
    }

    return render(request, 'users/client_portal.html', context)

class OfficeStaffListView(ListView):
    model = CustomUser
    template_name = 'office_staff_list.html'
    queryset = CustomUser.objects.filter(role__name__in=['MANAGER', 'SALES_PERSON'])

@login_required
def office_staff_dashboard(request, pk):
    staff_member = get_object_or_404(CustomUser, pk=pk)
    incomplete_tasks = Task.objects.filter(assigned_to=request.user, is_completed=False).order_by('due_date')
    completed_tasks = Task.objects.filter(assigned_to=request.user, is_completed=True).order_by('due_date')

    context = {
        'staff_member': staff_member,
        'incomplete_tasks': incomplete_tasks,
        'completed_tasks': completed_tasks,
        'task_form': TaskForm(),
    }
    return render(request, 'users/office_staff_dashboard.html', context)


class OfficeStaffCreateView(CreateView):
    model = CustomUser
    form_class = OfficeStaffForm
    template_name = 'office_staff_form.html'


class OfficeStaffUpdateView(UpdateView):
    model = CustomUser
    form_class = OfficeStaffForm
    template_name = 'office_staff_form.html'


@login_required
def event_staff_dashboard(request, pk):
    # Retrieve the staff member
    staff_member = get_object_or_404(CustomUser, pk=pk)


    # Fetch bookings for the staff member that are either booked or confirmed
    bookings = EventStaffBooking.objects.filter(
        staff=staff_member
    ).filter(
        Q(status='BOOKED') | Q(confirmed=True)
    )

    context = {
        'staff_member': staff_member,
        'bookings': bookings,
    }

    return render(request, 'users/event_staff_dashboard.html', context)

@login_required
def event_staff(request):
    # Get role from request parameters or default to 'PHOTOGRAPHER'
    role_name = request.GET.get('role', 'PHOTOGRAPHER')

    # Fetch staff members sorted by their 'rank' attribute for the selected role
    staff_members = CustomUser.objects.filter(
        Q(role__name=role_name) | Q(additional_roles__name=role_name),
        status='ACTIVE'
    ).distinct().order_by('rank')  # Use 'distinct' to avoid duplicates when a staff has multiple roles

    staff_with_days_off = []
    for staff in staff_members:
        # Exclude PROSPECT status explicitly when counting bookings
        current_year_bookings = EventStaffBooking.objects.filter(
            staff=staff,
            contract__event_date__year=datetime.now().year,
            status__in=['PENDING', 'BOOKED']  # Exclude PROSPECT
        ).count()

        next_year_bookings = EventStaffBooking.objects.filter(
            staff=staff,
            contract__event_date__year=datetime.now().year + 1,
            status__in=['PENDING', 'BOOKED']  # Exclude PROSPECT
        ).count()

        days_off_count = Availability.objects.filter(
            staff=staff,
            available=False
        ).count()

        # Append only the filtered data
        staff_with_days_off.append({
            'staff': staff,
            'current_year_bookings': current_year_bookings,
            'next_year_bookings': next_year_bookings,
            'days_off_count': days_off_count,
        })

    # Ensure only relevant roles are displayed
    roles = Role.objects.filter(name__in=[Role.PHOTOGRAPHER, Role.VIDEOGRAPHER, Role.DJ, Role.PHOTOBOOTH_OPERATOR])

    # Render the event staff view with filtered data
    return render(request, 'users/event_staff.html', {
        'staff_list': staff_with_days_off,
        'roles': roles,
        'current_role': role_name,
    })


@login_required
@require_http_methods(["POST"])
def update_event_staff_ranking(request):
    try:
        rankings = request.POST.getlist('rankings[]')  # Fetches list of rankings directly
        if rankings:
            # Process each user_id from rankings
            for index, user_id in enumerate(rankings, start=1):
                user = CustomUser.objects.get(id=int(user_id))  # Ensure IDs are integers
                user.rank = index
                user.save()
            return JsonResponse({'status': 'success', 'message': 'Rankings updated successfully!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No rankings provided.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def event_staff_schedule(request, user_id):
    staff_member = CustomUser.objects.get(id=user_id)
    logo_url = f"https://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Fetch bookings, excluding 'PROSPECT' status
    bookings = EventStaffBooking.objects.filter(
        staff=staff_member,
        status__in=['PENDING', 'BOOKED']  # Exclude PROSPECT
    )

    # Fetch days off
    days_off = Availability.objects.filter(staff=staff_member, available=False).values_list('date', flat=True)

    return render(request, 'users/event_staff_schedule.html', {
        'staff_member': staff_member,
        'bookings': bookings,
        'days_off': days_off,
        'logo_url': logo_url
    })


@require_http_methods(["GET"])
def get_event_staff_schedule(request, user_id):
    role_id = request.GET.get('role_id')
    start_date_str = request.GET.get('start', None)
    end_date_str = request.GET.get('end', None)

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        year = request.GET.get('year', datetime.now().year)
        start_date = datetime(int(year), 1, 1)
        end_date = datetime(int(year), 12, 31)

    events = []
    always_off_days_list = []

    query_filters = {
        'staff_id': user_id,
        'contract__event_date__gte': start_date,
        'contract__event_date__lte': end_date,
    }
    if role_id:
        query_filters['staff__role__id'] = role_id

    # Exclude bookings with status 'PROSPECT'
    bookings = EventStaffBooking.objects.filter(**query_filters).exclude(status='PROSPECT')
    booking_dates = set()

    for booking in bookings:
        booking_date_str = booking.contract.event_date.strftime('%Y-%m-%d')
        booking_dates.add(booking_date_str)
        events.append({
            "start": booking_date_str,
            "day": booking.contract.event_date.strftime('%A'),
            "allDay": True,
            "color": "#378006",
            "type": "booking"
        })

    days_off = Availability.objects.filter(
        staff_id=user_id,
        date__gte=start_date,
        date__lte=end_date,
        available=False
    ).exclude(date__in=booking_dates)  # Exclude days that are already booked

    for day in days_off:
        events.append({
            "start": day.date.strftime('%Y-%m-%d'),
            "day": day.date.strftime('%A'),
            "allDay": True,
            "rendering": "background",
            "color": "#ff9f89",
            "type": "day_off"
        })

    try:
        always_off_record = Availability.objects.get(staff_id=user_id, date__isnull=True)
        always_off_days = always_off_record.always_off_days
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in always_off_days:
                current_date_str = current_date.strftime('%Y-%m-%d')
                if current_date_str not in booking_dates:  # Exclude always off days that are already booked
                    always_off_days_list.append(current_date.strftime('%A'))
                    events.append({
                        "start": current_date_str,
                        "day": current_date.strftime('%A'),
                        "allDay": True,
                        "rendering": "background",
                        "color": "#ff0000",
                        "type": "always_off"
                    })
            current_date += timedelta(days=1)
    except Availability.DoesNotExist:
        pass

    sorted_events = sorted(events, key=lambda x: x['start'])
    return JsonResponse({"events": sorted_events, "alwaysOffDays": list(set(always_off_days_list))}, safe=False)

@require_http_methods(["POST"])
def update_specific_date_availability(request, user_id):
    try:
        data = json.loads(request.body)
        date = data.get('date')
        available = data.get('available')

        if date and available is not None:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            available = json.loads(available.lower()) if isinstance(available, str) else available

            with transaction.atomic():
                availability, created = Availability.objects.update_or_create(
                    staff_id=user_id,
                    date=date_obj,
                    defaults={'available': available}
                )
            return JsonResponse({'status': 'success', 'message': 'Day updated successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid or missing data'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["POST"])
def update_always_off_days(request, user_id):
    try:
        data = json.loads(request.body)
        always_off_days = data.get('always_off_days')

        if always_off_days is not None:
            Availability.objects.update_or_create(
                staff_id=user_id,
                date__isnull=True,
                defaults={'always_off_days': always_off_days}
            )
            return JsonResponse({'status': 'success', 'message': 'Always off days updated successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No always off days provided'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def event_staff_schedule_read_only(request, user_id):
    staff_member = CustomUser.objects.get(id=user_id)
    logo_url = f"https://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Fetch scheduled days off
    days_off = Availability.objects.filter(staff=staff_member, available=False).values_list('date', flat=True)
    return render(request, 'users/event_staff_schedule_read_only.html', {
        'staff_member': staff_member,  # Pass the staff_member object with the name staff_member
        'days_off': days_off,
        'user_id': user_id,  # Pass the user_id to the template context
        'logo_url': logo_url
    })


