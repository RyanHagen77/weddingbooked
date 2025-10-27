"use client";
import NewContractForm from "@/components/contract/NewContractForm"; // rename if you place it elsewhere
import SidebarShell from "@/components/layout/SidebarShell";

export default function Page() {
  return (
    <SidebarShell>
    <div className="p-6">
      <NewContractForm postUrl="/contracts/new/" />
    </div>
    </SidebarShell>

  );
}
