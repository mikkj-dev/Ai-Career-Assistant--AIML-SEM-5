import type { Match, Opportunity, Person, Post, Profile, User } from "./api";

// --- Explainable Recommendation Engine (Ported from api/app/matching.py) ---
const WEIGHTS = { position: 0.25, skills: 0.3, age: 0.15, location: 0.1, experience: 0.1, goals: 0.1 };
const LEVELS = ["beginner", "district", "state", "national", "professional"];
const AGE_TOLERANCE = 1;

const RELATED_POSITIONS: Set<string>[] = [
  new Set(["central midfielder", "attacking midfielder"]),
  new Set(["central midfielder", "defensive midfielder"]),
  new Set(["attacking midfielder", "winger"]),
  new Set(["winger", "striker"]),
  new Set(["centre back", "full back"]),
  new Set(["centre back", "defensive midfielder"]),
  new Set(["batter", "wicket keeper"]),
  new Set(["all rounder", "batter"]),
  new Set(["all rounder", "bowler"]),
  new Set(["point guard", "shooting guard"]),
  new Set(["small forward", "power forward"]),
  new Set(["sprinter", "hurdler"]),
];

const norm = (s: string | null | undefined) => (s || "").trim().toLowerCase();

export function eligible(athlete: Profile, opp: Opportunity): boolean {
  if (norm(athlete.sport) !== norm(opp.sport)) return false;
  if (athlete.age == null) return true;
  const lo = (opp.age_min ?? 0) - AGE_TOLERANCE;
  const hi = (opp.age_max ?? 200) + AGE_TOLERANCE;
  return athlete.age >= lo && athlete.age <= hi;
}

export function positionScore(pos: string | null, wanted: string[]): number {
  const wantedSet = new Set((wanted || []).map(norm));
  const p = norm(pos);
  if (wantedSet.size === 0) return 1.0;
  if (wantedSet.has(p)) return 1.0;
  for (const set of RELATED_POSITIONS) {
    if (set.has(p)) {
      for (const w of wantedSet) {
        if (set.has(w)) return 0.6;
      }
    }
  }
  return 0.0;
}

export function skillsScore(have: string[], want: string[]): number {
  const a = new Set((have || []).map(norm));
  const b = new Set((want || []).map(norm));
  if (b.size === 0) return 1.0;
  if (a.size === 0) return 0.0;
  let common = 0;
  for (const s of a) {
    if (b.has(s)) common++;
  }
  return common / Math.sqrt(a.size * b.size);
}

export function ageScore(age: number | null, lo: number | null, hi: number | null): number {
  if (age == null) return 0.5;
  if ((lo == null || age >= lo) && (hi == null || age <= hi)) return 1.0;
  return 0.5;
}

export function locationScore(athlete: Profile, opp: Opportunity): number {
  if (!opp.city) return 1.0;
  if (norm(athlete.city) === norm(opp.city)) return 1.0;
  if (athlete.region && norm(athlete.region) === norm(opp.city)) return 0.6;
  return 0.2;
}

export function experienceScore(have: string | null, want: string | null): number {
  if (!want || !LEVELS.includes(want) || !have || !LEVELS.includes(have)) {
    return !want ? 1.0 : 0.5;
  }
  const gap = Math.abs(LEVELS.indexOf(have) - LEVELS.indexOf(want));
  if (gap === 0) return 1.0;
  if (gap === 1) return 0.6;
  return 0.2;
}

export function goalsScore(goals: string | null, text: string | null): number {
  if (!goals || !text) return 0.5;
  const gWords = new Set(norm(goals).split(/\W+/).filter((w) => w.length > 3));
  const tWords = new Set(norm(text).split(/\W+/).filter((w) => w.length > 3));
  if (gWords.size === 0 || tWords.size === 0) return 0.5;
  let overlap = 0;
  for (const w of gWords) {
    if (tWords.has(w)) overlap++;
  }
  const sim = overlap / Math.sqrt(gWords.size * tWords.size);
  return Math.min(1.0, Math.max(0.3, Math.round(sim * 100) / 100 + 0.3));
}

export function combine(components: Record<string, number>): number {
  const sum =
    WEIGHTS.position * components.position +
    WEIGHTS.skills * components.skills +
    WEIGHTS.age * components.age +
    WEIGHTS.location * components.location +
    WEIGHTS.experience * components.experience +
    WEIGHTS.goals * components.goals;
  return Math.round(1000 * sum) / 10;
}

export function explain(components: Record<string, number>, athlete: Profile, opp: Opportunity, score: number): string[] {
  const head = score >= 80 ? "Strong match" : score >= 60 ? "Good match" : "Partial match";
  const reasons: string[] = [head];
  if (components.position === 1.0 && opp.positions.length > 0) reasons.push("Position matches");
  else if (components.position >= 0.6) reasons.push("Related position");

  const aSkills = new Set((athlete.skills || []).map(norm));
  const common = (opp.skills || []).filter((s) => aSkills.has(norm(s)));
  if (common.length > 0) reasons.push("Skill overlap on " + common.slice(0, 3).join(" and "));

  if (components.age === 1.0 && (opp.age_min || opp.age_max)) reasons.push("Age within range");
  if (components.location === 1.0 && opp.city) reasons.push("Same city");
  else if (components.location === 0.6) reasons.push("Same region");
  if (components.experience === 1.0 && opp.level) reasons.push("Level fits");

  return reasons;
}

export function rankMatches(athlete: Profile, pool: Opportunity[], k = 10): Match[] {
  const eligibleOpps = pool.filter((o) => eligible(athlete, o));
  const matches: Match[] = eligibleOpps.map((o) => {
    const c = {
      position: positionScore(athlete.position, o.positions),
      skills: Math.round(skillsScore(athlete.skills, o.skills) * 1000) / 1000,
      age: ageScore(athlete.age, o.age_min, o.age_max),
      location: locationScore(athlete, o),
      experience: experienceScore(athlete.level, o.level),
      goals: Math.round(goalsScore(athlete.goals, o.description) * 1000) / 1000,
    };
    const s = combine(c);
    return {
      opportunity: o,
      score: s,
      components: c,
      reasons: explain(c, athlete, o, s),
    };
  });
  matches.sort((a, b) => b.score - a.score);
  return matches.slice(0, k);
}

// --- Initial Mock Data Seed ---
export const DEFAULT_USER: User = {
  id: "u-arjun-01",
  email: "arjun.rawat@example.com",
  name: "Arjun Rawat",
  avatar_url: null,
  role: "athlete",
  mode: "professional",
  verification_status: "verified",
  profile: {
    sport: "football",
    position: "attacking midfielder",
    age: 19,
    city: "Delhi",
    region: "North",
    level: "state",
    skills: ["vision", "passing", "dribbling", "positioning", "stamina"],
    goals: "Compete at national trials, earn an academy scholarship and play professionally.",
    bio: "Attacking midfielder competing at Delhi state level. Focused on playmaking, vision and quick transitional play.",
  },
};

export const SCOUT_USER: User = {
  id: "u-vikram-02",
  email: "vikram.singh@rangers.example.com",
  name: "Coach Vikram Singh",
  avatar_url: null,
  role: "scout",
  mode: "professional",
  verification_status: "verified",
  profile: {
    sport: "football",
    position: "coach",
    age: 38,
    city: "Delhi",
    region: "North",
    level: "professional",
    skills: ["tactics", "scouting", "development"],
    goals: "Scouting young talent for Eastern Rangers FC academy.",
    bio: "Head Scout & Youth Academy Coach at Eastern Rangers FC.",
  },
};

export const INITIAL_OPPORTUNITIES: Opportunity[] = [
  {
    id: "opp-01",
    title: "Open Trial: Football U21",
    org: "Eastern Rangers FC",
    type: "trial",
    sport: "football",
    positions: ["attacking midfielder", "central midfielder", "winger"],
    age_min: 17,
    age_max: 21,
    city: "Delhi",
    level: "state",
    skills: ["passing", "vision", "dribbling", "stamina"],
    description: "Eastern Rangers FC is holding open trials for our U21 development squad. We are looking for creative midfielders and sharp wingers with strong tactical awareness.",
    deadline: "2026-12-15T18:00:00Z",
    synthetic: false,
  },
  {
    id: "opp-02",
    title: "Sports Scholarship: Elite Football Academy",
    org: "Riverside Academy",
    type: "scholarship",
    sport: "football",
    positions: ["central midfielder", "defensive midfielder", "attacking midfielder"],
    age_min: 16,
    age_max: 20,
    city: "Delhi",
    level: "state",
    skills: ["passing", "vision", "positioning"],
    description: "Full residential scholarship program covering training, gear, accommodation and education. Selected athletes will train under UEFA-licensed coaches.",
    deadline: "2026-11-30T18:00:00Z",
    synthetic: false,
  },
  {
    id: "opp-03",
    title: "Tournament Entry: Capital Youth Championship",
    org: "Capital Youth League",
    type: "tournament",
    sport: "football",
    positions: ["attacking midfielder", "striker", "winger"],
    age_min: 18,
    age_max: 23,
    city: "Delhi",
    level: "district",
    skills: ["dribbling", "finishing", "pace"],
    description: "Annual showcase tournament attended by scouts from top tier clubs across the country. Outstanding performers receive direct invites to state team trials.",
    deadline: "2026-12-05T18:00:00Z",
    synthetic: false,
  },
  {
    id: "opp-04",
    title: "High Performance Training Camp: Midfield Mastery",
    org: "Northgate Sports Club",
    type: "camp",
    sport: "football",
    positions: ["central midfielder", "attacking midfielder"],
    age_min: 16,
    age_max: 22,
    city: "Chandigarh",
    level: "state",
    skills: ["vision", "passing", "tackling"],
    description: "Intensive 3-week camp covering position-specific tactical drills, physical conditioning, and video analysis sessions with former national team players.",
    deadline: "2026-12-20T18:00:00Z",
    synthetic: true,
  },
  {
    id: "opp-05",
    title: "National Division Trials: Striker & Wing Showcase",
    org: "Coastal Sports Trust",
    type: "trial",
    sport: "football",
    positions: ["striker", "winger"],
    age_min: 18,
    age_max: 24,
    city: "Mumbai",
    level: "national",
    skills: ["finishing", "pace", "dribbling"],
    description: "Looking for dynamic forwards and wingers capable of playing at the national level. High work rate and finishing ability required.",
    deadline: "2027-01-10T18:00:00Z",
    synthetic: true,
  },
  {
    id: "opp-06",
    title: "Karnataka State League Scouting Camp",
    org: "Sahyadri Athletics",
    type: "camp",
    sport: "football",
    positions: ["goalkeeper", "centre back", "defensive midfielder"],
    age_min: 17,
    age_max: 22,
    city: "Bengaluru",
    level: "state",
    skills: ["positioning", "tackling", "heading"],
    description: "Focus on defensive organization, high pressing and tactical discipline. Match simulations against senior state league squads.",
    deadline: "2027-01-15T18:00:00Z",
    synthetic: true,
  },
  {
    id: "opp-07",
    title: "Junior Pace Academy Trials",
    org: "Kaveri Cricket Academy",
    type: "trial",
    sport: "cricket",
    positions: ["bowler", "all rounder"],
    age_min: 15,
    age_max: 21,
    city: "Bengaluru",
    level: "district",
    skills: ["pace bowling", "fitness"],
    description: "Comprehensive speed gun and biomechanics evaluation for aspiring fast bowlers looking to join state selection pools.",
    deadline: "2026-12-28T18:00:00Z",
    synthetic: false,
  },
  {
    id: "opp-08",
    title: "All-India Inter-Collegiate Basketball Invitational",
    org: "Deccan Hoops",
    type: "tournament",
    sport: "basketball",
    positions: ["point guard", "shooting guard", "small forward"],
    age_min: 17,
    age_max: 23,
    city: "Pune",
    level: "state",
    skills: ["shooting", "ball handling", "passing"],
    description: "Premier collegiate tournament with FIBA-certified referees and pro scout coverage. Live streamed nationally.",
    deadline: "2026-12-18T18:00:00Z",
    synthetic: false,
  },
  {
    id: "opp-09",
    title: "National Sprint & Hurdles Development Program",
    org: "Brahmaputra Sports Foundation",
    type: "scholarship",
    sport: "athletics",
    positions: ["sprinter", "hurdler"],
    age_min: 14,
    age_max: 20,
    city: "Guwahati",
    level: "national",
    skills: ["speed", "explosiveness", "technique"],
    description: "Full scholarship program for track athletes preparing for national junior athletics championships.",
    deadline: "2027-02-01T18:00:00Z",
    synthetic: false,
  },
];

export const INITIAL_POSTS: Post[] = [
  {
    id: "p-01",
    body: "Scoring 2 goals and setting up the winner in yesterday's Delhi State semi-final. Feeling sharp and ready for the final next weekend! Training focus this week: set pieces and box arrivals.",
    created_at: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
    author: { id: "u-arjun-01", name: "Arjun Rawat", role: "athlete" },
  },
  {
    id: "p-02",
    body: "Excited to announce that Eastern Rangers FC will be hosting open trials on Dec 15th for our U21 squad. Looking forward to seeing high quality midfield and winger talent. Spread the word!",
    created_at: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
    author: { id: "u-vikram-02", name: "Coach Vikram Singh", role: "scout" },
  },
  {
    id: "p-03",
    body: "Clocked a new personal best in the 200m today at Jawaharlal Nehru Stadium (21.84s). Hard work during winter training camp is paying off.",
    created_at: new Date(Date.now() - 1000 * 60 * 600).toISOString(),
    author: { id: "u-rohit-03", name: "Rohit Verma", role: "athlete" },
  },
  {
    id: "p-04",
    body: "Huge congratulations to our academy under-19 squad for qualifying for the National Youth Cup! Great discipline and work rate across all 90 minutes.",
    created_at: new Date(Date.now() - 1000 * 60 * 1440).toISOString(),
    author: { id: "u-ananya-04", name: "Coach Ananya Sen", role: "coach" },
  },
];

export const INITIAL_PEOPLE: Person[] = [
  { id: "p-1", name: "Devansh Sharma", position: "central midfielder", city: "Delhi", role: "athlete" },
  { id: "p-2", name: "Coach Vikram Singh", position: "Head Scout", city: "Delhi", role: "scout" },
  { id: "p-3", name: "Kunal Ghosh", position: "winger", city: "Delhi", role: "athlete" },
  { id: "p-4", name: "Rohan Nair", position: "defensive midfielder", city: "Chandigarh", role: "athlete" },
  { id: "p-5", name: "Coach Ananya Sen", position: "Academy Director", city: "Delhi", role: "coach" },
];

// --- Persistent Storage Helpers ---
const KEY_USER = "gu_mock_user";
const KEY_POSTS = "gu_mock_posts";
const KEY_OPPS = "gu_mock_opportunities";

function isClient(): boolean {
  return typeof window !== "undefined" && typeof localStorage !== "undefined";
}

export function getStoredUser(): User {
  if (!isClient()) return DEFAULT_USER;
  const raw = localStorage.getItem(KEY_USER);
  if (!raw) {
    localStorage.setItem(KEY_USER, JSON.stringify(DEFAULT_USER));
    return DEFAULT_USER;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return DEFAULT_USER;
  }
}

export function saveStoredUser(user: User): User {
  if (isClient()) {
    localStorage.setItem(KEY_USER, JSON.stringify(user));
  }
  return user;
}

export function getStoredPosts(): Post[] {
  if (!isClient()) return INITIAL_POSTS;
  const raw = localStorage.getItem(KEY_POSTS);
  if (!raw) {
    localStorage.setItem(KEY_POSTS, JSON.stringify(INITIAL_POSTS));
    return INITIAL_POSTS;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return INITIAL_POSTS;
  }
}

export function addStoredPost(body: string): Post {
  const user = getStoredUser();
  const newPost: Post = {
    id: `p-${Date.now()}`,
    body: body.trim(),
    created_at: new Date().toISOString(),
    author: {
      id: user.id,
      name: user.name || "Athlete",
      role: user.role,
    },
  };
  const list = [newPost, ...getStoredPosts()];
  if (isClient()) {
    localStorage.setItem(KEY_POSTS, JSON.stringify(list));
  }
  return newPost;
}

export function getStoredOpportunities(): Opportunity[] {
  if (!isClient()) return INITIAL_OPPORTUNITIES;
  const raw = localStorage.getItem(KEY_OPPS);
  if (!raw) {
    localStorage.setItem(KEY_OPPS, JSON.stringify(INITIAL_OPPORTUNITIES));
    return INITIAL_OPPORTUNITIES;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return INITIAL_OPPORTUNITIES;
  }
}
