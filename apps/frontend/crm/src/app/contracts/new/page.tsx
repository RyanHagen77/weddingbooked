"use client";
import NewContractForm from "@/components/NewContractForm"; // rename if you place it elsewhere

export default function Page() {
  return (
    <div className="p-6">
      <NewContractForm postUrl="/contracts/new/" />
    </div>
  );
}
