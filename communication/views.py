from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from .models import UnifiedCommunication
from contracts.models import Contract
from .forms import TaskForm
from .forms import CommunicationForm  # Assuming you have a form for message input


def post_contract_message(request, contract_id):
    contract = get_object_or_404(Contract, id=contract_id)

    if request.method == 'POST':
        form = CommunicationForm(request.POST)
        if form.is_valid():
            content_type = ContentType.objects.get_for_model(Contract)
            UnifiedCommunication.objects.create(
                content=form.cleaned_data['message'],
                note_type='contract',  # or determine type based on user role or form input
                created_by=request.user,
                content_type=content_type,
                object_id=contract.id
            )
            return redirect('some_view_name')  # Redirect to a relevant page
    else:
        form = CommunicationForm()

    return render(request, 'post_contract_message.html', {'form': form, 'contract': contract})



