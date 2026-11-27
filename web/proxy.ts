import { NextResponse, type NextRequest } from "next/server";

// Optimistic gate only. The API re-checks the token on every call.
export function proxy(req: NextRequest) {
  const signedIn = req.cookies.has("gu_token");
  const onLogin = req.nextUrl.pathname === "/login";
  const publicPage = onLogin || req.nextUrl.pathname === "/evaluation";
  if (!signedIn && !publicPage) return NextResponse.redirect(new URL("/login", req.url));
}

export const config = {
  matcher: ["/((?!_next|favicon.ico|.*\\.(?:svg|png|jpg|ico)$).*)"],
};
