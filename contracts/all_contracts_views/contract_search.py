# contracts/views.py
import logging

# Django Imports
from django.shortcuts import render,redirect

from django.contrib.auth.decorators import login_required

from django.db.models import Q
from django.core.paginator import Paginator


from contracts.models import Contract


from contracts.forms import (
    ContractSearchForm
)

# Logging setup
logger = logging.getLogger(__name__)

@login_required
def contract_search(request):
    form = ContractSearchForm(request.GET or None)
    contracts = Contract.objects.all()

    # Clear filters if the "clear" flag is in the query string
    if "clear" in request.GET:
        return redirect(request.path)

    # Apply ordering
    order = request.GET.get('order', 'desc')
    contracts = contracts.order_by('event_date' if order == 'asc' else '-event_date')

    # Apply filters if the form is valid
    if form.is_valid():
        if form.cleaned_data.get('location'):
            contracts = contracts.filter(location=form.cleaned_data['location'])
        if form.cleaned_data.get('ceremony_site'):
            contracts = contracts.filter(ceremony_site__icontains=form.cleaned_data['ceremony_site'])
        if form.cleaned_data.get('reception_site'):
            contracts = contracts.filter(reception_site__icontains=form.cleaned_data['reception_site'])

        event_date_start = form.cleaned_data.get('event_date_start')
        event_date_end = form.cleaned_data.get('event_date_end')
        if event_date_start and event_date_end:
            contracts = contracts.filter(event_date__range=[event_date_start, event_date_end])

        contract_date_start = form.cleaned_data.get('contract_date_start')
        contract_date_end = form.cleaned_data.get('contract_date_end')
        if contract_date_start and contract_date_end:
            contracts = contracts.filter(contract_date__range=[contract_date_start, contract_date_end])

        if form.cleaned_data.get('contract_number'):
            contracts = contracts.filter(custom_contract_number__icontains=form.cleaned_data['contract_number'])
        if form.cleaned_data.get('primary_contact'):
            contracts = contracts.filter(client__primary_contact__icontains=form.cleaned_data['primary_contact'])
        if form.cleaned_data.get('status'):
            contracts = contracts.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('csr'):
            contracts = contracts.filter(csr=form.cleaned_data['csr'])

        # Filter by DJs
        if form.cleaned_data.get('dj'):
            contracts = contracts.filter(Q(dj1=form.cleaned_data['dj']) | Q(dj2=form.cleaned_data['dj']))

    # Apply search query
    query = request.GET.get('q')
    if query:
        contracts = contracts.filter(
            Q(custom_contract_number__icontains=query) |
            Q(client__primary_contact__icontains=query) |
            Q(client__partner_contact__icontains=query) |
            Q(old_contract_number__icontains=query) |
            Q(client__primary_email__icontains=query) |
            Q(client__primary_phone1__icontains=query) |
            Q(dj1__get_full_name__icontains=query) |
            Q(dj2__get_full_name__icontains=query)
        )

    # Paginate results
    paginator = Paginator(contracts, 25)
    page_number = request.GET.get('page')
    contracts = paginator.get_page(page_number)

    return render(request, 'contracts/contract_search.html', {
        'form': form,
        'contracts': contracts,
    })