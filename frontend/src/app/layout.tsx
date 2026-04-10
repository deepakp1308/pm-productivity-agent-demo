"use client";
import "./globals.css";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/recommendations", label: "Recommendations", icon: "✦" },
  { href: "/decisions", label: "Decisions", icon: "⚡" },
  { href: "/priorities", label: "Priorities", icon: "🎯" },
  { href: "/chat", label: "Ask Agent", icon: "💬" },
];

const PM_LINKS = [
  { href: "/pm/jordan-park", label: "Jordan Park", initials: "SY" },
  { href: "/pm/morgan-lee", label: "Morgan Lee", initials: "NJ" },
  { href: "/pm/taylor-kim", label: "Taylor Kim", initials: "VW" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <html lang="en" className="h-full antialiased">
      <head>
        <title>PM Productivity Agent</title>
        <meta name="description" content="Evidence-backed weekly coaching for PM teams" />
      </head>
      <body className="min-h-full">
        <div className="flex h-screen overflow-hidden">
          {/* Dark navy sidebar */}
          <aside
            className="w-[240px] flex-shrink-0 flex flex-col"
            style={{ background: "var(--sidebar-bg)" }}
          >
            {/* Logo */}
            <div className="px-5 py-5 flex items-center gap-2">
              <span className="text-[#00b9a9] text-xl">✦</span>
              <span className="text-white font-semibold text-[15px]">PM Agent</span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 space-y-1">
              {NAV_ITEMS.map((item) => {
                const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-md text-[13px] transition-colors ${
                      active
                        ? "bg-white/15 text-white font-medium"
                        : "text-white/70 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    <span className="text-base w-5 text-center">{item.icon}</span>
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {/* Team members */}
            <div className="px-3 pb-5">
              <div className="text-white/40 text-[11px] font-medium uppercase tracking-wider px-3 mb-2">
                Team
              </div>
              {PM_LINKS.map((pm) => {
                const active = pathname === pm.href;
                return (
                  <Link
                    key={pm.href}
                    href={pm.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-md text-[13px] transition-colors ${
                      active
                        ? "bg-white/15 text-white font-medium"
                        : "text-white/70 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    <span
                      className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold"
                      style={{ background: "var(--accent-blue)", color: "white" }}
                    >
                      {pm.initials}
                    </span>
                    {pm.label}
                  </Link>
                );
              })}
            </div>
          </aside>

          {/* Main content */}
          <main className="flex-1 overflow-y-auto" style={{ background: "var(--page-bg)" }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
