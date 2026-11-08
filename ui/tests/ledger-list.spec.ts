import { test, expect } from "@playwright/test";
test("ledger records are compact, comparable and expand on demand", async ({
  page,
}, info) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Login", exact: true })
    .first()
    .click();
  await page.goto("/ledger");
  const records = page.locator(".ledger-record");
  await expect(records).toHaveCount(6);
  await expect(page.locator(".ledger-record[open]")).toHaveCount(0);
  const heights = await records.evaluateAll((items) =>
    items.map((item) => item.getBoundingClientRect().height),
  );
  expect(Math.max(...heights)).toBeLessThan(100);
  await expect(page.getByText("UI-only sample", { exact: false })).toHaveCount(
    0,
  );
  await records.nth(3).locator("summary").click();
  await expect(
    records.nth(3).getByRole("region", { name: "Public honesty box" }),
  ).toBeVisible();
  await records.nth(0).locator("summary").click();
  await expect(page.locator(".ledger-record[open]")).toHaveCount(1);
  await records
    .nth(0)
    .getByRole("button", { name: "Verify fixture hash" })
    .click();
  await expect(records.nth(0).locator("summary")).toContainText(
    "Receipt matched",
  );
  await records.nth(0).locator("summary").click();
  await page.screenshot({
    path: test.info().outputPath("compact-ledger.png"),
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
