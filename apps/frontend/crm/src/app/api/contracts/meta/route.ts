import { NextRequest, NextResponse } from "next/server";
export const dynamic = "force-dynamic";
export const fetchCache = "default-no-store";

function getBackendOrigin() {
  const raw = (process.env.NEXT_PUBLIC_BACKEND_ORIGIN || "http://localhost:8000").trim();
  try { const u = new URL(raw.includes("://") ? raw : `https://${raw}`); return `${u.protocol}//${u.host}`; }
  catch { return "http://localhost:8000"; }
}

export async function GET(req: NextRequest) {
  const origin = getBackendOrigin();
  const url = `${origin}/api/contracts/meta/`;
  const cookie = req.headers.get("cookie") || "";
  try {
    const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest", Accept: "application/json", Cookie: cookie }, redirect: "manual", cache: "no-store" });
    if ([301,302,303].includes(res.status) && (res.headers.get("location")||"").includes("/login")) {
      return NextResponse.json({ error: "Not authenticated", login: res.headers.get("location") }, { status: 401 });
    }
    const text = await res.text();
    const out = (() => { try { return NextResponse.json(JSON.parse(text), { status: res.status }); }
      catch { return new NextResponse(text, { status: res.status, headers: { "Content-Type": res.headers.get("content-type") || "text/plain" } }); }})();
    const setCookie = res.headers.get("set-cookie"); if (setCookie) out.headers.set("set-cookie", setCookie);
    return out;
  } catch (err: any) {
    return NextResponse.json({ error: "Backend unavailable", details: err?.message, target: url }, { status: 502 });
  }
}
