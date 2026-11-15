"use client";
import Script from "next/script";
import { useState } from "react";
import { DeviceMobile, Lightning, ShieldCheck, Sparkle, UserCircle } from "@phosphor-icons/react";
import { post, setToken, type User } from "@/lib/api";
import { Logo } from "@/components/app-shell";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

type Session = { token: string; user: User };

function next(user: User) {
  if (user.verification_status === "unverified") return "/onboarding/verify";
  if (!user.profile?.sport) return "/onboarding/profile";
  return "/";
}

declare global {
  interface Window {
    google?: { accounts: { id: { initialize: (o: object) => void; renderButton: (el: HTMLElement, o: object) => void } } };
  }
}

export default function LoginPage() {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showCustom, setShowCustom] = useState(false);

  async function finish(p: Promise<Session>) {
    setBusy(true);
    setError(null);
    try {
      const s = await p;
      setToken(s.token);
      location.href = next(s.user);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  function initGoogle() {
    const el = document.getElementById("google-btn");
    if (!window.google || !el || !GOOGLE_CLIENT_ID) return;
    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: (r: { credential: string }) => finish(post<Session>("/auth/google", { credential: r.credential })),
    });
    window.google.accounts.id.renderButton(el, { theme: "outline", size: "large", width: 320, text: "continue_with" });
  }

  const loginDemoAthlete = () =>
    finish(post<Session>("/auth/dev", { email: "arjun.rawat@example.com", name: "Arjun Rawat" }));

  const loginDemoScout = () =>
    finish(post<Session>("/auth/dev", { email: "vikram.singh@rangers.example.com", name: "Coach Vikram Singh" }));

  return (
    <div className="grid min-h-[100dvh] md:grid-cols-[1.1fr_1fr]">
      {/* Left hero panel with reliable background gradient and graphics */}
      <section className="relative hidden overflow-hidden bg-gradient-to-br from-zinc-950 via-zinc-900 to-emerald-950 md:flex md:flex-col md:justify-between md:p-12">
        {/* Subtle athletic field pitch lines */}
        <div className="pointer-events-none absolute inset-0 opacity-20">
          <svg className="size-full stroke-emerald-500/40" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
                <path d="M 60 0 L 0 0 0 60" fill="none" strokeWidth="0.8" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            <circle cx="50%" cy="50%" r="140" fill="none" strokeWidth="1.5" />
            <line x1="0" y1="50%" x2="100%" y2="50%" strokeWidth="1.5" />
          </svg>
        </div>

        {/* Ambient stadium lighting glow */}
        <div className="pointer-events-none absolute -bottom-24 -left-24 size-96 rounded-full bg-emerald-500/15 blur-3xl" />
        <div className="pointer-events-none absolute -top-24 -right-24 size-96 rounded-full bg-accent/20 blur-3xl" />

        {/* Hero image with graceful fallback to styled background if picsum is blocked */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="https://picsum.photos/seed/groundup-athlete-track/1200/1600?grayscale"
          alt=""
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
          className="absolute inset-0 size-full object-cover mix-blend-overlay opacity-60"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-black/40" />

        {/* Top badge */}
        <div className="relative z-10 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">
          <Sparkle size={16} weight="fill" />
          Sports AI Career Assistant
        </div>

        {/* Bottom hero copy */}
        <div className="relative z-10 max-w-lg">
          <p className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-950/40 px-3 py-1 text-xs text-emerald-300 backdrop-blur">
            <ShieldCheck size={14} weight="fill" /> Explainable athlete-to-opportunity matching
          </p>
          <p className="mt-4 text-3xl font-semibold leading-tight tracking-tight text-white lg:text-4xl">
            Trials, scholarships and tournaments that actually fit you.
          </p>
          <p className="mt-3 text-sm text-zinc-300">
            Transparent scoring on position, skills, age, location, and career goals.
          </p>
        </div>
      </section>

      {/* Right sign-in form */}
      <section className="flex flex-col justify-center px-6 py-12 sm:px-16">
        <div className="mx-auto w-full max-w-sm">
          <Logo />
          <h1 className="mt-10 text-3xl font-semibold tracking-tight">Sign in</h1>
          <p className="mt-2 text-muted">Build your profile once. We rank opportunities for you and tell you why.</p>

          <div className="mt-8 flex flex-col gap-3">
            {/* 1-Click Demo Login: Instant, reliable access */}
            <button
              onClick={loginDemoAthlete}
              disabled={busy}
              className="btn-primary flex w-full items-center justify-center gap-2.5 py-3 text-sm font-medium shadow-md shadow-accent/15"
            >
              <Lightning size={18} weight="fill" />
              <span>Continue as Demo Athlete (Arjun Rawat)</span>
            </button>

            <button
              onClick={loginDemoScout}
              disabled={busy}
              className="btn-ghost flex w-full items-center justify-center gap-2 text-sm"
            >
              <UserCircle size={18} />
              <span>Continue as Scout (Coach Vikram)</span>
            </button>

            {/* Google OAuth (if configured) */}
            {GOOGLE_CLIENT_ID ? (
              <div className="mt-2">
                <Script src="https://accounts.google.com/gsi/client" onReady={initGoogle} />
                <div id="google-btn" className="min-h-10" />
              </div>
            ) : null}

            {/* Phone option */}
            <button className="btn-ghost w-full opacity-60" disabled title="Coming soon">
              <DeviceMobile size={18} /> Phone number (coming soon)
            </button>

            {/* Toggle custom credentials */}
            <div className="mt-2 text-center">
              <button
                type="button"
                onClick={() => setShowCustom((prev) => !prev)}
                className="text-xs text-muted hover:text-ink underline underline-offset-4"
              >
                {showCustom ? "Hide custom login" : "Sign in with another name / email"}
              </button>
            </div>
          </div>

          {/* Expandable Custom Sign-in Form */}
          {showCustom && (
            <form
              className="mt-6 flex flex-col gap-3 rounded-2xl border border-line bg-surface/50 p-4"
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                finish(post<Session>("/auth/dev", { email: f.get("email"), name: f.get("name") }));
              }}
            >
              <label htmlFor="name" className="text-xs font-medium text-muted">Full Name</label>
              <input id="name" name="name" type="text" required defaultValue="Arjun Rawat" className="field text-sm" />
              <label htmlFor="email" className="text-xs font-medium text-muted">Email address</label>
              <input id="email" name="email" type="email" required defaultValue="arjun.rawat@example.com" className="field text-sm" />
              <button className="btn-primary mt-1" disabled={busy}>Sign in</button>
            </form>
          )}

          {error && <p role="alert" className="mt-4 rounded-lg bg-red-500/10 p-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
        </div>
      </section>
    </div>
  );
}
