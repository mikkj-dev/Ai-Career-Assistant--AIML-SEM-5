"use client";
import { AppShell } from "@/components/app-shell";
import { API_URL } from "@/lib/api";
import { useApi } from "@/lib/use-api";

const METRICS = ["Precision@5", "Recall@5", "NDCG@5", "Precision@10", "Recall@10", "NDCG@10"];
type MethodRow = { id: string; name: string; metrics: Record<string, number>; ci95: Record<string, [number, number]> };
type Evaluation = {
  dataset: { as_of: string; counts: Record<string, number>; candidate_pairs: number; profiles_with_no_candidates: number; profiles_with_no_relevant_items: number };
  methodology: { label_source: string; threshold: number; aggregation: string; candidate_policy: string; bootstrap_resamples: number; random_shuffles_per_profile: number };
  weights: Record<string, number>;
  models: MethodRow[];
  ablations: (MethodRow & { delta_ndcg10: number })[];
  semantic_status: string;
  paired_tfidf_minus_filter: Pick<MethodRow, "metrics" | "ci95">;
  weight_sensitivity: { samples: number; min: number; median: number; max: number };
};
type LiveModel = { active: string; configured: string; weights: Record<string, number> };
const LABELS: Record<string, string> = { position: "Position", skills: "Skills", age: "Age", location: "Location", experience: "Experience", goals: "Goals" };
const MODEL_NAMES: Record<string, string> = { tfidf: "TF-IDF", "sentence-bert": "Sentence-BERT" };
const number = (value: number) => value.toFixed(3);
const signed = (value: number) => `${value > 0 ? "+" : ""}${number(value)}`;

export default function EvaluationPage() {
  const result = useApi<Evaluation>("/evaluation/results");
  const runtime = useApi<LiveModel>("/evaluation/model");
  const data = result.data;
  return (
    <AppShell>
      <h1 className="text-3xl font-semibold tracking-tight">ML evaluation</h1>
      <p className="mt-2 max-w-prose text-muted">Compare the quality of opportunity rankings on the fixed synthetic benchmark.</p>
      {result.loading && <p className="mt-6 text-muted" role="status">Loading evaluation results…</p>}
      {result.error && <div className="panel mt-6 space-y-3 p-5">
        <p role="alert">{result.error}</p><button className="btn-ghost" onClick={result.reload}>Retry</button>
      </div>}
      {data && (
        <div className="mt-6 grid gap-6">
          <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {[["Athletes", data.dataset.counts.athletes], ["Opportunities", data.dataset.counts.opportunities],
              ["Eligible candidate pairs", data.dataset.candidate_pairs], ["Relevance labels", data.dataset.counts.relevance_labels]].map(([label, value]) => (
              <div key={label} className="panel p-4 sm:p-5"><dt className="text-sm text-muted">{label}</dt>
                <dd className="mt-1 text-2xl font-semibold">{value.toLocaleString("en-IN")}</dd></div>
            ))}
          </dl>
          <section className="panel space-y-3 p-5">
            <h2 className="text-lg font-semibold">Compatibility scoring</h2>
            <p className="text-sm">Live text method · {runtime.data ? MODEL_NAMES[runtime.data.active] : runtime.error ? "Unavailable" : "Checking…"}</p>
            {runtime.data && runtime.data.active !== runtime.data.configured && <p className="text-sm text-muted">The configured semantic model is unavailable. The app is using TF-IDF.</p>}
            <p className="rounded-lg bg-bg p-3 font-mono text-sm break-words">
              Score = 100 × ({Object.entries(runtime.data?.weights ?? data.weights).map(([key, value]) => `${value.toFixed(2)} × ${LABELS[key]}`).join(" + ")})
            </p>
            <p className="text-sm text-muted">Each component ranges from 0 to 1. The benchmark evaluates the ranking of compatible postings.</p>
          </section>
          <section className="panel space-y-4 p-5">
            <h2 className="text-lg font-semibold">Model comparison</h2>
            <p className="text-sm text-muted">Primary metric · NDCG@10</p>
            <MetricsTable rows={data.models} />
            <p className="text-sm">
              Weighted TF-IDF minus filter-only NDCG@10 · {signed(data.paired_tfidf_minus_filter.metrics["NDCG@10"])}.
              95% paired bootstrap interval {data.paired_tfidf_minus_filter.ci95["NDCG@10"].map(signed).join(" to ")}.
            </p>
            {data.semantic_status !== "evaluated" && <p className="text-sm text-muted">Sentence-BERT results are unavailable for this benchmark run.</p>}
            <Figure name="model_comparison" alt="Bar chart of NDCG at 5 and 10 for each evaluated model, with bootstrap intervals" />
          </section>
          <section className="panel space-y-4 p-5">
            <h2 className="text-lg font-semibold">Ablation study</h2>
            <p className="text-sm text-muted">Each variant removes one feature group and renormalizes the remaining weights. All variants keep the same eligibility checks.</p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-line text-muted"><tr><th scope="col" className="py-2">Variant</th>
                  <th scope="col" className="p-2 text-right">NDCG@10</th><th scope="col" className="py-2 text-right">Change</th></tr></thead>
                <tbody className="divide-y divide-line">
                  {data.ablations.map((row) => (
                    <tr key={row.id}><th scope="row" className="py-2 font-medium">{row.name}</th>
                      <td className="p-2 text-right tabular-nums">{number(row.metrics["NDCG@10"])}</td>
                      <td className="py-2 text-right tabular-nums">{signed(row.delta_ndcg10)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Figure name="ablation_study" alt="Change in NDCG at 10 for each removed feature and equal weights" />
          </section>
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="panel space-y-3 p-5">
              <h2 className="text-lg font-semibold">Score distribution</h2>
              <Figure name="score_distribution" alt="Histogram of TF-IDF compatibility scores across eligible pairs" />
            </section>
            <section className="panel space-y-3 p-5">
              <h2 className="text-lg font-semibold">Dataset composition</h2>
              <Figure name="dataset_distribution" alt="Athlete counts by sport and opportunity counts by type" />
            </section>
          </div>
          <section className="panel space-y-3 p-5">
            <h2 className="text-lg font-semibold">Methodology and limitations</h2>
            <p className="text-sm">{data.methodology.candidate_policy}</p>
            <p className="text-sm">{data.methodology.label_source}, grades 0–3. A grade of {data.methodology.threshold} or higher counts as relevant for precision and recall.</p>
            <p className="text-sm">{data.methodology.aggregation} The dataset includes {data.dataset.profiles_with_no_candidates} profiles with no candidates and {data.dataset.profiles_with_no_relevant_items} profiles with no relevant items.</p>
            <p className="text-sm">Random averages {data.methodology.random_shuffles_per_profile} shuffles per profile. Confidence intervals use {data.methodology.bootstrap_resamples.toLocaleString()} athlete resamples. Benchmark date · {data.dataset.as_of.slice(0, 10)}.</p>
            <p className="text-sm text-muted">The labels reflect designed rules about intent, travel, readiness and role. Their assumptions influence the results. Human-rated relevance and real-world validation remain open.</p>
          </section>
        </div>
      )}
    </AppShell>
  );
}

function MetricsTable({ rows }: { rows: MethodRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full whitespace-nowrap text-left text-sm">
        <thead className="border-b border-line text-muted">
          <tr><th scope="col" className="py-2 pr-4">Method</th>
            {METRICS.map((metric) => <th scope="col" key={metric} className="px-2 py-2 text-right">{metric}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((row) => <tr key={row.id}><th scope="row" className="py-3 pr-4 font-medium">{row.name}</th>
            {METRICS.map((metric) => <td key={metric} className="px-2 py-3 text-right tabular-nums">{number(row.metrics[metric])}</td>)}</tr>)}
        </tbody>
      </table>
    </div>
  );
}

function Figure({ name, alt }: { name: string; alt: string }) {
  return (
    // Generated benchmark plots are served by FastAPI and sized by their containing panel.
    // eslint-disable-next-line @next/next/no-img-element
    <img src={`${API_URL}/evaluation/plots/${name}`} alt={alt} loading="lazy" className="w-full rounded-lg bg-white" />
  );
}
