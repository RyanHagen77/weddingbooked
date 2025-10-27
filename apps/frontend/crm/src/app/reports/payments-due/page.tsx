// apps/frontend/crm/src/app/reports/payments-due/page.tsx
"use client";

import { useEffect, useMemo, useState, useRef } from "react";

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
  filters: { start_date: string; end_date: string; location: string; page: number; page_size: number };
  summary: { total_due: number; total_items: number; total_pages: number };
  locations: { id: number; name: string }[];
  results: Row[];
};

const usd = new Intl.NumberFormat(undefined, { style: "currency", currency: "USD", minimumFractionDigits: 2 });

function ymd(d: Date) {
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

export default function PaymentsDuePage() {
  const todayRef = useRef(new Date());
  const firstOfMonth = useMemo(
    () => new Date(todayRef.current.getFullYear(), todayRef.current.getMonth(), 1),
    []
  );
  const lastOfMonth = useMemo(
    () => new Date(todayRef.current.getFullYear(), todayRef.current.getMonth() + 1, 0),
    []
  );

  const [startDate, setStartDate] = useState(() => ymd(firstOfMonth));
  const [endDate, setEndDate]     = useState(() => ymd(lastOfMonth));
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
          start_date: startDate,
          end_date: endDate,
          location,
          page: String(page),
          page_size: "50",
        }).toString();
        const res = await fetch(`/api/reports/payments-due?${params}`, {
          signal: controller.signal,
          credentials: "include",
          cache: "no-store",
        });
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const json = (await res.json()) as ApiResponse;
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

  const clearFilters = () => {
    setStartDate(ymd(firstOfMonth));
    setEndDate(ymd(lastOfMonth));
    setLocation("all");
    setPage(1);
  };

  return (
    <section className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Payments Due</h1>

      {/* Filters — matches Contract Search look */}
      <div className="grid grid-cols-1 md:grid-cols-4 xl:grid-cols-6 gap-3 items-end">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Start date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => { setPage(1); setStartDate(e.target.value); }}
            className="border rounded-lg p-2 w-full"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">End date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => { setPage(1); setEndDate(e.target.value); }}
            className="border rounded-lg p-2 w-full"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">Location</label>
          <select
            value={location}
            onChange={(e) => { setPage(1); setLocation(e.target.value); }}
            className="border rounded-lg p-2 w-full"
          >
            <option value="all">All locations</option>
            {data?.locations?.map((loc) => (
              <option key={loc.id} value={String(loc.id)}>
                {loc.name}
              </option>
            ))}
          </select>
        </div>

        <div className="md:col-span-1">
          <button
            type="button"
            onClick={clearFilters}
            className="border rounded-lg px-3 py-2 w-full md:w-auto"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Summary chip */}
      {!loading && data && (
        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-700">
          <div className="rounded-full border border-rose-100 bg-rose-50/50 px-3 py-1.5">
            <strong>Total due:</strong> {usd.format(data.summary.total_due)}
          </div>
          <div className="rounded-full border border-slate-200 bg-white px-3 py-1.5">
            <strong>Items:</strong> {data.summary.total_items}
          </div>
          <div className="rounded-full border border-slate-200 bg-white px-3 py-1.5">
            <strong>Page:</strong> {data.filters.page} / {data.summary.total_pages || 1}
          </div>
        </div>
      )}

      {/* Table / state */}
      {loading && <div className="text-sm text-slate-600">Loading…</div>}
      {err && <div className="text-sm text-rose-600">Error: {err}</div>}

      {!loading && data && (
        <>
          <div className="border rounded-xl overflow-hidden">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr className="text-left">
                  <th className="p-2">Due Date</th>
                  <th className="p-2">Amount</th>
                  <th className="p-2">Event Date</th>
                  <th className="p-2">Client</th>
                  <th className="p-2">Phone</th>
                  <th className="p-2">Contract</th>
                </tr>
              </thead>
              <tbody className="[&_tr:hover]:bg-gray-50">
                {data.results.map((r, i) => (
                  <tr key={`${r.contract_id}-${i}`} className="border-t">
                    <td className="p-2">{r.date_due}</td>
                    <td className="p-2">{usd.format(r.amount_due)}</td>
                    <td className="p-2">{r.event_date}</td>
                    <td className="p-2">{r.primary_contact}</td>
                    <td className="p-2">{r.primary_phone1}</td>
                    <td className="p-2">
                      <a
                        className="text-rose-600 hover:underline"
                        href={`/contracts/${r.contract_id}`}
                      >
                        {r.custom_contract_number ?? `#${r.contract_id}`}
                      </a>
                    </td>
                  </tr>
                ))}
                {data.results.length === 0 && (
                  <tr>
                    <td className="p-3 text-slate-500" colSpan={6}>
                      No results.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination (matches search page buttons) */}
          <div className="flex items-center gap-2">
            <button
              className="border rounded-lg px-3 py-1 disabled:opacity-50"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={data.filters.page <= 1}
            >
              Prev
            </button>
            <span>
              Page {data.filters.page} of {data.summary.total_pages || 1}
            </span>
            <button
              className="border rounded-lg px-3 py-1 disabled:opacity-50"
              onClick={() => setPage((p) => Math.min(data.summary.total_pages || 1, p + 1))}
              disabled={data.filters.page >= (data.summary.total_pages || 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </section>
  );
}
