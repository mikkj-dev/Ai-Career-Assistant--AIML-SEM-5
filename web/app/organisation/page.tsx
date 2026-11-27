"use client";
import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { post, type Application, type Catalog, type Opportunity, type User } from "@/lib/api";
import { useApi } from "@/lib/use-api";

export default function OrganisationPage() {
  const account = useApi<User>("/me");
  const catalog = useApi<Catalog>("/catalog");
  const authorised = Boolean(account.data?.organisation_name && account.data.role === "team");
  const opportunities = useApi<Opportunity[]>(authorised ? "/organisation/opportunities" : null);
  const applications = useApi<Application[]>(authorised ? "/organisation/applications" : null);
  return (
    <AppShell>
      <h1 className="text-3xl font-semibold tracking-tight">Organisation dashboard</h1>
      {account.loading && <p role="status" className="mt-4 text-muted">Loading organisation…</p>}
      {account.error && <p role="alert" className="panel mt-4 p-4">{account.error}</p>}
      {account.data && !authorised && <p className="panel mt-4 p-4">An authorised organisation account is required.</p>}
      {authorised && (
        <>
          <p className="mt-2 text-muted">{account.data?.organisation_name}{account.data?.synthetic && " · Local demo organisation"}</p>
          <div className="mt-6 grid items-start gap-6 lg:grid-cols-2">
            {catalog.loading && <p role="status">Loading opportunity fields…</p>}
            {catalog.error && <p role="alert" className="panel p-4">{catalog.error}</p>}
            {catalog.data && <CreateOpportunity catalog={catalog.data} onCreated={opportunities.reload} />}
            <div className="space-y-6">
              <section className="panel p-5">
                <h2 className="text-lg font-semibold">Received applications</h2>
                <button type="button" className="mt-1 text-sm text-accent hover:underline" onClick={applications.reload}>Refresh applications</button>
                {applications.loading && <p role="status" className="mt-3 text-muted">Loading applications…</p>}
                {applications.error && <p role="alert" className="mt-3">{applications.error}</p>}
                {applications.data?.length === 0 && <p className="mt-3 text-sm text-muted">No applications received yet.</p>}
                <ul className="mt-3 divide-y divide-line">
                  {applications.data?.map(({ id, athlete, opportunity, status }) => (
                    <li key={id} className="py-3">
                      <p className="font-medium">{athlete.name || "Athlete"}</p>
                      <p className="text-sm text-muted">{opportunity.title} · <span className="capitalize">{status}</span></p>
                    </li>
                  ))}
                </ul>
              </section>
              <section className="panel p-5">
                <h2 className="text-lg font-semibold">Posted opportunities</h2>
                {opportunities.loading && <p role="status" className="mt-3 text-muted">Loading postings…</p>}
                {opportunities.error && <p role="alert" className="mt-3">{opportunities.error}</p>}
                {opportunities.data?.length === 0 && <p className="mt-3 text-sm text-muted">Your published opportunities will appear here.</p>}
                <ul className="mt-3 max-h-96 divide-y divide-line overflow-y-auto">
                  {opportunities.data?.map((item) => (
                    <li key={item.id} className="py-3">
                      <Link href={`/opportunities/${item.id}`} className="font-medium text-accent hover:underline">{item.title}</Link>
                      <p className="text-sm capitalize text-muted">{item.sport} · {item.type}</p>
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}

function CreateOpportunity({ catalog, onCreated }: { catalog: Catalog; onCreated: () => void }) {
  const [sport, setSport] = useState(Object.keys(catalog.sports)[0]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const get = (key: string) => String(data.get(key) ?? "").trim();
    const int = (key: string) => get(key) ? Number(get(key)) : null;
    setBusy(true);
    setNotice("");
    setError("");
    try {
      const item = await post<Opportunity>("/opportunities", {
        title: get("title"), sport, type: get("type"), description: get("description"),
        age_min: int("min"), age_max: int("max"), city: get("city") || null,
        region: get("region") || null, level: get("level") || null,
        positions: get("position") ? [get("position")] : [],
        skills: get("skills").split(",").map((skill) => skill.trim()).filter(Boolean),
        deadline: get("deadline") ? new Date(get("deadline")).toISOString() : null,
        hard_age_limit: data.has("hard_age_limit"),
      });
      form.reset();
      setNotice(`Published: ${item.title}`);
      onCreated();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="panel grid gap-4 p-5" onSubmit={submit}>
      <h2 className="text-lg font-semibold">Create opportunity</h2>
      <Field label="Title"><input name="title" minLength={3} maxLength={160} className="field" required /></Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Sport"><select value={sport} onChange={(e) => setSport(e.target.value)} className="field capitalize">
          {Object.keys(catalog.sports).map((key) => <option key={key}>{key}</option>)}
        </select></Field>
        <Field label="Opportunity type"><select name="type" className="field">
          {Object.entries(catalog.types).map(([key, value]) => <option key={key} value={key}>{value}</option>)}
        </select></Field>
        <Field label="Position"><select name="position" key={sport} className="field capitalize">
          <option value="">All positions</option>
          {catalog.sports[sport].map((value) => <option key={value}>{value}</option>)}
        </select></Field>
        <Field label="Experience level"><select name="level" className="field capitalize">
          <option value="">Any level</option>
          {catalog.levels.map((value) => <option key={value}>{value}</option>)}
        </select></Field>
        <Field label="Minimum age"><input name="min" type="number" min={8} max={60} className="field" /></Field>
        <Field label="Maximum age"><input name="max" type="number" min={8} max={60} className="field" /></Field>
        <Field label="City"><input name="city" maxLength={80} className="field" placeholder="Leave blank for open or online" /></Field>
        <Field label="Region"><input name="region" maxLength={40} className="field" /></Field>
      </div>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="hard_age_limit" defaultChecked /> Enforce the stated age range for applications</label>
      <Field label="Required skills"><input className="field" name="skills" placeholder="Comma-separated skills" /></Field>
      <Field label="Description"><textarea className="field" name="description" minLength={10} maxLength={4000} rows={3} required /></Field>
      <Field label="Application deadline"><input className="field" type="datetime-local" name="deadline" /></Field>
      {error && <p role="alert" className="text-sm text-red-700 dark:text-red-300">{error}</p>}
      {notice && <p role="status" className="text-sm text-accent">{notice}</p>}
      <button type="submit" className="btn-primary justify-self-start" disabled={busy}>{busy ? "Publishing…" : "Publish opportunity"}</button>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="grid gap-1 text-sm"><span className="font-medium">{label}</span>{children}</label>;
}
