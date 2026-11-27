export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001").replace(/\/$/, "");
const COOKIE = "gu_token";

export type Profile = {
  sport: string | null;
  position: string | null;
  age: number | null;
  city: string | null;
  region: string | null;
  level: string | null;
  skills: string[];
  goals: string | null;
  bio: string | null;
};

export type User = {
  id: string;
  email: string | null;
  name: string | null;
  avatar_url: string | null;
  role: string;
  mode: string;
  verification_status: "unverified" | "pending" | "verified" | "rejected";
  organisation_name: string | null;
  synthetic: boolean;
  profile: Profile | null;
};

export type Opportunity = {
  id: string;
  title: string;
  org: string;
  type: string;
  sport: string;
  positions: string[];
  age_min: number | null;
  age_max: number | null;
  city: string | null;
  region: string | null;
  level: string | null;
  skills: string[];
  description: string | null;
  deadline: string | null;
  synthetic: boolean;
  hard_age_limit: boolean;
};

export type Eligibility = "strict" | "age_tolerance" | "age_unknown" | "age_ineligible" | "closed" | "different_sport" | "profile_required";

export const eligibilityLabel: Record<Eligibility, string> = {
  strict: "Meets sport and age requirements",
  age_tolerance: "One year outside the stated age range",
  age_unknown: "Add your age to confirm eligibility",
  age_ineligible: "Outside the eligible age range",
  closed: "Application deadline has passed",
  different_sport: "Opportunity is for a different sport",
  profile_required: "An athlete profile is needed to check eligibility",
};

export type Match = {
  opportunity: Opportunity;
  score: number;
  compatibility_score: number;
  components: Record<string, number>;
  reasons: string[];
  eligibility: Eligibility;
  can_apply: boolean;
  matching_skills: string[];
  missing_skills: string[];
  similarity_method: "tfidf" | "sentence-bert";
};

export type Application = {
  id: string;
  status: string;
  created_at: string;
  opportunity: Opportunity;
  athlete: Pick<User, "id" | "name">;
};

export type OpportunityDetail = {
  opportunity: Opportunity;
  match: Match | null;
  eligibility: Eligibility;
  application: Application | null;
};

export type Catalog = { sports: Record<string, string[]>; types: Record<string, string>; levels: string[] };
export type DemoInfo = { enabled: boolean; accounts: { id: string; label: string }[] };
export type Post = {
  id: string;
  body: string;
  created_at: string;
  synthetic: boolean;
  author: Pick<User, "id" | "name" | "avatar_url" | "role">;
};
export type Person = Pick<User, "id" | "name" | "avatar_url" | "role"> & { position: string | null; city: string | null };

export function getToken(): string | null {
  if (typeof document === "undefined") return null;
  return document.cookie.split("; ").find((entry) => entry.startsWith(COOKIE + "="))?.slice(COOKIE.length + 1) ?? null;
}

export function setToken(token: string | null) {
  const secure = location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${COOKIE}=${token ?? ""}; Path=/; SameSite=Lax; Max-Age=${token ? 604800 : 0}${secure}`;
}

export function endSession() {
  setToken(null);
  // A document navigation discards all private data held in the previous session's router cache.
  location.replace(new URL("/login", location.origin).href);
}

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body) headers.set("Content-Type", "application/json");
  let response: Response;
  try {
    response = await fetch(API_URL + path, { ...init, headers, cache: "no-store" });
  } catch (error) {
    if (init.signal?.aborted) throw error;
    throw new ApiError(0, "Could not reach the Ground Up API. Check that it is running and try again.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    if (response.status === 401 && token && !path.startsWith("/auth/")) {
      endSession();
    }
    const detail = body?.detail;
    const message = typeof detail === "string" ? detail
      : Array.isArray(detail) ? detail.map((item: { loc?: unknown[]; msg: string }) =>
        [item.loc?.slice(1).join(" "), item.msg].filter(Boolean).join(" · ")).join(". ")
      : `Request failed (${response.status})`;
    throw new ApiError(response.status, message);
  }
  return response.json();
}

export const post = <T>(path: string, body?: unknown, method = "POST") =>
  api<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });
