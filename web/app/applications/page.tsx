"use client";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import type { Application } from "@/lib/api";
import { useApi } from "@/lib/use-api";

export default function ApplicationsPage() {
  const results = useApi<Application[]>("/me/applications");
  return (
    <AppShell>
      <h1 className="text-3xl font-semibold tracking-tight">Your applications</h1>
      <p className="mt-2 text-muted">Review the opportunities you have applied to.</p>
      {results.loading && <p className="mt-6 text-muted" role="status">Loading applications…</p>}
      {results.error && <p role="alert" className="panel mt-6 p-5">{results.error}</p>}
      {results.data?.length === 0 && <div className="panel mt-6 p-6">
        <p>No applications yet.</p>
        <Link className="btn-ghost mt-4" href="/opportunities">See your opportunities</Link>
      </div>}
      {!!results.data?.length && (
        <ul className="panel mt-6 divide-y divide-line">
          {results.data.map(({ id, opportunity, status, created_at }) => (
            <li key={id} className="flex flex-wrap items-center justify-between gap-3 p-5">
              <div>
                <Link href={`/opportunities/${opportunity.id}`} className="font-medium text-accent hover:underline">{opportunity.title}</Link>
                <p className="mt-1 text-sm text-muted">{opportunity.org} · {new Date(created_at).toLocaleDateString()}</p>
              </div>
              <span className="rounded-lg bg-accent-soft px-3 py-1 text-sm capitalize text-accent">{status}</span>
            </li>
          ))}
        </ul>
      )}
    </AppShell>
  );
}
