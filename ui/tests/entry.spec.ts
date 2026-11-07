import { test, expect } from "@playwright/test";
import { reachSubmit } from "./expert-flow";
import AxeBuilder from "@axe-core/playwright";
import { submitCard } from "./card-flow";

test("public entry exposes research and Login opens the workspace without credentials", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "One question.Independent judgement.",
  );
  // ACAPS is credited as the data source, never imitated: one outbound link, in the footer, and
  // a banner saying what this is. No reproduction of their navigation.
  await expect(
    page.getByRole("link", { name: "Official ACAPS website" }),
  ).toHaveAttribute("href", "https://www.acaps.org/en/");
  await expect(
    page.getByRole("complementary", { name: "Prototype notice" }),
  ).toContainText("Not an ACAPS service");
  await expect(
    page.getByRole("link", { name: "Countries", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText("Equal-weight mean", { exact: true }),
  ).toHaveCount(0);
  await expect(page.locator('input[type="password"]')).toHaveCount(0);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("public-home.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Login", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(/\/workspace$/);
  const navigation = page.getByRole("navigation", { name: "Main navigation" });
  for (const name of [
    "Countries",
    "Analysis",
    "Topics & data",
    "ACAPS website",
  ])
    await expect(page.getByRole("link", { name, exact: true })).toHaveCount(0);
  await expect(page.getByRole("search")).toHaveCount(0);
  for (const name of ["Alerts", "Expert card", "Analyst desk", "Ledger"])
    await expect(
      navigation.getByRole("link", { name, exact: true }),
    ).toBeVisible();
  await expect(page.locator(".journey-overview > a")).toHaveCount(4);
  await page.goto("/topics");
  await expect(page).toHaveURL(/\/workspace$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "From a signal to an accountable decision",
  );
  await navigation.getByText("More", { exact: true }).click();
  await navigation.getByRole("link", { name: "Stage", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Stage");
  await navigation.getByText("More", { exact: true }).click();
  await navigation
    .getByRole("link", { name: "Calibration", exact: true })
    .click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Your calibration",
  );
  await navigation
    .getByRole("link", { name: "Expert card", exact: true })
    .click();
  await reachSubmit(page);
  await expect(
    page.getByRole("button", { name: "Submit", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Sealed Signals", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "From a signal to an accountable decision",
  );
  await page.screenshot({
    path: test.info().outputPath("workspace-navigation.png"),
    fullPage: true,
  });
  await page
    .getByText("Workspace data and supporting tools", { exact: true })
    .click();
  await page
    .getByRole("link", { name: "Risk Radar & metrics", exact: false })
    .click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Risk Radar",
  );
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto("/desk");
  await expect(page).toHaveURL(/\/\?next=%2Fdesk$/);
  await expect(page.getByRole("button", { name: "Ask panel" })).toHaveCount(0);
  await page
    .getByRole("button", { name: "Login", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(/\/desk$/);
});

test("expired sessions return to the public page and unsafe destinations are ignored", async ({
  page,
}) => {
  await page.addInitScript(
    () =>
      !sessionStorage.getItem("sealed-signals-demo-session") &&
      sessionStorage.setItem(
        "sealed-signals-demo-session",
        JSON.stringify({ kind: "demo", expiresAt: 0 }),
      ),
  );
  await page.goto("/ledger");
  await expect(page).toHaveURL(/\/\?next=%2Fledger$/);
  await page.goto("/?next=https%3A%2F%2Fexample.com");
  await page
    .getByRole("button", { name: "Login", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(/\/workspace$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "From a signal to an accountable decision",
  );
});

test("expert invitations stay no-login, accept abstentions and explain limits", async ({
  page,
}) => {
  await page.goto("/e/demo");
  await expect(
    page.getByText("Rating hidden until after submission", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".timer")).toHaveCount(0);
  await expect(
    page.getByText("may identify its author to colleagues", { exact: false }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Outside my expertise", exact: true })
    .click();
  await expect(page.getByRole("slider")).toHaveCount(0);
  await submitCard(page);
  await expect(
    page.getByRole("heading", {
      name: "Submitted. You’ll get the group outcome.",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Opt in to private calibration" }),
  ).toHaveCount(0);
  await expect(
    page.getByText("Anonymous answers have no identity link", { exact: false }),
  ).toBeVisible();
});
