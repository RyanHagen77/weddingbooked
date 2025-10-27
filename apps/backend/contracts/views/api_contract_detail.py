from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from contracts.models import Contract
from apps.backend.contracts.serializers import ContractCoreSerializer


class ContractDetailAPIView(APIView):
    queryset = Contract.objects.all()  # 👈 add this line

    """
    Core contract payload for /api/contracts/<contract_id>/
    """

    def get(self, request, contract_id):
        contract = get_object_or_404(
            Contract.objects.select_related("client", "location", "csr"),
            contract_id=contract_id
        )
        serializer = ContractCoreSerializer(contract, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
