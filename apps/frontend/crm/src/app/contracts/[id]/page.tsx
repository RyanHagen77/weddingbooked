import SidebarShell from "@/components/layout/SidebarShell";
import ContractTabs from "@/components/contract/ContractTabs";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

export default async function ContractDetailPage({ params }: { params: { id: string } }) {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_BACKEND_ORIGIN}/api/contracts/${params.id}/`,
    { cache: "no-store" }
  );
  if (!res.ok) notFound();
  const contract = await res.json();

  return (
    <SidebarShell>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between bg-gray-100 p-3 rounded-lg shadow-sm">
          <div className="flex items-center gap-4">
            <span className="font-semibold text-gray-700">
              Event Date: {contract.event_date || "—"}
            </span>
            <span className="text-sm text-gray-600">
              Contract ID: {contract.custom_contract_number || "—"}
            </span>
          </div>
          <div className="space-x-4 text-sm">
            <button className="text-blue-600 hover:underline">Print</button>
            <button className="text-blue-600 hover:underline">View</button>
            <button className="text-blue-600 hover:underline">Give Portal Access</button>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border rounded-lg p-4 bg-white shadow-sm">
            <p><strong>Status:</strong> {contract.status}</p>
            <p><strong>Location:</strong> {contract.location?.name || "—"}</p>
            <p><strong>Sales Person:</strong> {contract.csr?.name || "—"}</p>
            <p><strong>Contract Date:</strong> {contract.contract_date || "—"}</p>
          </div>
          <div className="border rounded-lg p-4 bg-white shadow-sm">
            <p><strong>Primary Contact:</strong> {contract.client?.primary_contact || "—"}</p>
            <p><strong>Partner Contact:</strong> {contract.client?.partner_contact || "—"}</p>
            <p><strong>Primary Email:</strong> {contract.client?.email || "—"}</p>
            <p><strong>Primary Phone:</strong> {contract.client?.phone || "—"}</p>
          </div>
          <div className="border rounded-lg p-4 bg-white shadow-sm">
            <p><strong>Next Payment Due:</strong> $0.00</p>
            <p><strong>Due Date:</strong> —</p>
            <p><strong>Balance Due:</strong> $0.00</p>
            <p><strong>Contract Total:</strong> $0.00</p>
          </div>
        </div>

        {/* Tabs & tab content (client component) */}
        <ContractTabs contract={contract} />
      </div>
    </SidebarShell>
  );
}
