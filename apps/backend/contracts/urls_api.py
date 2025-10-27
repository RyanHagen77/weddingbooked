# apps/backend/contracts/urls_api.py
from django.urls import path
from .views.api_meta import contracts_meta
from .views.api_new_contract import new_contract
from .views.api_search import search_contracts
from apps.backend.contracts.views.api_contract_detail import ContractDetailAPIView


urlpatterns = [
    path("search/", search_contracts, name="contracts-search"),
    path("meta/", contracts_meta, name="contracts-meta"),
    path("new/", new_contract, name="contracts_new"),
    path("<int:contract_id>/", ContractDetailAPIView.as_view(), name="contracts-detail"),

]
