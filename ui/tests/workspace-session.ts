import { test as base } from "@playwright/test";

// Existing tool-level tests begin inside the demo workspace. Entry tests exercise Login itself.
export const test = base.extend({
  page: async ({ page }, use) => {
    await page.addInitScript(() => {
      sessionStorage.setItem("sealed-signals-samples-v1", "off");
      sessionStorage.setItem(
        "sealed-signals-demo-session",
        JSON.stringify({
          kind: "demo",
          expiresAt: Date.now() + 60 * 60 * 1000,
        }),
      );
    });
    await use(page);
  },
});
