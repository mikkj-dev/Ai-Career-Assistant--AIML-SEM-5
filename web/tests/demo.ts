import { expect, type Page } from "@playwright/test";
import { resolve } from "node:path";

export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export async function signIn(page: Page, account: string, destination: string) {
  await page.goto("/login");
  const response = page.waitForResponse((res) => res.url() === `${API}/auth/demo` && res.request().method() === "POST");
  await page.getByRole("button", { name: account, exact: true }).click();
  expect((await response).ok()).toBe(true);
  await expect(page).toHaveURL(destination);
}

export async function capture(page: Page, name: string, fullPage = false) {
  if (process.env.GROUNDUP_CAPTURE_SCREENSHOTS !== "1") return;
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: resolve("..", "docs", "screenshots", name), fullPage, animations: "disabled" });
}
