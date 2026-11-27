"use client";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { OpportunityGallery } from "@/components/opportunity-gallery";
import type { Match } from "@/lib/api";
import { useApi } from "@/lib/use-api";

export default function OpportunitiesPage() {
  const { data, loading, error, reload } = useApi<Match[]>("/opportunities/recommended?k=100");
  return (
    <AppShell>
      <h1 className="text-3xl font-semibold tracking-tight">Opportunities for you</h1>
      <p className="mt-2 max-w-[65ch] text-muted">
        Your compatibility score reflects position, skills, age, location, level and goals. Open any recommendation to see how the score was calculated.
      </p>
      <p className="mt-2 text-sm text-muted">Compatibility describes profile fit. Selection decisions belong to the organisation.</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Link href="/onboarding/profile" className="btn-ghost">Edit athlete profile</Link>
        <Link href="/browse" className="btn-ghost">Browse all sports</Link>
      </div>

      <div className="mt-8">
        {loading && (
          <div className="grid auto-rows-[420px] gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => <div key={i} className="animate-pulse rounded-3xl bg-surface" />)}
          </div>
        )}
        {error && (
          <div className="panel flex items-center justify-between p-5 text-sm">
            <span className="text-red-600 dark:text-red-400">{error}</span>
            <button className="btn-ghost" onClick={reload}>Retry</button>
          </div>
        )}
        {data?.length === 0 && (
          <div className="panel p-8 text-center">
            <p className="font-medium">No matches yet</p>
            <p className="mt-1 text-sm text-muted">There are no open opportunities in the sport and age range on your profile.</p>
            <Link href="/browse" className="btn-primary mt-4">Browse opportunities</Link>
          </div>
        )}
        {!!data?.length && <OpportunityGallery matches={data} />}
      </div>
    </AppShell>
  );
}
