import { test, expect } from "@playwright/test";
import risksFixture from "../../fixtures/GET_risks.json" with { type: "json" };
import result from "../../fixtures/GET_pulses_result.json" with { type: "json" };
// Read from the fixture, never retyped: the last set of hard-coded percentages in
// these specs still said 69 % long after the engine had stopped producing it.
const meanPercent = `${Math.round(result.mean * 100)}%`;
const meanTwoDp = result.mean.toFixed(2);

test("populated samples connect every main page and align content with the header", async ({
  page,
}, info) => {
  if (info.project.name === "desktop")
    await page.setViewportSize({ width: 1531, height: 668 });
  await page.goto("/");
  await page
    .getByRole("button", { name: "Login", exact: true })
    .first()
    .click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "From a signal to an accountable decision",
  );
  await page
    .getByText("Workspace data and supporting tools", { exact: true })
    .click();
  await expect(
    page.getByText("6 risk records", { exact: false }),
  ).toBeVisible();
  const brand = await page.locator(".portal-topline .brand").boundingBox(),
    title = await page.getByRole("heading", { level: 1 }).boundingBox();
  expect(Math.abs(brand!.x - title!.x)).toBeLessThan(1);
  await page.screenshot({
    path: test.info().outputPath("sample-overview.png"),
    fullPage: true,
  });
  await page.goto("/radar");
  await expect(page.locator("tbody tr")).toHaveCount(6);
  await page.getByLabel("Country", { exact: true }).selectOption("Haiti");
  await page.getByRole("link", { name: "View ledger history" }).click();
  await page.locator(".ledger-record > summary").first().click();
  await expect(
    page.getByRole("heading", { name: "Resolved history / R0105" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "No matching risks" }),
  ).toHaveCount(0);
  await page.goto("/ledger");
  await expect(page.locator(".honesty-box")).toHaveCount(6);
  await page.locator(".ledger-record > summary").first().click();
  await expect(
    page.locator(".ledger-entry .ledger-stats strong").first(),
  ).toHaveText(meanPercent);
  await expect(page.getByText("river-ibis", { exact: true })).toHaveCount(0);
  await page.getByLabel("Find a risk").fill("Haiti");
  await expect(page.locator(".honesty-box")).toHaveCount(1);
  await page.goto("/calibration");
  await page
    .getByRole("button", { name: "View my private calibration" })
    .click();
  await expect(page.getByText("0.18", { exact: true })).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(5);
  await page.screenshot({
    path: test.info().outputPath("sample-calibration.png"),
    fullPage: true,
  });
  await page.goto("/committee");
  const applications = page.locator(".workspace-panel").filter({
    has: page.getByRole("heading", {
      name: "Applications",
      exact: true,
    }),
  });
  await expect(applications.locator("tbody tr")).toHaveCount(3);
  await page.getByRole("button", { name: "Review X-SAMPLE-002" }).click();
  await page.getByRole("button", { name: "Record my approval" }).click();
  await expect(
    page.getByRole("heading", { name: "Expert approved", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    applications.locator("tr").filter({ hasText: "X-SAMPLE-002" }),
  ).toContainText("approved · 2/2");
  await page.goto("/apply");
  await page.getByRole("button", { name: "Use sample application" }).click();
  await page
    .getByRole("button", { name: "Apply for committee review" })
    .click();
  await page
    .getByRole("link", { name: "Review synthetic application" })
    .click();
  await expect(page.getByLabel("Application ID")).toHaveValue("X-SAMPLE-004");
  await page.goto("/stage");
  await expect(
    page.getByRole("heading", { name: "Invitations" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Open optional round-two card" })
    .click();
  await expect(
    page.getByText(`8 synthetic answers · Equal-weight mean ${meanPercent}`, {
      exact: true,
    }),
  ).toBeVisible();
});

test("sample reset opens a fresh analyst round without losing history", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Login", exact: true })
    .first()
    .click();
  await page
    .getByText("Workspace data and supporting tools", { exact: true })
    .click();
  await page.getByRole("button", { name: "Start a fresh round" }).click();
  await page.goto("/desk");
  await expect(
    page.getByRole("button", { name: "Reveal round 1" }),
  ).toBeDisabled();
  await page.getByText("Round tools", { exact: true }).click();
  await page.getByRole("button", { name: "Load answers" }).click();
  await page.getByRole("button", { name: "Reveal round 1" }).click();
  await page.getByRole("button", { name: "Prepare draft" }).click();
  await page.getByText("Read the drafted wording", { exact: true }).click();
  // The drafted wording restates the panel claim in plain language for a general audience; the
  // method is named beside it, in the decision summary. So this asserts the number the draft
  // puts in front of the analyst, derived from the round rather than typed in.
  await expect(page.locator(".draft-text")).toContainText(
    `The average expert estimate is ${meanPercent}`,
  );
  // And every claim is its own claim: the sample used to overwrite all of them with one
  // hard-coded sentence, which rendered as eight identical paragraphs.
  const paragraphs = await page.locator(".draft-text p").allInnerTexts();
  expect(new Set(paragraphs).size).toBe(paragraphs.length);
  await page.getByLabel("Decision note").fill("Synthetic review completed.");
  await page
    .getByLabel("Decision to inform", { exact: true })
    .fill("Pre-position shelter");
  await page
    .getByLabel("Decision owner", { exact: true })
    .fill("Synthetic preparedness lead");
  await page
    .getByLabel("Decision needed by", { exact: true })
    .fill("2026-11-20");
  await page.getByRole("button", { name: "Accept draft", exact: true }).click();
  await page.getByRole("link", { name: "View public ledger" }).click();
  await expect(page.locator(".honesty-box")).toHaveCount(6);
  await page.goto("/workspace");
  await page
    .getByText("Workspace data and supporting tools", { exact: true })
    .click();
  await page.getByRole("button", { name: "Clear records" }).click();
  await page
    .getByText("Workspace data and supporting tools", { exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Load records", exact: true }),
  ).toBeVisible();
  await page.goto("/radar");
  // Back on the plain fixture: one row per risk in it, whatever the regeneration kept.
  await expect(page.locator("tbody tr")).toHaveCount(risksFixture.risks.length);
});
