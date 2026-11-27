import { expect, test } from "@playwright/test";
import { API, capture, signIn } from "./demo";
import type { Match } from "../lib/api";

test("profile changes rerank matches, applications persist and organisations receive them", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await signIn(page, "Football athlete", "/");
  await expect(page.getByText("Local demo account")).toBeVisible();
  await expect(page.getByText("People you may know")).toBeVisible();
  await expect(page.getByText("passing, vision", { exact: false }).first()).toBeVisible();
  await capture(page, "athlete-dashboard.png");

  const firstResponse = page.waitForResponse((res) => res.url() === `${API}/opportunities/recommended?k=100`);
  await page.getByRole("link", { name: "Opportunities", exact: true }).click();
  const first = (await (await firstResponse).json()) as Match[];
  expect(first[0].opportunity.title).toContain("Juniperline 001");
  const firstCard = page.getByRole("button", { name: /Juniperline 001, match score/ });
  await expect(firstCard).toBeVisible();
  await capture(page, "opportunity-gallery.png");
  await firstCard.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("region", { name: "Score breakdown" }).locator(":scope > div")).toHaveCount(6);
  await expect(dialog.getByText("Matching skills", { exact: false })).toBeAttached();
  await expect(dialog.getByRole("button", { name: "Apply", exact: true })).toBeVisible();
  await capture(page, "opportunity-detail.png");
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(firstCard).toBeFocused();

  await page.getByRole("link", { name: "Edit athlete profile" }).click();
  await page.getByLabel("Position").selectOption("winger");
  await page.getByLabel("Skills").fill("dribbling, pace, crossing");
  await page.getByLabel("Goals").fill("I want an academy trial for wide attackers with crossing, dribbling, and pace.");
  const updatedResponse = page.waitForResponse((res) => res.url() === `${API}/opportunities/recommended?k=100`);
  await page.getByRole("button", { name: "Save profile" }).click();
  const updated = (await (await updatedResponse).json()) as Match[];
  expect(updated[0].opportunity.id).not.toBe(first[0].opportunity.id);
  const wide = updated.find(({ opportunity }) => opportunity.title.includes("Juniperline 016"))!;
  expect(wide.can_apply).toBe(true);
  expect(wide.components.skills).toBe(1);

  await page.getByRole("button", { name: /Juniperline 016, match score/ }).click();
  const submission = page.waitForResponse((res) => res.url().endsWith(`/opportunities/${wide.opportunity.id}/apply`) && res.request().method() === "POST");
  await dialog.getByRole("button", { name: "Apply", exact: true }).click();
  expect((await submission).status()).toBe(201);
  await expect(dialog.getByText("Application submitted", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();

  await page.getByRole("link", { name: "Applications", exact: true }).click();
  await expect(page.getByRole("link", { name: wide.opportunity.title })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("link", { name: wide.opportunity.title })).toBeVisible();
  await capture(page, "application-history.png");

  await page.getByRole("button", { name: "Sign out" }).click();
  await signIn(page, "Organisation administrator", "/organisation");
  const inbox = page.locator("section").filter({ has: page.getByRole("heading", { name: "Received applications" }) });
  await expect(inbox.getByText(wide.opportunity.title, { exact: false })).toBeVisible();
  const title = `Live demo development session ${Date.now()}`;
  await page.getByLabel("Title").fill(title);
  await page.getByLabel("Description").fill("A fictional academy session for athletes who want position-specific development.");
  await page.getByLabel("Opportunity type").selectOption("development");
  await page.getByRole("button", { name: "Publish opportunity" }).click();
  await expect(page.getByText(`Published: ${title}`)).toBeVisible();
  await expect(page.getByRole("link", { name: title })).toBeVisible();
  await capture(page, "organisation-dashboard.png");

  await page.getByRole("link", { name: "Evaluation", exact: true }).click();
  await expect(page.getByRole("heading", { name: "ML evaluation" })).toBeVisible();
  await expect(page.getByRole("rowheader", { name: "Weighted TF-IDF" })).toBeVisible();
  const benchmark = await page.request.get(`${API}/evaluation/results`);
  expect(benchmark.ok()).toBe(true);
  const benchmarkData = await benchmark.json();
  if (benchmarkData.semantic_status === "evaluated") {
    await expect(page.getByRole("rowheader", { name: "Weighted Sentence-BERT" })).toBeVisible();
  }
  await expect(page.getByRole("heading", { name: "Ablation study" })).toBeVisible();
  for (const figure of await page.locator('img[src*="/evaluation/plots/"]').all()) {
    await figure.scrollIntoViewIfNeeded();
    await expect.poll(() => figure.evaluate((element: HTMLImageElement) => element.naturalWidth)).toBeGreaterThan(0);
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await capture(page, "evaluation-dashboard.png", true);
  expect(errors).toEqual([]);
});
