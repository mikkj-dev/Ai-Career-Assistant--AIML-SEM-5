"use client";
import { useState } from "react";
import { eligibilityLabel, post, type Application, type OpportunityDetail } from "@/lib/api";
import { useApi } from "@/lib/use-api";

export function ApplicationAction({ opportunityId, onDark = false }: { opportunityId: string; onDark?: boolean }) {
  const detail = useApi<OpportunityDetail>(`/opportunities/${opportunityId}`);
  const [application, setApplication] = useState<Application | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const muted = onDark ? "text-white/75" : "text-muted";

  async function apply() {
    setBusy(true);
    setError(null);
    try {
      setApplication(await post<Application>(`/opportunities/${opportunityId}/apply`));
    } catch (err) {
      setError((err as Error).message);
      detail.reload();
    } finally {
      setBusy(false);
    }
  }

  if (application || detail.data?.application) {
    return <p role="status" className={`text-sm font-medium ${onDark ? "text-emerald-300" : "text-accent"}`}>Application submitted</p>;
  }
  if (detail.loading) return <p role="status" className={`text-sm ${muted}`}>Checking application status…</p>;
  if (detail.error) return (
    <div className="text-sm">
      <p role="alert">{detail.error}</p>
      <button type="button" className="underline" onClick={detail.reload}>Retry status check</button>
    </div>
  );
  const current = detail.data;
  if (!current?.match?.can_apply) {
    return <p className={`text-sm ${muted}`}>{current ? eligibilityLabel[current.eligibility] : "Application unavailable"}</p>;
  }
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button type="button" disabled={busy} className="btn-primary" onClick={() => void apply()}>{busy ? "Submitting…" : "Apply"}</button>
      {error && <p role="alert" className={`text-sm ${onDark ? "text-red-200" : "text-red-700 dark:text-red-300"}`}>{error}</p>}
    </div>
  );
}
