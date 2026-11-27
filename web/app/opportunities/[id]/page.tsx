"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Suspense } from "react";
import { AppShell } from "@/components/app-shell";
import { ApplicationAction } from "@/components/application-action";
import { ScoreRing } from "@/components/match-card";
import { eligibilityLabel, type OpportunityDetail } from "@/lib/api";
import { useApi } from "@/lib/use-api";

export default function OpportunityPage() {
  return (
    <AppShell>
      <Link href="/opportunities" className="text-sm text-accent hover:underline">Back to opportunities</Link>
      <Suspense fallback={<p role="status" className="mt-6 text-muted">Loading opportunity…</p>}>
        <OpportunityContent />
      </Suspense>
    </AppShell>
  );
}

function OpportunityContent() {
  const { id } = useParams<{ id: string }>();
  const result = useApi<OpportunityDetail>(`/opportunities/${id}`);
  const detail = result.data;
  return (
    <>
      {result.loading && <p role="status" className="mt-6 text-muted">Loading opportunity…</p>}
      {result.error && <p role="alert" className="panel mt-6 p-5">{result.error}</p>}
      {detail && (
        <article className="panel mt-5 max-w-3xl space-y-5 p-5 sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm capitalize text-muted">{detail.opportunity.sport} · {detail.opportunity.type}</p>
              <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">{detail.opportunity.title}</h1>
              <p className="mt-1 text-muted">{detail.opportunity.org}{detail.opportunity.synthetic && " · Synthetic opportunity"}</p>
            </div>
            {detail.match && <ScoreRing score={detail.match.score} />}
          </div>
          <p className="text-sm text-accent">{eligibilityLabel[detail.eligibility]}</p>
          <p>{detail.opportunity.description}</p>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div><dt className="text-muted">Location</dt><dd>{detail.opportunity.city || "Open / online"}</dd></div>
            <div><dt className="text-muted">Application deadline</dt><dd>{detail.opportunity.deadline ? new Date(detail.opportunity.deadline).toLocaleString() : "Rolling"}</dd></div>
            <div><dt className="text-muted">Age requirement</dt><dd>{[detail.opportunity.age_min ?? "Any minimum", detail.opportunity.age_max ?? "Any maximum"].join(" to ")}</dd></div>
            <div><dt className="text-muted">Level</dt><dd className="capitalize">{detail.opportunity.level || "Any"}</dd></div>
            <div><dt className="text-muted">Positions</dt><dd>{detail.opportunity.positions.join(", ") || "All positions"}</dd></div>
            <div><dt className="text-muted">Requested skills</dt><dd>{detail.opportunity.skills.join(", ") || "None specified"}</dd></div>
          </dl>
          {detail.match && (
            <div className="space-y-3 border-t border-line pt-5">
              <h2 className="font-semibold">Compatibility breakdown</h2>
              <dl className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {Object.entries(detail.match.components).map(([key, value]) => (
                  <div key={key} className="rounded-lg bg-accent-soft p-3">
                    <dt className="text-sm capitalize text-muted">{key}</dt><dd className="font-medium">{value.toFixed(3)}</dd>
                  </div>
                ))}
              </dl>
              <ul className="list-disc space-y-1 pl-5 text-sm">
                {detail.match.reasons.map((reason) => <li key={reason}>{reason}</li>)}
              </ul>
              <p className="text-sm">Matching skills · {detail.match.matching_skills.join(", ") || "None"}</p>
              <p className="text-sm">Missing skills · {detail.match.missing_skills.join(", ") || "None"}</p>
              <p className="text-sm text-muted">Goals similarity · {detail.match.similarity_method}</p>
            </div>
          )}
          <ApplicationAction opportunityId={detail.opportunity.id} />
        </article>
      )}
    </>
  );
}
