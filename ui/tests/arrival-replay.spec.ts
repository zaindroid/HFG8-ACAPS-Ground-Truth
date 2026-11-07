import { test } from "./workspace-session";
import { expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("arrivals replay incrementally, pause, reveal and return without changing the saved round", async ({
  page,
}) => {
  await page.goto("/desk");
  await page.getByText("Round tools", { exact: true }).click();
  await page.getByRole("button", { name: "Load answers", exact: true }).click();
  await page
    .getByRole("button", { name: "Reveal round 1", exact: true })
    .click();
  await page.getByRole("button", { name: "Simulate arrivals" }).click();
  await expect(
    page.getByRole("region", { name: "Panel locations and expertise" }).first(),
  ).toContainText("Expertise received so far");
  const tray = page.locator(".envelope-tray");
  await expect(tray.locator(".filled")).toHaveCount(1, { timeout: 3000 });
  await page.getByRole("button", { name: "Pause arrivals" }).click();
  const paused = await tray.locator(".filled").count();
  expect(paused).toBeLessThan(8);
  await page.waitForTimeout(850);
  await expect(tray.locator(".filled")).toHaveCount(paused);
  await expect(
    page.getByRole("region", { name: "Decision at a glance" }),
  ).toContainText("Sealed");
  await expect(
    page.getByRole("button", { name: "Reveal round 1", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Resume arrivals" }).click();
  await expect(tray.locator(".filled")).toHaveCount(8, { timeout: 8000 });
  await expect(
    page.getByRole("region", { name: "Decision at a glance" }),
  ).toContainText("Sealed");
  await page
    .getByRole("button", { name: "Reveal round 1", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Decision at a glance" }),
  ).toContainText("69%");
  const analysis = page.getByRole("region", { name: "Analysis walkthrough" });
  await expect(
    analysis.getByRole("heading", { name: "From answers to a decision" }),
  ).toBeVisible();
  await expect(
    analysis.getByRole("region", { name: "Expert forecast versus ACAPS" }),
  ).toBeVisible();
  await analysis.getByRole("button", { name: "Next step" }).click();
  await expect(analysis.locator(".regional-comparison")).toContainText(
    "Ouaddaï",
  );
  await analysis.getByRole("button", { name: "Next step" }).click();
  await expect(
    analysis.getByRole("heading", {
      name: "Repeated concerns still need evidence.",
    }),
  ).toBeVisible();
  await analysis.getByRole("button", { name: "Prepare draft preview" }).click();
  await expect(
    analysis.getByRole("heading", { name: "Keep probability High" }),
  ).toBeVisible();
  await expect(
    analysis.getByRole("button", { name: "Accept draft", exact: true }),
  ).toHaveCount(0);
  await page.screenshot({
    path: test.info().outputPath("analysis-preview.png"),
    fullPage: true,
  });
  await analysis.getByRole("button", { name: "Continue to decision" }).click();
  await expect(
    page.getByRole("region", { name: "Decision at a glance" }),
  ).toContainText("69%");
  await expect(tray.locator(".filled")).toHaveCount(8);
  await expect(page.locator(".response-card.revealed")).toHaveCount(8);
  await expect(
    page.getByRole("button", { name: "Accept draft", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Keep probability High" }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "What supports this assessment" }),
  ).toContainText("69%");
  await expect(page.locator(".draft-wording")).not.toHaveAttribute("open", "");
  await expect(page.locator(".draft-verification")).not.toHaveAttribute(
    "open",
    "",
  );
  await page.getByText("Read the drafted wording", { exact: true }).click();
  await expect(page.locator(".draft-text")).toBeVisible();
  await page.locator(".draft-verification > summary").click();
  await expect(
    page.getByText("Automated review score", { exact: true }),
  ).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("clear-draft.png"),
    fullPage: true,
  });
});
