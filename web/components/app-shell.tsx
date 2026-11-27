"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense } from "react";
import { SignOut } from "@phosphor-icons/react";
import { endSession, type User } from "@/lib/api";
import { useApi } from "@/lib/use-api";

const NAV = [
  { href: "/", label: "Feed" },
  { href: "/opportunities", label: "Opportunities" },
  { href: "/applications", label: "Applications" },
  { href: "/evaluation", label: "Evaluation" },
];

export function Logo() {
  return (
    <span className="flex items-center gap-2 font-semibold tracking-tight text-ink">
      <span aria-hidden className="grid size-7 place-items-center rounded-lg bg-accent text-xs font-bold text-accent-ink">GU</span>
      Ground Up
    </span>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Suspense fallback={<header className="h-14 border-b border-line" />}>
        <AppHeader />
      </Suspense>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
    </>
  );
}

function AppHeader() {
  const path = usePathname();
  const account = useApi<User>("/me");
  const user = account.data;
  const links = NAV.filter(({ href }) => href !== "/applications" || user?.role === "athlete");
  if (user?.organisation_name) links.splice(2, 0, { href: "/organisation", label: "Organisation" });
  return (
      <header className="sticky top-0 z-10 border-b border-line bg-bg/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 py-3 sm:flex-nowrap">
          <Link href="/"><Logo /></Link>
          {user ? (
            <button type="button" className="flex items-center gap-1.5 text-sm text-muted hover:text-ink sm:order-last sm:ml-auto"
              onClick={endSession}>
              <SignOut size={16} /> Sign out
            </button>
          ) : path === "/evaluation" && <Link href="/login" className="text-sm text-accent sm:order-last">Sign in</Link>}
          {(user || path !== "/evaluation") && (
            <nav aria-label="Main navigation" className="flex w-full flex-wrap gap-1 sm:w-auto">
              {links.map(({ href, label }) => (
                <Link key={href} href={href} aria-current={path === href ? "page" : undefined}
                  className={`rounded-lg px-2.5 py-1.5 text-sm transition ${path === href ? "bg-accent-soft font-medium text-accent" : "text-muted hover:text-ink"}`}>
                  {label}
                </Link>
              ))}
            </nav>
          )}
        </div>
      </header>
  );
}
