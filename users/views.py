
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from django.conf import settings
from django.template.loader import render_to_string
from django.views.generic import ListView, CreateView, UpdateView
from contracts.forms import ContractForm  # Import your contract form
from django.views.decorators.http import require_POST
from django.http import HttpResponseNotAllowed, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser, Role
from .forms import OfficeStaffForm, TaskForm
from contracts.models import EventStaffBooking, Availability
from communication.views import send_task_assignment_email
from communication.models import Task
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db import transaction
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods
import json

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

class OfficeStaffListView(ListView):
    model = CustomUser
    template_name = 'office_staff_list.html'
    queryset = CustomUser.objects.filter(role__name__in=['MANAGER', 'SALES_PERSON'])


@login_required
def office_staff_dashboard(request, pk):
    staff_member = get_object_or_404(CustomUser, pk=pk)
    # Fetch both completed and incomplete tasks
    incomplete_tasks = Task.objects.filter(assigned_to=request.user, is_completed=False).order_by('due_date')
    completed_tasks = Task.objects.filter(assigned_to=request.user, is_completed=True).order_by('due_date')

    task_form = TaskForm()  # Instantiate your task form
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    context = {
        'staff_member': staff_member,
        'contract_form': ContractForm(),  # Add the contract form to the context if needed
        'incomplete_tasks': incomplete_tasks,
        'completed_tasks': completed_tasks,
        'task_form': task_form,
        'logo_url': logo_url
    }
    return render(request, 'users/office_staff_dashboard.html', context)


@login_required
def task_list(request):
    # Fetch both completed and incomplete tasks
    incomplete_tasks = Task.objects.filter(assigned_to=request.user, is_completed=False).order_by('due_date')
    completed_tasks = Task.objects.filter(assigned_to=request.user, is_completed=True).order_by('due_date')

    task_form = TaskForm()
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    return render(request, 'users/task_list.html', {
        'incomplete_tasks': incomplete_tasks,
        'completed_tasks': completed_tasks,
        'task_form': task_form,
        'logo_url': logo_url
    })

@login_required
def open_task_form(request, contract_id=None, note_id=None):
    initial_data = {
        'sender': request.user.id,
        'contract': contract_id,
        'note': note_id,
    }
    form = TaskForm(initial=initial_data)
    return render(request, 'task_form.html', {'form': form})


@login_required
@require_POST
def create_internal_task(request):
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.sender = request.user
        task.type = 'internal'
        task.save()

        if hasattr(task.assigned_to, 'email') and task.assigned_to.email:
            send_task_assignment_email(request, task)

        incomplete_tasks = Task.objects.filter(
            assigned_to=request.user, type='internal', is_completed=False
        ).order_by('due_date')

        completed_tasks = Task.objects.filter(
            assigned_to=request.user, type='internal', is_completed=True
        ).order_by('due_date')

        task_list_html = render_to_string(
            'users/internal_task_list_snippet.html',
            {'incomplete_tasks': incomplete_tasks, 'completed_tasks': completed_tasks},
            request=request
        )
        return JsonResponse({'success': True, 'task_id': task.id, 'task_list_html': task_list_html})
    else:
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})

@login_required
def get_internal_tasks(request):
    tasks = Task.objects.filter(
        assigned_to=request.user, type='internal', is_completed=False
    ).order_by('due_date')
    task_list_html = render_to_string('users/internal_task_list_snippet.html', {'tasks': tasks}, request=request)
    return JsonResponse({'task_list_html': task_list_html})

@login_required
def task_list(request):
    incomplete_tasks = Task.objects.filter(assigned_to=request.user, is_completed=False).order_by('due_date')
    completed_tasks = Task.objects.filter(assigned_to=request.user, is_completed=True).order_by('due_date')
    task_form = TaskForm()
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    return render(request, 'users/task_list.html', {
        'incomplete_tasks': incomplete_tasks,
        'completed_tasks': completed_tasks,
        'task_form': task_form,
        'logo_url': logo_url
    })

@login_required
@require_POST
def update_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    form = TaskForm(request.POST, instance=task)
    if form.is_valid():
        task = form.save(commit=False)  # Save the form data to the task object but don't commit to the database yet
        task.sender = request.user  # Explicitly set the sender to the current user
        task.save()  # Now save the task to the database with all fields including sender

        # After saving the task, fetch the updated list of tasks and render it to HTML
        incomplete_tasks = Task.objects.filter(assigned_to=request.user, is_completed=False).order_by('due_date')
        completed_tasks = Task.objects.filter(assigned_to=request.user, is_completed=True).order_by('due_date')
        task_list_html = render_to_string('users/internal_task_list_snippet.html', {
            'incomplete_tasks': incomplete_tasks,
            'completed_tasks': completed_tasks
        }, request=request)

        return JsonResponse({'success': True, 'task_list_html': task_list_html})
    else:
        # If the form is not valid, return the form errors
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})

@login_required
@require_POST
def mark_complete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    task.is_completed = not task.is_completed
    task.save()

    incomplete_tasks = Task.objects.filter(assigned_to=request.user, is_completed=False).order_by('due_date')
    completed_tasks = Task.objects.filter(assigned_to=request.user, is_completed=True).order_by('due_date')
    task_list_html = render_to_string('users/internal_task_list_snippet.html', {
        'incomplete_tasks': incomplete_tasks,
        'completed_tasks': completed_tasks
    }, request=request)

    return JsonResponse({'success': True, 'task_list_html': task_list_html})

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
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"


    # Fetch bookings for the staff member that are either approved or confirmed
    bookings = EventStaffBooking.objects.filter(
        staff=staff_member
    ).filter(
        Q(status='APPROVED') | Q(confirmed=True)
    )

    context = {
        'staff_member': staff_member,
        'bookings': bookings,
        'logo_url': logo_url
    }

    return render(request, 'users/event_staff_dashboard.html', context)

def event_staff(request):
    # Get role from request parameters or default to 'PHOTOGRAPHER'
    role_name = request.GET.get('role', 'PHOTOGRAPHER')
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"


    # Fetch staff members sorted by their 'rank' attribute for the selected role
    staff_members = CustomUser.objects.filter(
        Q(role__name=role_name) | Q(additional_roles__name=role_name),
        status='ACTIVE'
    ).distinct().order_by('rank')  # Use 'distinct' to avoid duplicates when a staff has multiple roles

    staff_with_days_off = []
    for staff in staff_members:
        days_off_count = Availability.objects.filter(
            staff=staff,
            available=False
        ).count()
        staff_with_days_off.append({
            'staff': staff,
            'days_off_count': days_off_count
        })

    roles = Role.objects.filter(name__in=[Role.PHOTOGRAPHER, Role.VIDEOGRAPHER, Role.DJ, Role.PHOTOBOOTH_OPERATOR])
    return render(request, 'users/event_staff.html', {
        'staff_list': staff_with_days_off,
        'roles': roles,
        'current_role': role_name,
        'logo_url': logo_url
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

def event_staff_schedule(request, user_id):
    staff_member = CustomUser.objects.get(id=user_id)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Assume we have a model or method to fetch scheduled days off or events
    days_off = Availability.objects.filter(staff=staff_member, available=False).values_list('date', flat=True)
    return render(request, 'users/event_staff_schedule.html', {
        'staff_member': staff_member,
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

    bookings = EventStaffBooking.objects.filter(**query_filters)
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
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Fetch scheduled days off
    days_off = Availability.objects.filter(staff=staff_member, available=False).values_list('date', flat=True)
    return render(request, 'users/event_staff_schedule_read_only.html', {
        'staff_member': staff_member,  # Pass the staff_member object with the name staff_member
        'days_off': days_off,
        'user_id': user_id,  # Pass the user_id to the template context
        'logo_url': logo_url
    })

