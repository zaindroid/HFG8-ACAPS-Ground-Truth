import { expect } from "@playwright/test";
import { test } from "./workspace-session";
import AxeBuilder from "@axe-core/playwright";
test("blind round hides all ACAPS anchors, source and confidence are selectable", async ({
  page,
}, info) => {
  await page.goto("/e/demo");
  await expect(page.getByRole("button", { name: "Submit" })).toBeVisible();
  await expect(page.getByText("High", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Still High?", { exact: true })).toHaveCount(0);
  await expect(
    page.getByText("ACAPS rates this High.", { exact: false }),
  ).toHaveCount(0);
  await page
    .getByLabel("How confident are you in this estimate?")
    .selectOption("4");
  await page.getByRole("button", { name: "I read it" }).click();
  await expect(page.getByRole("button", { name: "I read it" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(
    page.getByRole("heading", { name: "Integrity notes" }),
  ).toHaveCount(0);
  await page.screenshot({
    path: `test-results/v2-expert-${info.project.name}.png`,
    fullPage: true,
  });
  await page.goto("/e/round2");
  await expect(page.getByText("ACAPS probability: High")).toBeVisible();
});
test("Radar filters, country map, source badge and matching work", async ({
  page,
}, info) => {
  await page.goto("/radar");
  await expect(
    page.getByText("Source: CSV fallback", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByText("INFORM Severity · Nov2026 · Cached edition", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText("Humanitarian access · Nov2026 · Cached edition", {
      exact: true,
    }),
  ).toBeVisible();
  const header = await page.locator(".site-header").boundingBox();
  const title = await page.locator(".workspace-title").boundingBox();
  expect(header!.y + header!.height).toBeLessThanOrEqual(title!.y);
  await expect(page.getByRole("link", { name: "Review risk" })).toBeVisible();
  await page.getByLabel("Search risks").fill("earthquake");
  await expect(
    page.getByText("No risks match these filters.", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await page
    .getByRole("button", { name: "Chad, 1 risks", exact: true })
    .click();
  await expect(page.getByLabel("Country", { exact: true })).toHaveValue("Chad");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `test-results/radar-${info.project.name}.png`,
    fullPage: true,
  });
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.getByRole("link", { name: "Review risk" }).click();
  await page.getByRole("button", { name: "Preview matched panel" }).click();
  await expect(
    page.getByText("Composition check: passes", { exact: false }),
  ).toBeVisible();
});
test("synthetic application requires consent and distinct committee admins", async ({
  page,
}, info) => {
  await page.goto("/apply");
  await expect(
    page.getByRole("button", { name: "Apply for committee review" }),
  ).toBeDisabled();
  await page
    .getByLabel("This is a synthetic expert application.", { exact: false })
    .check();
  await page
    .getByRole("button", { name: "Apply for committee review" })
    .click();
  await expect(page.getByText("Application X-0009: applied.")).toBeVisible();
  await page
    .getByRole("link", { name: "Review synthetic application" })
    .click();
  await page.getByRole("button", { name: "Record my approval" }).click();
  await expect(
    page.getByRole("heading", { name: "Awaiting second approval" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Record my approval" }),
  ).toBeDisabled();
  await page.getByLabel("Synthetic admin").selectOption("synthetic-admin-b");
  await page.getByRole("button", { name: "Record my approval" }).click();
  await expect(
    page.getByRole("heading", { name: "Expert approved" }),
  ).toBeVisible();
  await expect(
    page.getByText("Synthetic approval replay only. No credential was issued."),
  ).toBeVisible();
  await page.screenshot({
    path: `test-results/committee-${info.project.name}.png`,
    fullPage: true,
  });
});
test("integrity is desk-only and the public ledger includes honesty and resolved history", async ({
  page,
}) => {
  await page.goto("/desk");
  await page.getByText("Round tools", { exact: true }).click();
  await page.getByRole("button", { name: "Load answers" }).click();
  await page.getByRole("button", { name: "Reveal round 1" }).click();
  await expect(
    page.getByRole("heading", { name: "Integrity notes" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Prepare draft" }).click();
  await expect(
    page.getByRole("heading", { name: "To verify before inclusion" }),
  ).toBeVisible();
  await page
    .getByLabel("Decision note")
    .fill(
      "Fixture replay only; uncorroborated claim excluded from the visible draft.",
    );
  await page
    .getByLabel("Decision to inform", { exact: true })
    .fill("Pre-position shelter");
  await page.getByLabel("Decision owner", { exact: true }).fill("NGO lead");
  await page
    .getByLabel("Decision needed by", { exact: true })
    .fill("2026-11-20");
  await page.getByRole("button", { name: "Accept draft" }).click();
  await page.getByRole("link", { name: "View public ledger" }).click();
  await expect(page.locator(".honesty-box")).toHaveCount(2);
  await expect(
    page.getByRole("heading", { name: "Integrity notes" }),
  ).toHaveCount(0);
  await expect(page.getByText("quiet-heron")).toHaveCount(0);
  await page.locator(".ledger-record > summary").last().click();
  await expect(
    page.getByRole("heading", { name: "Resolved history / R0987" }),
  ).toBeVisible();
  await expect(page.getByText("Includes misses")).toHaveCount(2);
  await expect(
    page.getByRole("heading", { name: "Panel view rejected by the analyst" }),
  ).toBeVisible();
  await page.locator(".ledger-record > summary").first().click();
  await expect(
    page.getByText("Pre-position shelter", { exact: true }),
  ).toBeVisible();
});
