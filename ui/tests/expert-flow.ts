import { expect, type Page } from "@playwright/test";

/**
 * Walk the expert card to its final step.
 *
 * The card runs up to three steps and only offers Submit on the last one, so a test that
 * wants to seal has to get there first. Waits for the card to render before looking:
 * counting buttons on a page that is still loading finds none and returns too early.
 * Abstentions end at step one and already show Submit, so the loop exits immediately.
 */
export async function reachSubmit(page: Page, max = 3) {
  await expect(page.locator(".seal-button").first()).toBeVisible();
  for (let i = 0; i < max; i++) {
    const next = page.getByRole("button", { name: /^Continue/ });
    if ((await next.count()) === 0) return;
    await next.first().click();
  }
}
