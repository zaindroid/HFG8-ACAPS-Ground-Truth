import { expect } from "@playwright/test";
import { test } from "./workspace-session";
import AxeBuilder from "@axe-core/playwright";
import calibration from "../../fixtures/GET_me_calibration.json" with { type: "json" };
test("jury QR, private calibration, reduced motion and keyboard access", async ({
  page,
}, info) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/stage");
  await expect(page.getByRole("img", { name: /QR code/ })).toBeVisible();
  await expect(
    page.getByText("Computer-only address.", { exact: false }),
  ).toBeVisible();
  await page
    .getByLabel("Expert invitation URL")
    .fill("http://192.168.1.25:5173/e/demo");
  await expect(
    page.getByRole("status").filter({ hasText: "previous link" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Generate QR" }).click();
  await expect(
    page.getByRole("link", {
      name: "http://192.168.1.25:5173/e/demo",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText("Network address supplied.", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Enlarge QR" }).click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `test-results/stage-${info.project.name}.png`,
    fullPage: true,
  });
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.goto("/me/demo/calibration");
  await page
    .getByRole("button", { name: "View my private calibration" })
    .click();
  await expect(
    page.getByText(calibration.mean_brier.toFixed(2), { exact: true }),
  ).toBeVisible();

});
test("expert card accessibility and text scaling", async ({ page }) => {
  await page.goto("/e/demo");
  await expect(page.getByRole("button", { name: "Submit" })).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.addStyleTag({ content: "html { font-size: 200% }" });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page
    .getByRole("button", { name: "Pseudonym Nickname to peers" })
    .click();
  await page.getByRole("button", { name: "Submit" }).click();
  // v3.4: Submit opens a confirmation screen and commits nothing. A link click, a mail scanner
  // or a link preview can reach the draft; only Confirm records an answer.
  await expect(page.getByRole("heading", { name: "Is this right?" })).toBeVisible();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  // The receipt no longer offers a calibration link. v3.4 made calibration a separate,
  // consent-gated programme with its own screen, so an invitation to it does not belong on the
  // back of an answer somebody has just given.
  await expect(
    page.getByRole("link", { name: "Opt in to private calibration" }),
  ).toHaveCount(0);
  await expect(
    page.getByText("in the message you get after the deadline", {
      exact: false,
    }),
  ).toBeVisible();
});
