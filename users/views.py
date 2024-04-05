

from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.generic import ListView, CreateView, UpdateView
from contracts.forms import ContractForm  # Import your contract form
from django.views.decorators.http import require_POST
from django.http import HttpResponseNotAllowed, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser
from .forms import OfficeStaffForm
from contracts.models import EventStaffBooking, Contract
from communication.models import Task, UnifiedCommunication
from .forms import TaskForm



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
    customuser = get_object_or_404(CustomUser, pk=pk)
    contract_form = ContractForm()  # Instantiate your contract form
    tasks = Task.objects.filter(assigned_to=request.user).order_by('due_date')
    context = {
        'customuser': customuser,
        'contract_form': contract_form,  # Add the form to the context
        'tasks': tasks
    }
    return render(request, 'users/office_staff_dashboard.html', context)

def task_list(request):
    tasks = Task.objects.filter(assigned_to=request.user).order_by('due_date')
    task_form = TaskForm()
    return render(request, 'users/task_list.html', {'tasks': tasks, 'task_form': task_form})

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
def create_task(request, contract_id=None, note_id=None):
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.sender = request.user

        if contract_id:
            task.contract = get_object_or_404(Contract, id=contract_id)

        if note_id:
            task.note = get_object_or_404(UnifiedCommunication, id=note_id)

        task.save()

        tasks = Task.objects.filter(assigned_to=request.user)  # Adjust the queryset as needed
        task_list_html = render_to_string('users/task_list_snippet.html', {'tasks': tasks})
        return JsonResponse({'success': True, 'task_list_html': task_list_html})
    else:
        return JsonResponse({'success': False, 'errors': form.errors})


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
        tasks = Task.objects.all()  # Apply any necessary filtering based on your requirements
        task_list_html = render_to_string('users/task_list_snippet.html', {'tasks': tasks}, request=request)

        return JsonResponse({'success': True, 'task_list_html': task_list_html})
    else:
        # If the form is not valid, return the form errors
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})


@require_POST
def mark_complete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    task.is_completed = not task.is_completed  # Toggle the completion status
    task.save()

    # Render the updated task list HTML
    tasks = Task.objects.filter(assigned_to=request.user).order_by('due_date')
    task_list_html = render_to_string('users/task_list_snippet.html', {'tasks': tasks})

    return JsonResponse({'success': True, 'task_list_html': task_list_html})
class OfficeStaffCreateView(CreateView):
    model = CustomUser
    form_class = OfficeStaffForm
    template_name = 'office_staff_form.html'


class OfficeStaffUpdateView(UpdateView):
    model = CustomUser
    form_class = OfficeStaffForm
    template_name = 'office_staff_form.html'


def event_staff_dashboard(request, pk):
    customuser = get_object_or_404(CustomUser, pk=pk)

    if request.method == 'POST':
        content = request.POST.get('content')
        booking_id = request.POST.get('booking_id')

        if booking_id:
            booking = EventStaffBooking.objects.get(pk=booking_id)
            new_note = Note.objects.create(content=content, booking=booking, created_by=request.user)

            return JsonResponse({
                'success': True,
                'note_id': new_note.id,
                'author': request.user.username,
                'timestamp': new_note.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid booking_id'})

    bookings = EventStaffBooking.objects.filter(staff=customuser).exclude(status='DECLINED')

    context = {
        'CustomUser': CustomUser,
        'bookings': bookings,
    }
    return render(request, 'users/event_staff_dashboard.html', context)

@login_required
def profile_redirect(request):
    return redirect('users:event_staff_dashboard', pk=request.user.pk)


def approve_booking(request, pk):
    booking = get_object_or_404(EventStaffBooking, pk=pk)
    if request.method == 'POST':
        booking.status = 'APPROVED'
        booking.confirmed = True  # set confirmed to True when the booking is approved
        booking.save()
        return redirect('users:event_staff_profile', pk=request.user.pk)
    return HttpResponseNotAllowed(['POST'])


def decline_booking(request, pk):
    booking = get_object_or_404(EventStaffBooking, pk=pk)
    if request.method == 'POST':
        booking.status = 'DECLINED'
        booking.save()
    return redirect('users:event_staff_profile', pk=booking.staff.pk)

def financial_reports(request):
    # Dummy data for demonstration purposes
    financial_reports = [
        {'title': 'Catering Expenses', 'date': '2024-03-20', 'amount': 1500, 'description': 'Payment for catering services'},
        {'title': 'Venue Rental', 'date': '2024-03-15', 'amount': 3000, 'description': 'Rental fee for wedding venue'},
        # Add more reports as needed
    ]

    context = {
        'financial_reports': financial_reports,
    }

    return render(request, 'users/financial_reports.html', context)