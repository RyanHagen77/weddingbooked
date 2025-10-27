// ***REMOVED***ts-due/page.tsx
"use client";

import { useEffect, useMemo, useState } from "react";

type Row = {
  event_date: string;
  amount_due: number;
  date_due: string;
  primary_contact: string;
  primary_phone1: string;
  custom_contract_number: string | null;
  contract_id: number;
};

type ApiResponse = {
  filters: { start_date: string; end_date: string; location: string; page: number; page_size: number; };
  summary: { total_due: number; total_items: number; total_pages: number; };
  locations: { id: number; name: string }[];
  results: Row[];
};

export default function PaymentsDuePage() {
  const today = useMemo(() => new Date(), []);
  const firstOfMonth = useMemo(() => new Date(today.getFullYear(), today.getMonth(), 1), [today]);
  const lastOfMonth  = useMemo(() => new Date(today.getFullYear(), today.getMonth()+1, 0), [today]);

  function fmt(d: Date) { return d.toISOString().slice(0,10); }

  const [startDate, setStartDate] = useState(() => fmt(firstOfMonth));
  const [endDate, setEndDate]     = useState(() => fmt(lastOfMonth));
  const [location, setLocation]   = useState<string>("all");
  const [page, setPage]           = useState(1);

  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    async function run() {
      setLoading(true);
      setErr(null);
      try {
        const params = new URLSearchParams({
          start_date: startDate, end_date: endDate, location, page: String(page), page_size: "50",
        }).toString();
        const res = await fetch(`/api/reports/payments-due?${params}`, { signal: controller.signal, credentials: "include" });
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const json = await res.json() as ApiResponse;
        setData(json);
      } catch (e: any) {
        if (e.name !== "AbortError") setErr(e.message || "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    run();
    return () => controller.abort();
  }, [startDate, endDate, location, page]);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Payments Due</h1>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-slate-500">Start date</label>
          <input type="date" value={startDate} onChange={(e)=>{ setPage(1); setStartDate(e.target.value); }}
                 className="rounded border px-2 py-1" />
        </div>
        <div>
          <label className="block text-xs text-slate-500">End date</label>
          <input type="date" value={endDate} onChange={(e)=>{ setPage(1); setEndDate(e.target.value); }}
                 className="rounded border px-2 py-1" />
        </div>
        <div>
          <label className="block text-xs text-slate-500">Location</label>
          <select value={location} onChange={(e)=>{ setPage(1); setLocation(e.target.value); }}
                  className="rounded border px-2 py-1 min-w-[12rem]">
            <option value="all">All locations</option>
            {data?.locations?.map(loc => (
              <option key={loc.id} value={String(loc.id)}>{loc.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table / state */}
      {loading && <div className="text-sm text-slate-600">Loading…</div>}
      {err && <div className="text-sm text-rose-600">Error: {err}</div>}

      {!loading && data && (
        <>
          <div className="text-sm text-slate-700">
            <strong>Total due:</strong> ${data.summary.total_due.toFixed(2)} ·{" "}
            <strong>Items:</strong> {data.summary.total_items}
          </div>

          <div className="overflow-auto border rounded-xl">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50">
                <tr className="text-left">
                  <th className="p-2">Due Date</th>
                  <th className="p-2">Amount</th>
                  <th className="p-2">Event Date</th>
                  <th className="p-2">Client</th>
                  <th className="p-2">Phone</th>
                  <th className="p-2">Contract</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((r, i) => (
                  <tr key={`${r.contract_id}-${i}`} className="border-t">
                    <td className="p-2">{r.date_due}</td>
                    <td className="p-2">${r.amount_due.toFixed(2)}</td>
                    <td className="p-2">{r.event_date}</td>
                    <td className="p-2">{r.primary_contact}</td>
                    <td className="p-2">{r.primary_phone1}</td>
                    <td className="p-2">
                      <a className="text-rose-600 hover:underline" href={`/contracts/${r.contract_id}/`}>
                        {r.custom_contract_number ?? `#${r.contract_id}`}
                      </a>
                    </td>
                  </tr>
                ))}
                {data.results.length === 0 && (
                  <tr><td className="p-2 text-slate-500" colSpan={6}>No results</td></tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center gap-3">
            <button className="rounded border px-3 py-1 disabled:opacity-50"
                    onClick={()=> setPage(p => Math.max(1, p-1))}
                    disabled={data.filters.page <= 1}>Prev</button>
            <span className="text-sm">
              Page {data.filters.page} of {data.summary.total_pages}
            </span>
            <button className="rounded border px-3 py-1 disabled:opacity-50"
                    onClick={()=> setPage(p => Math.min(data.summary.total_pages, p+1))}
                    disabled={data.filters.page >= data.summary.total_pages}>Next</button>
          </div>
        </>
      )}
    </section>
  );
}
