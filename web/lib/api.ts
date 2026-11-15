import {
  DEFAULT_USER,
  INITIAL_PEOPLE,
  addStoredPost,
  getStoredOpportunities,
  getStoredPosts,
  getStoredUser,
  rankMatches,
  saveStoredUser,
} from "./mock-data";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";
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
  level: string | null;
  skills: string[];
  description: string | null;
  deadline: string | null;
  synthetic: boolean;
};

export type Match = {
  opportunity: Opportunity;
  score: number;
  components: Record<string, number>;
  reasons: string[];
};

export type Post = {
  id: string;
  body: string;
  created_at: string;
  author: { id: string; name: string | null; role: string };
};

export type Person = {
  id: string;
  name: string | null;
  position: string | null;
  city: string | null;
  role: string;
};

export function getToken(): string | null {
  if (typeof document === "undefined") return null;
  return document.cookie.match(new RegExp(`(?:^|; )${COOKIE}=([^;]*)`))?.[1] ?? null;
}

export function setToken(token: string | null) {
  const secure = typeof location !== "undefined" && location.protocol === "https:" ? "; secure" : "";
  if (typeof document !== "undefined") {
    document.cookie = token
      ? `${COOKIE}=${token}; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax${secure}`
      : `${COOKIE}=; path=/; max-age=0`;
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

// Fallback Mock Request Handler: executes in-browser when backend is not deployed/offline
function handleMockRequest<T>(path: string, init: RequestInit = {}): T | null {
  const [pathname, search] = path.split("?");
  const method = (init.method || "GET").toUpperCase();
  const rawBody = typeof init.body === "string" ? JSON.parse(init.body) : {};

  // Auth: Dev login
  if (pathname === "/auth/dev" && method === "POST") {
    const user = getStoredUser();
    const updated = saveStoredUser({
      ...user,
      email: rawBody.email || user.email,
      name: rawBody.name || user.name,
      verification_status: "verified",
    });
    return { token: `gu_mock_token_${Date.now()}`, user: updated } as T;
  }

  // Auth: Google login
  if (pathname === "/auth/google" && method === "POST") {
    const user = getStoredUser();
    return { token: `gu_mock_token_${Date.now()}`, user } as T;
  }

  // Me
  if (pathname === "/me" && method === "GET") {
    return getStoredUser() as T;
  }

  // Profile update
  if (pathname === "/me/profile" && method === "PUT") {
    const current = getStoredUser();
    const p = current.profile ?? DEFAULT_USER.profile!;
    const updatedUser: User = {
      ...current,
      name: rawBody.name ?? current.name,
      role: rawBody.role ?? current.role,
      mode: rawBody.mode ?? current.mode,
      profile: {
        ...p,
        sport: rawBody.sport ?? p.sport,
        position: rawBody.position ?? p.position,
        age: rawBody.age != null ? Number(rawBody.age) : p.age,
        city: rawBody.city ?? p.city,
        region: rawBody.region ?? p.region,
        level: rawBody.level ?? p.level,
        skills: Array.isArray(rawBody.skills) ? rawBody.skills : p.skills,
        goals: rawBody.goals ?? p.goals,
        bio: rawBody.bio ?? p.bio,
      },
    };
    return saveStoredUser(updatedUser) as T;
  }

  // Verification
  if (pathname === "/me/verification" && method === "POST") {
    const current = getStoredUser();
    const updatedUser: User = {
      ...current,
      verification_status: "verified",
    };
    return saveStoredUser(updatedUser) as T;
  }

  // Posts Feed
  if (pathname === "/posts") {
    if (method === "GET") {
      return getStoredPosts() as T;
    }
    if (method === "POST") {
      const p = addStoredPost(rawBody.body || "");
      return { id: p.id } as T;
    }
  }

  // Opportunities
  if (pathname === "/opportunities/recommended" && method === "GET") {
    const user = getStoredUser();
    const params = new URLSearchParams(search || "");
    const k = Number(params.get("k")) || 10;
    const opps = getStoredOpportunities();
    const p = user.profile ?? DEFAULT_USER.profile!;
    return rankMatches(p, opps, k) as T;
  }

  if (pathname === "/opportunities" && method === "GET") {
    return getStoredOpportunities() as T;
  }

  // People
  if (pathname === "/people/suggested" && method === "GET") {
    return INITIAL_PEOPLE as T;
  }

  return null;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();

  // If API_URL is provided, attempt live fetch first
  if (API_URL) {
    try {
      const res = await fetch(`${API_URL}${path}`, {
        ...init,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...init.headers,
        },
      });

      if (res.status === 401 && token) {
        setToken(null);
        if (typeof location !== "undefined") {
          location.href = "/login";
        }
      }

      if (res.ok) {
        return await res.json();
      }

      // If backend is not deployed / returning 404/5xx, fall back to mock engine
      if (res.status === 404 || res.status >= 500) {
        const mock = handleMockRequest<T>(path, init);
        if (mock !== null) return mock;
      }

      const body = await res.json().catch(() => ({}));
      throw new ApiError(res.status, typeof body.detail === "string" ? body.detail : "Something went wrong");
    } catch (networkError) {
      // Backend unreachable / DNS resolution failed / CORS blocked: seamlessly fallback to mock
      const mock = handleMockRequest<T>(path, init);
      if (mock !== null) return mock;
      throw networkError;
    }
  }

  // If no API_URL is defined, execute through mock engine
  const mock = handleMockRequest<T>(path, init);
  if (mock !== null) return mock;
  throw new Error(`Endpoint not found: ${path}`);
}

export const post = <T>(path: string, body: unknown, method = "POST") =>
  api<T>(path, { method, body: JSON.stringify(body) });
