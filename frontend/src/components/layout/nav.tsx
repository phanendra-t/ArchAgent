"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/review", label: "Review" },
  { href: "/reviews", label: "Reviews" },
  { href: "/metrics", label: "Metrics" },
  { href: "/docs", label: "Docs" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-14 items-center px-4">
        <Link href="/" className="flex items-center gap-2 mr-8">
          <div className="h-7 w-7 rounded bg-foreground flex items-center justify-center">
            <span className="text-background font-bold text-sm">A</span>
          </div>
          <span className="font-semibold tracking-tight">ArchAgent</span>
        </Link>
        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-3 py-1.5 text-sm rounded-md transition-colors",
                pathname === item.href
                  ? "bg-accent text-accent-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
