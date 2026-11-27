"use client";
import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import type { Catalog, Opportunity } from "@/lib/api";
import { useApi } from "@/lib/use-api";

export default function BrowsePage() {
  const [sport, setSport] = useState("football");
  const [type, setType] = useState("");
  const [sort, setSort] = useState("deadline");
  const catalog = useApi<Catalog>("/catalog");
  const query = new URLSearchParams({ sport, sort, ...(type ? { type } : {}) });
  const listings = useApi<Opportunity[]>(`/opportunities?${query}`);
  return (
    <AppShell>
      <Link href="/opportunities" className="text-sm text-accent hover:underline">See your recommendations</Link>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">Browse opportunities</h1>
      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <div className="text-sm">
          <label htmlFor="browse-sport">Sport</label>
          <select id="browse-sport" className="field mt-1 capitalize" value={sport} onChange={(event) => setSport(event.target.value)}>
            {Object.keys(catalog.data?.sports ?? { football: [] }).map((name) => <option key={name}>{name}</option>)}
          </select>
        </div>
        <div className="text-sm">
          <label htmlFor="browse-type">Type</label>
          <select id="browse-type" className="field mt-1" value={type} onChange={(event) => setType(event.target.value)}>
            <option value="">All opportunity types</option>
            {Object.entries(catalog.data?.types ?? {}).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
        </div>
        <div className="text-sm">
          <label htmlFor="browse-sort">Sort</label>
          <select id="browse-sort" className="field mt-1" value={sort} onChange={(event) => setSort(event.target.value)}>
            <option value="deadline">Deadline soonest</option>
            <option value="newest">Newest</option>
          </select>
        </div>
      </div>
      {listings.loading && <p role="status" className="mt-5 text-muted">Loading opportunities…</p>}
      {(catalog.error || listings.error) && <p role="alert" className="panel mt-5 p-5">{catalog.error ?? listings.error}</p>}
      {listings.data?.length === 0 && <p className="panel mt-5 p-5">No active opportunities for those filters.</p>}
      {!!listings.data?.length && <ul className="panel mt-5 divide-y divide-line">
        {listings.data.map((item) => <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 p-4">
          <div>
            <Link href={`/opportunities/${item.id}`} className="font-medium text-accent hover:underline">{item.title}</Link>
            <p className="text-sm text-muted">{item.org} · {item.city || "Open / online"}</p>
          </div>
          <span className="text-sm text-muted">{item.deadline ? new Date(item.deadline).toLocaleDateString() : "Rolling deadline"}</span>
        </li>)}
      </ul>}
    </AppShell>
  );
}
