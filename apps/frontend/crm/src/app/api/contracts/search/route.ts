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
  const backendURL = new URL(`${origin}/api/contracts/search/`);
  // forward query params
  req.nextUrl.searchParams.forEach((v, k) => backendURL.searchParams.set(k, v));
  const cookie = req.headers.get("cookie") || "";

  try {
    const res = await fetch(backendURL.toString(), {
      headers: { "X-Requested-With": "XMLHttpRequest", Accept: "application/json", Cookie: cookie },
      redirect: "manual",
      cache: "no-store",
    });

    if ([301, 302, 303].includes(res.status) && (res.headers.get("location") || "").includes("/login")) {
      return NextResponse.json({ error: "Not authenticated", login: res.headers.get("location") }, { status: 401 });
    }

    const body = await res.text();
    try { return NextResponse.json(JSON.parse(body), { status: res.status }); }
    catch { return new NextResponse(body, { status: res.status, headers: { "Content-Type": res.headers.get("content-type") || "text/plain" } }); }

  } catch (err: any) {
    return NextResponse.json({ error: "Backend unavailable", details: err?.message, target: backendURL.toString() }, { status: 502 });
  }
}
