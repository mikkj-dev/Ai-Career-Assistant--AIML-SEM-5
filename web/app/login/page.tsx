"use client";
import Link from "next/link";
import Script from "next/script";
import { useState } from "react";
import { Lightning, ShieldCheck, Sparkle } from "@phosphor-icons/react";
import { post, setToken, type DemoInfo, type User } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { Logo } from "@/components/app-shell";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
type Session = { token: string; user: User };

function destination(user: User) {
  if (user.organisation_name) return "/organisation";
  if (user.synthetic && !user.profile?.sport) return "/onboarding/profile";
  if (!user.synthetic && user.verification_status === "unverified") return "/onboarding/verify";
  return user.profile?.sport ? "/" : "/onboarding/profile";
}

declare global {
  interface Window {
    google?: { accounts: { id: { initialize: (options: object) => void; renderButton: (el: HTMLElement, options: object) => void } } };
  }
}

export default function LoginPage() {
  const demo = useApi<DemoInfo>("/demo/info");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function finish(session: Promise<Session>) {
    setBusy(true);
    setError(null);
    try {
      const { token, user } = await session;
      setToken(token);
      location.assign(destination(user));
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  function initGoogle() {
    const el = document.getElementById("google-btn");
    if (!window.google || !el || !GOOGLE_CLIENT_ID) return;
    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: (result: { credential: string }) => {
        void finish(post<Session>("/auth/google", { credential: result.credential }));
      },
    });
    window.google.accounts.id.renderButton(el, { theme: "outline", size: "large", width: 280, text: "continue_with" });
  }

  return (
    <div className="grid min-h-[100dvh] md:grid-cols-[1.1fr_1fr]">
      <section className="relative hidden overflow-hidden bg-gradient-to-br from-zinc-950 via-zinc-900 to-emerald-950 md:flex md:flex-col md:justify-between md:p-12">
        <div aria-hidden className="pointer-events-none absolute inset-0 opacity-20"
          style={{ backgroundImage: "linear-gradient(#34d39955 1px, transparent 1px), linear-gradient(90deg, #34d39955 1px, transparent 1px)", backgroundSize: "60px 60px" }} />
        <div className="pointer-events-none absolute -bottom-24 -left-24 size-96 rounded-full bg-emerald-500/15 blur-3xl" />
        <div className="pointer-events-none absolute -top-24 -right-24 size-96 rounded-full bg-accent/20 blur-3xl" />
        <div className="relative z-10 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">
          <Sparkle size={16} weight="fill" /> Sports AI Career Assistant
        </div>
        <div className="relative z-10 max-w-lg">
          <p className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-950/40 px-3 py-1 text-xs text-emerald-300">
            <ShieldCheck size={14} weight="fill" /> Explainable opportunity matching
          </p>
          <p className="mt-4 text-3xl font-semibold leading-tight tracking-tight text-white lg:text-4xl">
            Find sports opportunities that fit your profile.
          </p>
          <p className="mt-3 text-sm text-zinc-300">Explore trials, scholarships, tournaments and training programmes.</p>
        </div>
      </section>

      <section className="flex flex-col justify-center px-6 py-12 sm:px-16">
        <div className="mx-auto w-full max-w-sm">
          <Logo />
          <h1 className="mt-10 text-3xl font-semibold tracking-tight">Sign in</h1>
          <p className="mt-2 text-muted">Build your profile and see ranked opportunities with an explanation for each match.</p>
          {demo.loading && <p className="mt-6 text-sm text-muted" role="status">Checking local demo availability…</p>}
          {demo.error && (
            <div className="mt-6 space-y-2">
              <p role="alert" className="text-sm text-red-600 dark:text-red-400">{demo.error}</p>
              <button className="btn-ghost" onClick={demo.reload}>Retry</button>
            </div>
          )}
          {demo.data?.enabled && (
            <section aria-labelledby="demo-heading" className="mt-7 space-y-3">
              <h2 id="demo-heading" className="font-semibold">Local demo accounts</h2>
              <p className="text-sm text-muted">Choose a fictional account. Profile edits and applications are saved to the local database.</p>
              {!demo.data.accounts.length && <p className="text-sm text-muted">Load the demo fixtures to make accounts available.</p>}
              {demo.data.accounts.map(({ id, label }, index) => (
                <button key={id} disabled={busy} className={`${index === 0 ? "btn-primary" : "btn-ghost"} w-full`}
                  onClick={() => void finish(post<Session>("/auth/demo", { account: id }))}>
                  {index === 0 && <Lightning size={16} weight="fill" />} {label}
                </button>
              ))}
            </section>
          )}
          {GOOGLE_CLIENT_ID && (
            <div className="mt-5">
              <Script src="https://accounts.google.com/gsi/client" onReady={initGoogle} />
              <div id="google-btn" className="min-h-10" />
            </div>
          )}
          {demo.data && !demo.data.enabled && !GOOGLE_CLIENT_ID && <p className="mt-5 text-sm text-muted">Sign-in is unavailable on this instance.</p>}
          {error && <p role="alert" className="mt-4 rounded-lg bg-red-500/10 p-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
          <Link href="/evaluation" className="mt-6 inline-block text-sm text-accent hover:underline">View ML evaluation</Link>
        </div>
      </section>
    </div>
  );
}
