import { test } from "./workspace-session";
import { expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("April alert leads to a human panel request and a readable desk", async ({
  page,
}, info) => {
  await page.goto("/alerts");
  await expect(
    page.getByRole("heading", { name: "Alerts", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Replay April" }).click();
  await expect(page.locator(".shift-row")).toHaveCount(3);
  await expect(
    page.getByRole("img", { name: /Severity increased from 6.1/ }),
  ).toBeVisible();
  await expect(
    page.getByText("index delta >= 0.5", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: info.outputPath("alerts.png"),
    fullPage: true,
  });
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Ask experts", exact: true }).click();
  await expect(page).toHaveURL(/\/desk\?risk_id=R1043&pulse_id=P-0001/);
  await expect(
    page.getByRole("region", { name: "Decision at a glance" }),
  ).toContainText("Sealed");
  await page.getByRole("button", { name: "Load 8 demo answers" }).click();
  await page.getByRole("button", { name: "Advance to deadline" }).first().click();
  await page.getByRole("button", { name: "Reveal answers" }).click();
  await expect(
    page.getByRole("region", { name: "Decision at a glance" }),
  ).toContainText("69%");
  await expect(
    page.getByRole("region", { name: "Decision at a glance" }),
  ).toContainText("30–90%");
  await page.getByRole("button", { name: "Continue to decision" }).click();
  await expect(page.getByRole("button", { name: "Accept draft" })).toBeVisible();
  await page.screenshot({ path: info.outputPath("desk.png"), fullPage: true });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("current editions can be empty and dismissal requires a note", async ({
  page,
}) => {
  await page.goto("/alerts");
  await page.getByRole("button", { name: "Run current editions" }).click();
  await expect(
    page.getByRole("heading", { name: "No shifts crossed the rules" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Replay April" }).click();
  await page.getByRole("button", { name: "Dismiss", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Save dismissal" }),
  ).toBeDisabled();
  await page
    .getByLabel("Why dismiss this change?")
    .fill("Covered by the scheduled assessment.");
  await page.getByRole("button", { name: "Save dismissal" }).click();
  await expect(
    page.getByText("This change was dismissed", { exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByText("This change was dismissed", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByText("More", { exact: true })
    .click();
  await expect(
    page.getByRole("link", { name: "Calibration", exact: true }),
  ).toBeVisible();
});
