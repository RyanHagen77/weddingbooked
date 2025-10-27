// apps/crm/src/app/api/users/current/route.ts
import { NextRequest, NextResponse } from "next/server";

function getBackendOrigin() {
  const raw = (process.env.NEXT_PUBLIC_BACKEND_ORIGIN || "http://localhost:8000").trim();
  try { const u = new URL(raw.includes("://") ? raw : `https://${raw}`); return `${u.protocol}//${u.host}`; }
  catch { return "http://localhost:8000"; }
}

export async function GET(req: NextRequest) {
  const origin = getBackendOrigin();
  const cookie = req.headers.get("cookie") || "";
  try {
    const res = await fetch(`${origin}/api/users/current/`, {
      headers: { "X-Requested-With": "XMLHttpRequest", Cookie: cookie, Accept: "application/json" },
      redirect: "manual",
      cache: "no-store",
    });
    if ([301,302,303].includes(res.status) && (res.headers.get("location")||"").includes("/login")) {
      return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
    }
    const json = await res.json();
    return NextResponse.json(json, { status: res.status });
  } catch (e: any) {
    return NextResponse.json({ error: "Backend unavailable", details: e?.message }, { status: 502 });
  }
}
