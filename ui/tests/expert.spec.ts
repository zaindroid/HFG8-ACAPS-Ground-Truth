import { expect } from "@playwright/test";
import { reachSubmit } from "./expert-flow";
import { test } from "./workspace-session";
import result from "../../fixtures/GET_pulses_result.json" with { type: "json" };
import { submitCard } from "./card-flow";
// Read from the fixture, never retyped: the last set of hard-coded percentages in
// these specs still said 69 % long after the engine had stopped producing it.
const meanPercent = `${Math.round(result.mean * 100)}%`;
const meanTwoDp = result.mean.toFixed(2);
test("expert card fits, supports keyboard sliders and seals selected mask", async ({
  page,
}, info) => {
  await page.goto("/e/demo");
  await expect(
    page.getByRole("heading", { name: /Escalating cross-border/ }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  const probability = page.getByRole("slider").first();
  await probability.focus();
  await probability.press("ArrowRight");
  await expect(probability).toHaveAttribute("aria-valuenow", "51");
  await page
    .getByRole("button", { name: "Pseudonym Nickname to peers" })
    .click();
  await page
    .getByLabel("What are we missing?")
    .fill("A synthetic local signal.");
  await page.screenshot({
    path: `test-results/expert-${info.project.name}.png`,
    fullPage: true,
  });
  await reachSubmit(page);
  await submitCard(page);
  await expect(
    page.getByRole("heading", {
      name: "Submitted. You’ll get the group outcome.",
    }),
  ).toBeVisible();
  await expect(
    page.getByText("Fixture receipt · not a live seal"),
  ).toBeVisible();
  await expect(page.getByText("pseudonym", { exact: true })).toBeVisible();
});
test("round two and empty invitation render meaningful states", async ({
  page,
}) => {
  await page.goto("/e/round2");
  await expect(
    page.getByRole("heading", { name: "How the panel answered" }),
  ).toBeVisible();
  await expect(
    page.getByText(`8 synthetic answers · Equal-weight mean ${meanPercent}`),
  ).toBeVisible();
  await page.getByLabel("I changed my mind after seeing the panel").check();
  await page.goto("/e/empty");
  await expect(page.getByRole("alert")).toContainText("no active pulse");
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
});
