// apps/crm/src/components/layout/SidebarShell.tsx
"use client";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { ClipboardList, FilePlus2, Users, Search, BarChart3, Settings, LogOut } from "lucide-react";

type Item = { href: string; label: string; icon: React.ReactNode };

export default function SidebarShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [displayName, setDisplayName] = useState<string>("");

// inside useEffect()
  useEffect(() => {
    fetch("/api/users/current/", { credentials: "include" })
      .then(r => (r.ok ? r.json() : null))
      .then(d => setDisplayName(d?.first_name || d?.username || ""))
      .catch(() => setDisplayName(""));
  }, []);


  const items: Item[] = [
    { href: "/contracts/search", label: "Contract Search", icon: <Search className="inline h-4 w-4 mr-2" /> },
    { href: "/contracts/new",    label: "New Contract",    icon: <FilePlus2 className="inline h-4 w-4 mr-2" /> },
    { href: "/bookings/search",  label: "Booking Search",  icon: <Search className="inline h-4 w-4 mr-2" /> },
    { href: "/event-staff",      label: "Event Staff",     icon: <Users className="inline h-4 w-4 mr-2" /> },
    { href: "/reports",          label: "Reports",         icon: <BarChart3 className="inline h-4 w-4 mr-2" /> },
    { href: "/tasks",            label: "Tasks",           icon: <ClipboardList className="inline h-4 w-4 mr-2" /> },
    { href: "/admin",            label: "Admin",           icon: <Settings className="inline h-4 w-4 mr-2" /> },
  ];

  const isActive = (href: string) => pathname === href || (href !== "/" && pathname.startsWith(href));
  const isTopNav = pathname.startsWith("/contracts/search");

  return (
    <div className="min-h-screen bg-[radial-gradient(800px_300px_at_20%_-10%,#fff6f7_0%,transparent_60%),radial-gradient(600px_250px_at_100%_0%,#f3f7f4_0%,transparent_60%)]">
      <header className="border-b border-rose-100/70 bg-gradient-to-b from-rose-50/70 to-white px-4 sm:px-6 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Image
            src="/Final_Logo.png"   // file must exist in apps/crm/public
            alt="Logo"
            width={112}
            height={28}
            priority
            className="h-7 w-auto"
          />
        </div>
        <div className="flex items-center gap-3">
          {displayName ? (
            <span className="hidden sm:block text-sm text-slate-600">Hello, {displayName}</span>
          ) : null}
          <a
            href="/users/logout/"
            className="flex items-center rounded-full border border-rose-200 px-3 py-1.5 text-sm text-rose-700 hover:bg-rose-100"
          >
            <LogOut className="h-4 w-4 mr-1" /> Logout
          </a>
        </div>
      </header>

      {isTopNav ? (
        <div className="mx-auto w-full max-w-7xl px-4 md:px-6 py-4">
          <nav className="mb-4 flex flex-wrap gap-2">
            {items.map(({ href, label, icon }) => {
              const active = isActive(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={[
                    "rounded-full px-3 py-2 text-sm transition border",
                    active
                      ? "bg-rose-100 text-rose-700 border-rose-200 shadow-sm"
                      : "bg-white text-slate-700 border-rose-100 hover:bg-rose-50 hover:text-rose-700",
                  ].join(" ")}
                >
                  {icon}{label}
                </Link>
              );
            })}
          </nav>
          <main className="rounded-2xl">{children}</main>
        </div>
      ) : (
        <div className="mx-auto max-w-6xl grid grid-cols-1 md:grid-cols-[220px_1fr] gap-6 px-4 md:px-6 py-6">
          <aside className="md:sticky md:top-4 h-max rounded-2xl border border-rose-100 bg-white shadow-sm p-3">
            <nav className="flex flex-col gap-1 text-sm">
              {items.map(({ href, label, icon }) => {
                const active = isActive(href);
                return (
                  <Link
                    key={href}
                    href={href}
                    className={[
                      "rounded-full px-3 py-2 transition",
                      active
                        ? "bg-rose-100 text-rose-700 shadow-sm"
                        : "hover:bg-rose-50 hover:text-rose-700",
                    ].join(" ")}
                  >
                    {icon}{label}
                  </Link>
                );
              })}
            </nav>
          </aside>
          <main>{children}</main>
        </div>
      )}
    </div>
  );
}
