import { expect, type Page } from "@playwright/test";
import { test } from "./workspace-session";
import AxeBuilder from "@axe-core/playwright";

async function draftReady(page: Page) {
  await page.goto("/desk");
  await expect(
    page.getByRole("button", { name: "Reveal round 1" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Load answers" }).click();
  await page.getByRole("button", { name: "Reveal round 1" }).click();
  await expect(
    page.getByText("Equal-weight mean", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Prepare draft" }).click();
}
test("approval gates public ledger, verification is labelled and both screens fit", async ({
  page,
}, info) => {
  await page.goto("/ledger");
  await expect(
    page.getByRole("heading", { name: "No approved group views yet" }),
  ).toBeVisible();
  await draftReady(page);
  await page
    .getByText("Question, panel and supporting details", { exact: true })
    .click();
  await expect(
    page.getByText("Other regions withheld", { exact: false }),
  ).toBeVisible();
  await expect(page.getByText("N'Djamena", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Accept draft" }).click();
  await expect(page.getByRole("alert")).toHaveText(
    "Add a decision note before continuing.",
  );
  await page
    .getByLabel("Decision note")
    .fill("Panel evidence supports retaining the High rating.");
  await page
    .getByLabel("Decision to inform", { exact: true })
    .fill("Pre-position shelter");
  await page
    .getByLabel("Decision owner", { exact: true })
    .fill("NGO preparedness lead");
  await page
    .getByLabel("Decision needed by", { exact: true })
    .fill("2026-11-20");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `test-results/desk-${info.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole("button", { name: "Accept draft" }).click();
  await page.getByRole("link", { name: "View public ledger" }).click();
  await page.locator(".ledger-record > summary").first().click();
  await expect(page.getByText("8 synthetic contributions")).toBeVisible();
  await expect(page.getByText("quiet-heron")).toHaveCount(0);
  await page.getByRole("button", { name: "Verify fixture hash" }).click();
  await expect(
    page.getByRole("button", { name: "Fixture verified" }),
  ).toBeVisible();
  await expect(
    page.getByRole("status").filter({ hasText: "No blockchain anchor" }),
  ).toContainText("No blockchain anchor");
  const trail = page
    .getByRole("region", { name: "From contribution to verification" })
    .first();
  await trail
    .getByRole("button", { name: "Verified Receipt matched", exact: true })
    .click();
  await expect(
    trail.getByText("No external proof is attached.", { exact: false }),
  ).toBeVisible();
  await expect(
    trail.getByRole("link", { name: "Open timestamp proof" }),
  ).toHaveCount(0);
  await expect(
    trail.getByRole("button", {
      name: "Verified Receipt matched",
      exact: true,
    }),
  ).toHaveAttribute("aria-pressed", "true");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await trail.screenshot({
    path: `test-results/verification-trail-${info.project.name}.png`,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `test-results/ledger-${info.project.name}.png`,
    fullPage: true,
  });
  await page.getByLabel("Find a risk").fill("does-not-exist");
  await expect(
    page.getByRole("heading", { name: "No matching risks" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear search" }).click();
  await page.locator(".ledger-record > summary").first().click();
  await expect(page.getByText("8 synthetic contributions")).toBeVisible();
});
test("rejection does not publish; editing preserves selected probability after navigation", async ({
  page,
}) => {
  await draftReady(page);
  await page.getByLabel("Decision note").fill("More corroboration is needed.");
  await page
    .getByLabel("Decision to inform", { exact: true })
    .fill("Pre-position shelter");
  await page
    .getByLabel("Decision owner", { exact: true })
    .fill("NGO preparedness lead");
  await page
    .getByLabel("Decision needed by", { exact: true })
    .fill("2026-11-20");
  await page.getByRole("button", { name: "Reject draft" }).click();
  await expect(
    page.getByRole("heading", { name: "Decision log" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Ledger", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "No approved group views yet" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Analyst desk", exact: true }).click();
  await page.getByRole("button", { name: "Reset round" }).click();
  await page.getByRole("button", { name: "Load answers" }).click();
  await page.getByRole("button", { name: "Reveal round 1" }).click();
  await page.getByRole("button", { name: "Prepare draft" }).click();
  await page.getByRole("button", { name: "Edit probability" }).click();
  await page.getByLabel("Edited probability").selectOption("Very High");
  await page
    .getByLabel("Decision note")
    .fill("Escalating indicators warrant a higher probability.");
  await page
    .getByLabel("Decision to inform", { exact: true })
    .fill("Pre-position shelter");
  await page
    .getByLabel("Decision owner", { exact: true })
    .fill("NGO preparedness lead");
  await page
    .getByLabel("Decision needed by", { exact: true })
    .fill("2026-11-20");
  await page.getByRole("button", { name: "Save edited decision" }).click();
  await page.getByRole("link", { name: "View public ledger" }).click();
  await page.locator(".ledger-record > summary").first().click();
  await expect(page.getByText("Very High", { exact: true })).toBeVisible();
  await page.reload();
  await page.locator(".ledger-record > summary").first().click();
  await expect(page.getByText("Very High", { exact: true })).toBeVisible();
});
