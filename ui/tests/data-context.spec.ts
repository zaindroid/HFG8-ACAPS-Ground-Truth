import { test } from "./workspace-session";
import { expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("edition history shows retained datasets in month order without loading a new page", async ({
  page,
}, info) => {
  await page.goto("/radar");
  await page.getByText("Edition history", { exact: true }).click();
  const history = page.locator(".edition-history");
  await expect(history.locator(".edition-history-row")).toHaveCount(2);
  await expect(
    history.locator(".edition-history-row").first().locator("a"),
  ).toHaveText(["Nov2026", "Oct2026", "Apr2026", "Mar2026"]);
  await expect(
    history.locator(".edition-history-row").last().locator("a"),
  ).toHaveText(["Nov2026"]);
  await expect(
    history.getByRole("link", {
      name: "INFORM Severity Apr2026 source edition",
    }),
  ).toHaveAttribute(
    "href",
    "https://api.acaps.org/api/v1/inform-severity-index/Apr2026/",
  );
  await page.screenshot({
    path: info.outputPath("edition-history.png"),
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});

test("risk link review requires geography confirmation and stays inside the alert", async ({
  page,
}, info) => {
  await page.goto("/alerts");
  await page.getByText("Review risk link", { exact: true }).click();
  await expect(page.getByLabel("Active risk in TCD")).toHaveValue("R1043");
  await expect(
    page.getByRole("button", { name: "Confirm risk link" }),
  ).toBeDisabled();
  await page
    .getByLabel("The geography and risk triggers match this crisis.")
    .check();
  await page.getByRole("button", { name: "Confirm risk link" }).click();
  await expect(page.locator(".risk-link-confirmed")).toHaveText(
    "R1043 linked to TCD005.",
  );
  await page
    .getByRole("button", { name: "Refresh risks", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Confirm risk link" }),
  ).toBeDisabled();
  await page.screenshot({
    path: info.outputPath("risk-link.png"),
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});
