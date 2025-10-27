"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

export default function ContractTabs({ contract }: { contract: any }) {
  const [showMore, setShowMore] = useState(false);
  const c = contract?.client ?? {};

  return (
    <Tabs defaultValue="info" className="mt-6">
      <TabsList className="sticky top-0 z-10" >
        <TabsTrigger value="info">Info</TabsTrigger>
        <TabsTrigger value="client">Client</TabsTrigger>
        <TabsTrigger value="event">Event</TabsTrigger>
        <TabsTrigger value="services">Services</TabsTrigger>
        <TabsTrigger value="financial">Financial</TabsTrigger>
        <TabsTrigger value="docs">Docs</TabsTrigger>
        <TabsTrigger value="tasks">Tasks/Messages</TabsTrigger>
        <TabsTrigger value="changelog">Change Log</TabsTrigger>
      </TabsList>

      {/* Info */}
      <TabsContent value="info">
        <div className="border rounded-b-md p-4 bg-white shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-y-2">
            <p><strong>Location:</strong> {contract.location?.name ?? "—"}</p>
            <p><strong>Lead Source:</strong> Venue Referral</p>
            <p><strong>Event Date:</strong> {contract.event_date ?? "—"}</p>
            <p><strong>Code 92:</strong> No</p>
            <p><strong>Status:</strong> {contract.status}</p>
            <p><strong>Old Contract Number:</strong> None</p>
            <p><strong>Sales Person:</strong> {contract.csr?.name ?? "—"}</p>
            <p><strong>Coordinator:</strong> Sean Hack</p>
          </div>
          <div className="mt-4 flex gap-2">
            <a
              href={`${process.env.NEXT_PUBLIC_BACKEND_ORIGIN}/contracts/${contract.id}/edit/`} // adjust if your legacy URL differs
              className="px-3 py-1 bg-rose-500 text-white text-sm rounded-md hover:bg-rose-600"
            >
              Edit Contract Info
            </a>
            <button className="px-3 py-1 bg-blue-500 text-white text-sm rounded-md hover:bg-blue-600">
              Add/Edit Special Terms
            </button>
          </div>
        </div>
      </TabsContent>

      {/* Client (legacy layout parity) */}
      <TabsContent value="client">
        <div className="border rounded-b-md p-4 bg-white shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Column 1 */}
            <div className="space-y-2">
              <LabelValue label="Primary Contact" value={c.primary_contact} />
              <LabelValue label="Primary Email" value={c.email} />
              <LabelValue label="Primary Phone 1" value={c.phone} />
            </div>
            {/* Column 2 */}
            <div className="space-y-2">
              <LabelValue label="Partner Contact" value={c.partner_contact} />
              <LabelValue label="Partner Email" value={c.partner_email} />
              <LabelValue label="Partner Phone 1" value={c.partner_phone} />
            </div>
          </div>

          {/* Show more */}
          <div className="mt-4">
            <button
              onClick={() => setShowMore((v) => !v)}
              className="px-3 py-1 bg-gray-100 rounded-md border text-sm"
            >
              {showMore ? "Hide" : "Show"} More Client Info
            </button>
            {showMore && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <LabelValue label="Primary Address 1" value={c.primary_address1} />
                  <LabelValue label="Primary Address 2" value={c.primary_address2} />
                  <LabelValue label="City" value={c.city} />
                  <LabelValue label="State" value={c.state} />
                  <LabelValue label="Postal Code" value={c.postal_code} />
                </div>
                <div className="space-y-2">
                  <LabelValue label="Alternative Contact" value={c.alt_contact} />
                  <LabelValue label="Alternative Email" value={c.alt_email} />
                  <LabelValue label="Alternative Phone" value={c.alt_phone} />
                </div>
              </div>
            )}
          </div>

          {/* Link to legacy edit (until v2 writes) */}
          <div className="mt-4">
            <a
              href={`${process.env.NEXT_PUBLIC_BACKEND_ORIGIN}/contracts/${contract.id}/edit/`} // adjust route
              className="px-3 py-1 bg-rose-500 text-white text-sm rounded-md hover:bg-rose-600"
            >
              Save Changes (Legacy)
            </a>
          </div>
        </div>
      </TabsContent>
    </Tabs>
  );
}

function LabelValue({ label, value }: { label: string; value?: string }) {
  return (
    <p>
      <span className="font-semibold">{label}:</span>{" "}
      {value ?? "—"}
    </p>
  );
}
