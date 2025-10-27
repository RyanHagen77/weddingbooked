"use client";

import React, { useEffect, useMemo, useState, useCallback, useRef } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Toaster, toast } from "sonner";

/* ========= Types & helpers ========= */
type MetaResponse = {
  locations?: { id: number | string; name: string }[];
  lead_source_categories?: { id: number | string; name: string }[];
  // Only trust these; do NOT derive from users.
  coordinators?: { id: number | string; full_name?: string; name?: string }[];
  sales?: { id: number | string; full_name?: string; name?: string }[];
};

type Option = { value: string; label: string };
type AnyRecord = Record<string, any>;

async function getJSON<T>(url: string) {
  const res = await fetch(url, {
    credentials: "include",
    headers: { "X-Requested-With": "XMLHttpRequest", Accept: "application/json" },
  });
  if (res.status === 401) {
    let login = "/users/login";
    try {
      const j = await res.json();
      login = (j as any)?.login || login;
    } catch {}
    throw new Error(`auth_required:${login}`);
  }
  const text = await res.text();
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error("invalid_json");
  }
}

function getCsrfToken() {
  if (typeof document === "undefined") return "";
  const cookie = document.cookie.split(";").map((c) => c.trim()).find((c) => c.startsWith("csrftoken="));
  if (cookie) return cookie.split("=")[1];
  const meta = document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement | null;
  return meta?.content ?? "";
}

function formatPhoneLoose(v: string) {
  const digits = v.replace(/\D/g, "").slice(0, 10);
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 3)}-${digits.slice(3)}`;
  return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
}

function mapOptions(arr: any[] | undefined | null): Option[] {
  if (!Array.isArray(arr)) return [];
  return arr
    .filter((x: AnyRecord) => x && x.id !== undefined)
    .map((x: AnyRecord) => ({
      value: String(x.id),
      label: String(x.name ?? x.full_name ?? x.label ?? x.id),
    }));
}

/* ========= Validation (mirrors Django) ========= */
const nameRegex = /^[A-Za-zÀ-ÖØ-öø-ÿ\s\-']+$/;
const phoneRegex = /^\d{3}[-.]\d{3}[-.]\d{4}$/;
const emailRegex = /[^@]+@[^@]+\.[^@]+/;

const Schema = z.object({
  // Client
  primary_contact: z.string().trim().min(1, "Primary contact is required.")
    .regex(nameRegex, "Letters, spaces, hyphens, apostrophes only."),
  partner_contact: z.string().trim().optional()
    .refine((v) => !v || nameRegex.test(v), { message: "Letters, spaces, hyphens, apostrophes only." }),
  primary_email: z.string().trim().min(1, "Email is required.")
    .regex(emailRegex, "Enter a valid email (e.g., example@domain.com)."),
  primary_phone1: z.string().trim().optional()
    .refine((v) => !v || phoneRegex.test(v), { message: "Use 123-456-7890 or 123.456.7890." }),

  // Contract (non-client)
  is_code_92: z.boolean().optional().default(false),
  event_date: z.string().min(1, "Event date is required."),
  location: z.string().min(1, "Store Location is required."),
  csr: z.string().min(1, "Sales Representative is required."),
  coordinator: z.string().min(1, "Coordinator is required."),
  lead_source_category: z.string().optional(),
  lead_source_details: z.string().trim().optional(),

  bridal_party_qty: z.coerce.number().int().nonnegative().optional(),
  guests_qty: z.coerce.number().int().nonnegative().optional(),

  ceremony_site: z.string().trim().optional(),
  ceremony_city: z.string().trim().optional(),
  ceremony_state: z.string().trim().optional(),
  reception_site: z.string().trim().optional(),
  reception_city: z.string().trim().optional(),
  reception_state: z.string().trim().optional(),
});

type FormValues = z.infer<typeof Schema>;

/* ========= Small UI bits ========= */
function SelectSkeleton() {
  return <div className="mt-2 h-9 w-full animate-pulse rounded-xl bg-rose-100/60" />;
}
function FieldHint({ id, children }: { id: string; children: React.ReactNode }) {
  return <p id={id} className="mt-1 text-xs text-slate-500">{children}</p>;
}
function ErrorText({ children }: { children?: React.ReactNode }) {
  if (!children) return null;
  return <p className="mt-1 text-xs text-rose-600">{children}</p>;
}
function SectionTitle({ children }: { children: React.ReactNode }) {
  return <p className="mt-2 text-sm font-medium text-slate-900">{children}</p>;
}

/* ========= Main component ========= */
export default function NewContractForm({
  postUrl = "/api/contracts/new",
  locations = [],
  sales = [],
  coordinators = [],
  leadCategories = [],
  onRedirect,
}: {
  postUrl?: string;
  locations?: Option[];
  sales?: Option[];
  coordinators?: Option[];
  leadCategories?: Option[];
  onRedirect?: (url: string) => void;
}) {
  const [submitting, setSubmitting] = useState(false);
  const [submittedOnce, setSubmittedOnce] = useState(false);

  // RHF
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = useForm<FormValues>({
    resolver: zodResolver(Schema),
    mode: "onBlur",
    defaultValues: {
      is_code_92: false,
      bridal_party_qty: 0,
      guests_qty: 0,
    },
  });

  // Leave guard
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (isDirty && !submitting) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty, submitting]);

  // Meta options (props or fetch)
  const [metaLoading, setMetaLoading] = useState(false);
  const [metaError, setMetaError] = useState<string | null>(null);

  const CHOOSE: Option = { value: "", label: "Choose…" };

  const [LOC, setLOC] = useState<Option[]>([CHOOSE]);
  const [SALES, setSALES] = useState<Option[]>([CHOOSE]);
  const [COORDS, setCOORDS] = useState<Option[]>([CHOOSE]);
  const [LEADS, setLEADS] = useState<Option[]>([{ value: "", label: "Optional…" }]);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      // If parent injected options, use them (with placeholders)
      if (locations.length || sales.length || coordinators.length || leadCategories.length) {
        if (!cancelled) {
          setLOC(locations.length ? [CHOOSE, ...locations] : [CHOOSE]);
          setSALES(sales.length ? [CHOOSE, ...sales] : [CHOOSE]);
          setCOORDS(coordinators.length ? [CHOOSE, ...coordinators] : [CHOOSE]);
          setLEADS(leadCategories.length ? [{ value: "", label: "Optional…" }, ...leadCategories] : [{ value: "", label: "Optional…" }]);
        }
        return;
      }

      try {
        setMetaLoading(true);
        setMetaError(null);

        const data = await getJSON<MetaResponse>("/api/contracts/meta/");

        const loc = mapOptions(data.locations);
        const s   = mapOptions(data.sales);         // ONLY trust explicit sales
        const c   = mapOptions(data.coordinators);  // ONLY trust explicit coordinators
        const ls  = mapOptions(data.lead_source_categories);

        if (cancelled) return;

        setLOC(loc.length ? [CHOOSE, ...loc] : [CHOOSE]);
        setSALES(s.length ? [CHOOSE, ...s] : [CHOOSE]);
        setCOORDS(c.length ? [CHOOSE, ...c] : [CHOOSE]);
        setLEADS(ls.length ? [{ value: "", label: "Optional…" }, ...ls] : [{ value: "", label: "Optional…" }]);

        // Do NOT auto-select; user must choose.
      } catch (e: any) {
        if (!cancelled) {
          setMetaError(e?.message ?? "Failed to load options");
          if (String(e?.message || "").startsWith("auth_required:")) {
            const login = e.message.split("auth_required:")[1] || "/users/login";
            toast.error("Please sign in", { description: `Open ${login} in a new tab, then retry.` });
          }
        }
      } finally {
        if (!cancelled) setMetaLoading(false);
      }
    }

    init();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Soft hints
  const nameShort = useMemo(() => {
    const n = watch("primary_contact") || "";
    return n.trim().length > 0 && n.trim().length < 4;
  }, [watch("primary_contact")]);

  const dateInPast = useMemo(() => {
    const d = watch("event_date");
    if (!d) return false;
    try {
      return new Date(d) < new Date(new Date().toDateString());
    } catch {
      return false;
    }
  }, [watch("event_date")]);

  // Keyboard shortcuts
  const formRef = useRef<HTMLFormElement | null>(null);
  const onKeyDown = useCallback((e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "enter") {
      e.preventDefault();
      formRef.current?.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
    }
    if (e.key === "Escape") {
      e.preventDefault();
      window.history.back();
    }
  }, []);

  // Submit
  const onSubmit = async (values: FormValues) => {
    setSubmittedOnce(true);
    try {
      setSubmitting(true);
      toast.loading("Creating contract…");

      const params = new URLSearchParams();
      Object.entries(values).forEach(([k, v]) => {
        if (typeof v === "boolean") params.append(k, v ? "on" : "");
        else params.append(k, v == null ? "" : String(v));
      });

      const res = await fetch(postUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest",
        },
        body: params.toString(),
        credentials: "include",
      });

      const text = await res.text();
      let payload: any = {};
      try { payload = JSON.parse(text); } catch { payload = { raw: text }; }

      if (!res.ok) {
        const errs: string[] = [];
        const e = payload?.errors;
        if (typeof e === "string") {
          try {
            const parsed = JSON.parse(e);
            const obj = typeof parsed === "string" ? JSON.parse(parsed) : parsed;
            Object.values(obj).forEach((arr: any) => (arr as any[]).forEach((x: any) => errs.push(String(x.message ?? x))));
          } catch { errs.push(String(e)); }
        } else if (e && typeof e === "object") {
          Object.values(e).forEach((arr: any) => (arr as any[]).forEach((x: any) => errs.push(String(x))));
        } else {
          errs.push("An unexpected error occurred.");
        }
        toast.dismiss();
        toast.error("Please fix the highlighted fields.", { description: errs[0] });
        return;
      }

      const redirect = payload?.redirect_url;
      toast.dismiss();
      if (redirect) {
        toast.success("Contract created", { description: "Redirecting…" });
        onRedirect ? onRedirect(redirect) : (window.location.href = redirect);
      } else {
        toast.error("No redirect URL returned.");
      }
    } catch (err: any) {
      toast.dismiss();
      toast.error("Network error", { description: err?.message ?? "Check connection" });
    } finally {
      setSubmitting(false);
    }
  };

  /* ======== Render ======== */
  const hasClientErrors = submittedOnce && Object.keys(errors).length > 0;

  return (
    <>
      <Toaster richColors position="top-center" />
      <div className="rounded-2xl border border-rose-100 bg-white/90 shadow-soft p-0 md:p-6">
        {/* Sticky header actions on mobile */}
        <div className="sticky top-0 z-10 -mx-4 mb-4 border-b border-rose-100 bg-white/80 px-4 py-3 backdrop-blur md:static md:m-0 md:border-none md:bg-transparent md:p-0 md:backdrop-blur-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-slate-900">New Contract</h2>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => window.history.back()}
                className="rounded-full border border-slate-200 px-3 py-1.5 text-sm hover:bg-rose-50"
              >
                Cancel (Esc)
              </button>
              <button
                form="new-contract-form"
                type="submit"
                disabled={submitting || metaLoading}
                className="rounded-full bg-rose-500 px-4 py-1.5 text-sm text-white shadow-soft hover:bg-rose-600 disabled:opacity-60"
              >
                {submitting ? "Submitting…" : "Submit (⌘/Ctrl+Enter)"}
              </button>
            </div>
          </div>
        </div>

        {/* Error summary */}
        {hasClientErrors && (
          <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            Please review the highlighted fields below.
          </div>
        )}
        {metaError && (
          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {metaError.startsWith("auth_required:")
              ? "You must sign in to load options."
              : "Failed to load dropdown options."}
          </div>
        )}

        <form
          id="new-contract-form"
          ref={formRef}
          onKeyDown={onKeyDown}
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-6"
          aria-describedby="form-help"
        >
          {/* ===== Non-client info (two columns) ===== */}
          <div className="flex items-center gap-2">
            <input
              id="is_code_92"
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300 text-rose-600 focus:ring-rose-400"
              onChange={(e) => setValue("is_code_92", e.target.checked)}
            />
            <label htmlFor="is_code_92" className="text-sm font-medium text-slate-900">
              Code 92
            </label>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Left column */}
            <div className="space-y-4">
              {/* Event Date */}
              <div>
                <label className="text-sm font-medium text-slate-900">
                  Event Date <span className="text-rose-600">*</span>
                </label>
                <input
                  type="date"
                  className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                  aria-invalid={!!errors.event_date}
                  aria-describedby="event_date_hint"
                  {...register("event_date")}
                />
                <ErrorText>{errors.event_date?.message}</ErrorText>
                {!errors.event_date && (
                  <FieldHint id="event_date_hint">
                    {dateInPast
                      ? <span className="text-amber-600">This date is in the past—confirm this is intentional.</span>
                      : "Event date is required."}
                  </FieldHint>
                )}
              </div>

              {/* Store Location */}
              <div>
                <label className="text-sm font-medium text-slate-900">
                  Store Location <span className="text-rose-600">*</span>
                </label>
                {metaLoading && LOC.length <= 1 ? (
                  <SelectSkeleton />
                ) : (
                  <select
                    className="mt-1 w-full rounded-xl border-slate-300 bg-white focus:border-rose-400 focus:ring-rose-400 disabled:opacity-60"
                    aria-invalid={!!errors.location}
                    {...register("location")}
                    defaultValue=""
                    disabled={metaLoading}
                  >
                    {LOC.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                )}
                <ErrorText>{errors.location?.message}</ErrorText>
                {!metaLoading && LOC.length <= 1 && (
                  <p className="mt-1 text-xs text-amber-600">No locations available.</p>
                )}
              </div>

              {/* Lead Source Category */}
              <div>
                <label className="text-sm font-medium text-slate-900">Lead Source Category</label>
                {metaLoading && LEADS.length <= 1 ? (
                  <SelectSkeleton />
                ) : (
                  <select
                    className="mt-1 w-full rounded-xl border-slate-300 bg-white focus:border-rose-400 focus:ring-rose-400 disabled:opacity-60"
                    {...register("lead_source_category")}
                    defaultValue=""
                    disabled={metaLoading}
                  >
                    {LEADS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                )}
                <FieldHint id="lead_source_hint">General category (e.g., Online, Venue Referral)</FieldHint>
              </div>
            </div>

            {/* Right column */}
            <div className="space-y-4">
              {/* Lead Source Details */}
              <div>
                <label className="text-sm font-medium text-slate-900">Lead Source Details</label>
                <input
                  className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                  placeholder="The Knot, XYZ Banquet Hall…"
                  {...register("lead_source_details")}
                />
                <FieldHint id="lead_source_details_hint">Specific source details.</FieldHint>
              </div>

              {/* Coordinator */}
              <div>
                <label className="text-sm font-medium text-slate-900">
                  Coordinator <span className="text-rose-600">*</span>
                </label>
                {metaLoading && COORDS.length <= 1 ? (
                  <SelectSkeleton />
                ) : (
                  <select
                    className="mt-1 w-full rounded-xl border-slate-300 bg-white focus:border-rose-400 focus:ring-rose-400 disabled:opacity-60"
                    aria-invalid={!!errors.coordinator}
                    {...register("coordinator")}
                    defaultValue=""
                    disabled={metaLoading}
                  >
                    {COORDS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                )}
                <ErrorText>{errors.coordinator?.message}</ErrorText>
                {!metaLoading && COORDS.length <= 1 && (
                  <p className="mt-1 text-xs text-amber-600">No coordinators available yet.</p>
                )}
              </div>

              {/* CSR */}
              <div>
                <label className="text-sm font-medium text-slate-900">
                  Sales Representative <span className="text-rose-600">*</span>
                </label>
                {metaLoading && SALES.length <= 1 ? (
                  <SelectSkeleton />
                ) : (
                  <select
                    className="mt-1 w-full rounded-xl border-slate-300 bg-white focus:border-rose-400 focus:ring-rose-400 disabled:opacity-60"
                    aria-invalid={!!errors.csr}
                    {...register("csr")}
                    defaultValue=""
                    disabled={metaLoading}
                  >
                    {SALES.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                )}
                <ErrorText>{errors.csr?.message}</ErrorText>
                {!metaLoading && SALES.length <= 1 && (
                  <p className="mt-1 text-xs text-amber-600">No sales reps available yet.</p>
                )}
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="my-6 h-px w-full bg-gradient-to-r from-transparent via-rose-200 to-transparent" />

          {/* ===== Client info (two columns) ===== */}
          <h3 className="text-base font-medium text-slate-900">Client</h3>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-4">
              {/* Primary Contact */}
              <div>
                <label className="text-sm font-medium text-slate-900">
                  Primary Contact <span className="text-rose-600">*</span>
                </label>
                <input
                  className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                  aria-invalid={!!errors.primary_contact}
                  {...register("primary_contact")}
                />
                <ErrorText>{errors.primary_contact?.message}</ErrorText>
                {!errors.primary_contact && (
                  <FieldHint id="primary_contact_hint">
                    {nameShort ? (
                      <span className="text-amber-600">Looks short—use full first &amp; last name.</span>
                    ) : (
                      "Letters, spaces, hyphens, apostrophes only."
                    )}
                  </FieldHint>
                )}
              </div>

              {/* Partner Contact */}
              <div>
                <label className="text-sm font-medium text-slate-900">Partner Contact</label>
                <input
                  className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                  aria-invalid={!!errors.partner_contact}
                  {...register("partner_contact")}
                />
                <ErrorText>{errors.partner_contact?.message}</ErrorText>
              </div>

              {/* Email */}
              <div>
                <label className="text-sm font-medium text-slate-900">
                  Primary Email <span className="text-rose-600">*</span>
                </label>
                <input
                  type="email"
                  className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                  placeholder="name@example.com"
                  aria-invalid={!!errors.primary_email}
                  {...register("primary_email")}
                />
                <ErrorText>{errors.primary_email?.message}</ErrorText>
                {!errors.primary_email && (
                  <FieldHint id="primary_email_hint">We’ll use this to create or match the client.</FieldHint>
                )}
              </div>

              {/* Phone */}
              <div>
                <label className="text-sm font-medium text-slate-900">Primary Phone 1</label>
                <input
                  inputMode="numeric"
                  className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                  placeholder="123-456-7890 or 123.456.7890"
                  aria-invalid={!!errors.primary_phone1}
                  {...register("primary_phone1", {
                    onBlur: (e) => {
                      const f = formatPhoneLoose(e.target.value);
                      if (f !== e.target.value) setValue("primary_phone1", f, { shouldDirty: true, shouldValidate: true });
                    },
                  })}
                />
                <ErrorText>{errors.primary_phone1?.message}</ErrorText>
                {!errors.primary_phone1 && (
                  <FieldHint id="primary_phone1_hint">Accepted: 123-456-7890 or 123.456.7890</FieldHint>
                )}
              </div>

              {/* Quantities */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-900">Bridal Party Quantity</label>
                  <input
                    type="number"
                    min={0}
                    className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                    {...register("bridal_party_qty", { valueAsNumber: true })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-900">Guest Quantity</label>
                  <input
                    type="number"
                    min={0}
                    className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                    {...register("guests_qty", { valueAsNumber: true })}
                  />
                </div>
              </div>
            </div>

            {/* Ceremony / Reception */}
            <div className="space-y-4">
              {/* Ceremony */}
              <SectionTitle>Ceremony</SectionTitle>
              <div>
                <label className="text-sm text-slate-900">Ceremony Site</label>
                <input
                  className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                  {...register("ceremony_site")}
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm text-slate-900">City</label>
                  <input
                    className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                    {...register("ceremony_city")}
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-900">State</label>
                  <input
                    className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                    {...register("ceremony_state")}
                  />
                </div>
              </div>

              {/* Reception */}
              <SectionTitle>Reception</SectionTitle>
              <div>
                <label className="text-sm text-slate-900">Reception Site</label>
                <input
                  className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                  {...register("reception_site")}
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm text-slate-900">City</label>
                  <input
                    className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                    {...register("reception_city")}
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-900">State</label>
                  <input
                    className="mt-1 w-full rounded-xl border-slate-300 focus:border-rose-400 focus:ring-rose-400"
                    {...register("reception_state")}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Bottom actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              className="rounded-full border border-slate-200 px-4 py-2 text-sm hover:bg-rose-50"
              onClick={() => window.history.back()}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || metaLoading}
              className="rounded-full bg-rose-500 px-5 py-2 text-sm text-white shadow-soft hover:bg-rose-600 disabled:opacity-60"
            >
              {submitting ? "Submitting…" : "Submit"}
            </button>
          </div>

          <p id="form-help" className="sr-only">Fields marked with an asterisk are required.</p>
        </form>
      </div>
    </>
  );
}


