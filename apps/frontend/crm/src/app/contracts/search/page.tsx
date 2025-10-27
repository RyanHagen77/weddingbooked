"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import SidebarShell from "@/components/layout/SidebarShell";

type Option = { id: number; name: string };
type StatusOption = { value: string; label: string };

type Meta = {
  statuses: StatusOption[];
  locations: Option[];
  csrs: Option[];
  photographers: Option[];
  videographers: Option[];
  photobooth_operators: Option[];
  djs: Option[];
};

type ContractRow = {
  id: number;
  custom_contract_number: string | null;
  status: string;
  event_date: string | null;
  location: Option | null;
  client: { id: number | null; primary_contact: string | null; email: string | null } | null;
  csr: Option | null; // Sales Person

  // --- staffing & package fields (optional, UI handles absence) ---
  photography_package?: boolean | null;
  photography_additional?: boolean | null;
  photographer1_name?: string | null;
  photographer2_name?: string | null;

  videography_package?: boolean | null;
  videography_additional?: boolean | null;
  videographer1_name?: string | null;
  videographer2_name?: string | null;

  photobooth_package?: boolean | null;
  photobooth_additional?: boolean | null;
  photobooth_op1_name?: string | null;
  photobooth_op2_name?: string | null;

  dj_package?: boolean | null;
  dj1_name?: string | null;
  dj2_name?: string | null;
};

type SearchResponse = {
  results: ContractRow[];
  page: number;
  page_size: number;
  total: number;
};

function useURLState() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const setParam = (key: string, value?: string) => {
    const sp = new URLSearchParams(params?.toString());
    if (!value) sp.delete(key);
    else sp.set(key, value);
    sp.set("page", sp.get("page") ?? "1");
    router.replace(`${pathname}?${sp.toString()}`);
  };
  return { params, setParam };
}

function formatYYYYMMDD(d: Date) {
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}
function getDefaultDateRange() {
  const start = new Date(); // today (local)
  const end = new Date();
  end.setDate(end.getDate() + 30); // or 28 for 4 weeks
  return { from: formatYYYYMMDD(start), to: formatYYYYMMDD(end) };
}

export default function ContractSearchPage() {
  const { params, setParam } = useURLState();

  // --- Meta ---
  const [meta, setMeta] = useState<Meta | null>(null);

  // --- Controls bound to URL params ---
  const [q, setQ] = useState(params.get("q") ?? "");
  const [statusCSV, setStatusCSV] = useState(params.get("status") ?? "");
  const [eventFrom, setEventFrom] = useState(params.get("event_date_from") ?? "");
  const [eventTo, setEventTo] = useState(params.get("event_date_to") ?? "");
  const [location, setLocation] = useState(params.get("location") ?? "");
  const [csr, setCsr] = useState(params.get("csr") ?? "");
  const [ceremonySite, setCeremonySite] = useState(params.get("ceremony_site") ?? "");
  const [receptionSite, setReceptionSite] = useState(params.get("reception_site") ?? "");
  const [photographer, setPhotographer] = useState(params.get("photographer") ?? "");
  const [videographer, setVideographer] = useState(params.get("videographer") ?? "");
  const [photoboothOp, setPhotoboothOp] = useState(params.get("photobooth_operator") ?? "");
  const [dj, setDj] = useState(params.get("dj") ?? "");
  const [sort, setSort] = useState(params.get("sort") ?? "-event_date");
  const [page, setPage] = useState<number>(parseInt(params.get("page") ?? "1") || 1);
  const [pageSize, setPageSize] = useState<number>(parseInt(params.get("page_size") ?? "25") || 25);

  // Keep local state in sync on back/forward
  useEffect(() => {
    setQ(params.get("q") ?? "");
    setStatusCSV(params.get("status") ?? "");
    setEventFrom(params.get("event_date_from") ?? "");
    setEventTo(params.get("event_date_to") ?? "");
    setLocation(params.get("location") ?? "");
    setCsr(params.get("csr") ?? "");
    setCeremonySite(params.get("ceremony_site") ?? "");
    setReceptionSite(params.get("reception_site") ?? "");
    setPhotographer(params.get("photographer") ?? "");
    setVideographer(params.get("videographer") ?? "");
    setPhotoboothOp(params.get("photobooth_operator") ?? "");
    setDj(params.get("dj") ?? "");
    setSort(params.get("sort") ?? "-event_date");
    setPage(parseInt(params.get("page") ?? "1") || 1);
    setPageSize(parseInt(params.get("page_size") ?? "25") || 25);
  }, [params]);

  // Load meta (map full_name -> name if needed)
  useEffect(() => {
    fetch("/api/contracts/meta/")
      .then((r) => r.json())
      .then((raw) => {
        const mapList = (arr: any[] = []) => arr.map((u: any) => ({ id: u.id, name: u.name ?? u.full_name ?? "" }));
        setMeta({
          statuses: raw.statuses ?? [],
          locations: mapList(raw.locations),
          csrs: mapList(raw.csrs),
          photographers: mapList(raw.photographers),
          videographers: mapList(raw.videographers),
          photobooth_operators: mapList(raw.photobooth_operators),
          djs: mapList(raw.djs),
        });
      })
      .catch(() => setMeta(null));
  }, []);

  // Default 30-day window on first load if no explicit dates in URL
  const didInitRef = useRef(false);
  useEffect(() => {
    if (didInitRef.current) return;
    didInitRef.current = true;

    const hasFrom = !!params.get("event_date_from");
    const hasTo = !!params.get("event_date_to");
    if (!hasFrom && !hasTo) {
      const { from, to } = getDefaultDateRange();
      setEventFrom(from);
      setEventTo(to);
      const sp = new URLSearchParams(params?.toString());
      sp.set("event_date_from", from);
      sp.set("event_date_to", to);
      sp.set("page", "1");
      history.replaceState(null, "", `?${sp.toString()}`);
    }
  }, [params]);

  // --- Debounced search ---
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<number | null>(null);

  const queryString = useMemo(() => {
    const sp = new URLSearchParams();
    if (q) sp.set("q", q);
    if (statusCSV) sp.set("status", statusCSV);
    if (eventFrom) sp.set("event_date_from", eventFrom);
    if (eventTo) sp.set("event_date_to", eventTo);
    if (location) sp.set("location", location);
    if (csr) sp.set("csr", csr);
    if (ceremonySite) sp.set("ceremony_site", ceremonySite);
    if (receptionSite) sp.set("reception_site", receptionSite);
    if (photographer) sp.set("photographer", photographer);
    if (videographer) sp.set("videographer", videographer);
    if (photoboothOp) sp.set("photobooth_operator", photoboothOp);
    if (dj) sp.set("dj", dj);
    if (sort) sp.set("sort", sort);
    sp.set("page", String(page));
    sp.set("page_size", String(pageSize));
    return sp.toString();
  }, [
    q,
    statusCSV,
    eventFrom,
    eventTo,
    location,
    csr,
    ceremonySite,
    receptionSite,
    photographer,
    videographer,
    photoboothOp,
    dj,
    sort,
    page,
    pageSize,
  ]);

  useEffect(() => {
    const sp = new URLSearchParams(queryString);
    history.replaceState(null, "", `?${sp.toString()}`);

    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => {
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      setLoading(true);
      setErr(null);
      fetch(`/api/contracts/search/?${queryString}`, { signal: ctrl.signal })
        .then(async (r) => {
          if (!r.ok) {
            const j = await r.json().catch(() => ({}));
            throw new Error(j.error || `HTTP ${r.status}`);
          }
          return r.json();
        })
        .then(setData)
        .catch((e) => {
          if (e.name !== "AbortError") setErr(e.message);
        })
        .finally(() => setLoading(false));
    }, 300);

    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
      abortRef.current?.abort();
    };
  }, [queryString]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  const toggleStatus = (value: string) => {
    const set = new Set((statusCSV ? statusCSV.split(",") : []).filter(Boolean));
    set.has(value) ? set.delete(value) : set.add(value);
    const next = Array.from(set).join(",");
    setStatusCSV(next);
    setParam("status", next || undefined);
    setParam("page", "1");
  };

  // helpers to render staffing cells
  const renderPhoto = (r: ContractRow) => {
    if (!r.photography_package) return "N/A";
    const p1 = r.photographer1_name;
    const p2 = r.photographer2_name;
    if (!p1 && !p2) return <span className="text-red-600">Not Assigned</span>;
    return (
      <>
        {p1 || <span className="text-red-600">Not Assigned</span>}
        {r.photography_additional ? (
          <>
            <br />
            {p2 || <span className="text-red-600">Not Assigned</span>}
          </>
        ) : null}
      </>
    );
  };
  const renderVideo = (r: ContractRow) => {
    if (!r.videography_package) return "N/A";
    const v1 = r.videographer1_name;
    const v2 = r.videographer2_name;
    if (!v1 && !v2) return <span className="text-red-600">Not Assigned</span>;
    return (
      <>
        {v1 || <span className="text-red-600">Not Assigned</span>}
        {r.videography_additional ? (
          <>
            <br />
            {v2 || <span className="text-red-600">Not Assigned</span>}
          </>
        ) : null}
      </>
    );
  };
  const renderBooth = (r: ContractRow) => {
    if (!r.photobooth_package) return "N/A";
    const b1 = r.photobooth_op1_name;
    const b2 = r.photobooth_op2_name;
    if (!b1 && !b2) return <span className="text-red-600">Not Assigned</span>;
    return (
      <>
        {b1 || <span className="text-red-600">Not Assigned</span>}
        {r.photobooth_additional ? (
          <>
            <br />
            {b2 || <span className="text-red-600">Not Assigned</span>}
          </>
        ) : null}
      </>
    );
  };
  const renderDj = (r: ContractRow) => {
    if (!r.dj_package) return "N/A";
    const d1 = r.dj1_name;
    const d2 = r.dj2_name;
    if (!d1 && !d2) return <span className="text-red-600">Not Assigned</span>;
    return (
      <>
        {d1 || null}
        {d2 ? (
          <>
            <br />
            {d2}
          </>
        ) : null}
      </>
    );
  };

  const clearAll = () => {
    const { from, to } = getDefaultDateRange();
    setQ("");
    setStatusCSV("");
    setEventFrom(from);
    setEventTo(to);
    setLocation("");
    setCsr("");
    setCeremonySite("");
    setReceptionSite("");
    setPhotographer("");
    setVideographer("");
    setPhotoboothOp("");
    setDj("");
    setSort("-event_date");
    setPage(1);
    setPageSize(25);

    const sp = new URLSearchParams();
    sp.set("event_date_from", from);
    sp.set("event_date_to", to);
    sp.set("sort", "-event_date");
    sp.set("page", "1");
    sp.set("page_size", "25");
    history.replaceState(null, "", `?${sp.toString()}`);
  };

  return (
    <SidebarShell>
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-semibold">Contract Search</h1>

        {/* Controls */}
        <div className="grid grid-cols-1 md:grid-cols-4 xl:grid-cols-6 gap-3">
          <input
            className="border rounded-lg p-2 col-span-2"
            placeholder="Search name, email, phone, contract #, lead notes…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setParam("q", e.target.value || undefined);
              setParam("page", "1");
            }}
          />

          <div className="col-span-2 flex flex-wrap gap-2 items-center">
            {meta?.statuses.map((s) => (
              <button
                key={s.value}
                onClick={() => toggleStatus(s.value)}
                className={`px-3 py-1 rounded-full border transition ${
                  statusCSV.split(",").includes(s.value)
                    ? "bg-black text-white border-black"
                    : "bg-white text-black hover:bg-gray-50 border-gray-300"
                }`}
                type="button"
              >
                {s.label}
              </button>
            ))}
          </div>

          <input
            type="date"
            className="border rounded-lg p-2"
            value={eventFrom}
            onChange={(e) => {
              setEventFrom(e.target.value);
              setParam("event_date_from", e.target.value || undefined);
              setParam("page", "1");
            }}
          />
          <input
            type="date"
            className="border rounded-lg p-2"
            value={eventTo}
            onChange={(e) => {
              setEventTo(e.target.value);
              setParam("event_date_to", e.target.value || undefined);
              setParam("page", "1");
            }}
          />

          <select
            className="border rounded-lg p-2"
            value={location}
            onChange={(e) => {
              setLocation(e.target.value);
              setParam("location", e.target.value || undefined);
              setParam("page", "1");
            }}
          >
            <option value="">All Locations</option>
            {meta?.locations.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>

          <select
            className="border rounded-lg p-2"
            value={csr}
            onChange={(e) => {
              setCsr(e.target.value);
              setParam("csr", e.target.value || undefined);
              setParam("page", "1");
            }}
          >
            <option value="">All CSRs</option>
            {meta?.csrs.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>

          {/* Ceremony / Reception */}
          <input
            className="border rounded-lg p-2 col-span-2"
            placeholder="Ceremony Site"
            value={ceremonySite}
            onChange={(e) => {
              setCeremonySite(e.target.value);
              setParam("ceremony_site", e.target.value || undefined);
              setParam("page", "1");
            }}
          />
          <input
            className="border rounded-lg p-2 col-span-2"
            placeholder="Reception Site"
            value={receptionSite}
            onChange={(e) => {
              setReceptionSite(e.target.value);
              setParam("reception_site", e.target.value || undefined);
              setParam("page", "1");
            }}
          />

          {/* Staff filters */}
          <select
            className="border rounded-lg p-2"
            value={photographer}
            onChange={(e) => {
              setPhotographer(e.target.value);
              setParam("photographer", e.target.value || undefined);
              setParam("page", "1");
            }}
          >
            <option value="">All Photographers</option>
            {meta?.photographers.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>

          <select
            className="border rounded-lg p-2"
            value={videographer}
            onChange={(e) => {
              setVideographer(e.target.value);
              setParam("videographer", e.target.value || undefined);
              setParam("page", "1");
            }}
          >
            <option value="">All Videographers</option>
            {meta?.videographers.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>

          <select
            className="border rounded-lg p-2"
            value={photoboothOp}
            onChange={(e) => {
              setPhotoboothOp(e.target.value);
              setParam("photobooth_operator", e.target.value || undefined);
              setParam("page", "1");
            }}
          >
            <option value="">All Photobooth Operators</option>
            {meta?.photobooth_operators.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>

          <select
            className="border rounded-lg p-2"
            value={dj}
            onChange={(e) => {
              setDj(e.target.value);
              setParam("dj", e.target.value || undefined);
              setParam("page", "1");
            }}
          >
            <option value="">All DJs</option>
            {meta?.djs.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>

          {/* Sort + Page size */}
          <select
            className="border rounded-lg p-2"
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setParam("sort", e.target.value);
            }}
          >
            <option value="-event_date">Event Date (newest)</option>
            <option value="event_date">Event Date (oldest)</option>
            <option value="-contract_date">Contract Date (newest)</option>
            <option value="contract_date">Contract Date (oldest)</option>
            <option value="custom_contract_number">Contract # (A→Z)</option>
            <option value="-custom_contract_number">Contract # (Z→A)</option>
          </select>

          <select
            className="border rounded-lg p-2"
            value={pageSize}
            onChange={(e) => {
              const v = parseInt(e.target.value) || 25;
              setPageSize(v);
              setParam("page_size", String(v));
              setParam("page", "1");
            }}
          >
            {[25, 50, 100].map((n) => (
              <option key={n} value={n}>
                {n}/page
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={clearAll}
            className="border rounded-lg px-3 py-2 col-span-1 md:col-auto"
          >
            Clear all filters
          </button>
        </div>

        {/* Results */}
        <div className="border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="text-left p-2">#</th>
                <th className="text-left p-2">Contract ID</th>
                <th className="text-left p-2">Event Date</th>
                <th className="text-left p-2">Primary Contact</th>
                <th className="text-left p-2">Photographer</th>
                <th className="text-left p-2">Videographer</th>
                <th className="text-left p-2">Photobooth</th>
                <th className="text-left p-2">DJ</th>
                <th className="text-left p-2">Sales Person</th>
                <th className="text-left p-2">Status</th>
              </tr>
            </thead>
            <tbody className="[&_tr:hover]:bg-gray-50">
              {loading && <tr><td className="p-3" colSpan={10}>Loading…</td></tr>}
              {err && !loading && <tr><td className="p-3 text-red-600" colSpan={10}>{err}</td></tr>}
              {!loading && !err && data?.results?.length === 0 && (
                <tr><td className="p-3" colSpan={10}>No results.</td></tr>
              )}

              {!loading && !err && data?.results?.map((r, i) => (
                <tr
                  key={r.id}
                  className="cursor-pointer"
                  onClick={() => { window.location.href = `/contracts/${r.id}`; }}
                >
                  <td className="p-2">{(data!.page - 1) * data!.page_size + (i + 1)}</td>
                  <td className="p-2">{r.custom_contract_number ?? "—"}</td>
                  <td className="p-2">{r.event_date ?? "—"}</td>
                  <td className="p-2">
                    {r.client?.primary_contact ?? "—"}
                  </td>
                  <td className="p-2">{renderPhoto(r)}</td>
                  <td className="p-2">{renderVideo(r)}</td>
                  <td className="p-2">{renderBooth(r)}</td>
                  <td className="p-2">{renderDj(r)}</td>
                  <td className="p-2">{r.csr?.name ?? "—"}</td>
                  <td className="p-2 capitalize">{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center gap-2">
          <button
            className="border rounded-lg px-3 py-1"
            disabled={page <= 1}
            onClick={() => {
              setPage(page - 1);
              setParam("page", String(page - 1));
            }}
          >
            Prev
          </button>
          <span>Page {data?.page ?? page} of {totalPages}</span>
          <button
            className="border rounded-lg px-3 py-1"
            disabled={data ? data.page * data.page_size >= data.total : true}
            onClick={() => {
              setPage(page + 1);
              setParam("page", String(page + 1));
            }}
          >
            Next
          </button>
        </div>
      </div>
    </SidebarShell>
  );
}
