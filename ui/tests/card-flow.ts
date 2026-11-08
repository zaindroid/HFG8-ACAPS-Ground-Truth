import { expect, type Page } from "@playwright/test";

/**
 * Walk the expert card to its end and commit.
 *
 * The card runs up to three steps: the scored question, then up to two follow-ups chosen on the
 * device from the expert's own answers. Submit appears only on the last one, and how many steps
 * a given answer produces depends on the probe rules -- an abstention ends at one, a wide gap
 * between an expert's own estimate and their guess at the panel opens a second. A test that
 * clicks "Submit" directly is asserting a step count it has no reason to know.
 *
 * Then Submit opens the confirmation screen and commits nothing; only Confirm writes. That split
 * is what keeps a link click, a mail scanner or a link preview from answering for somebody.
 */
export async function submitCard(page: Page, { confirm = true } = {}) {
  const submit = page.getByRole("button", { name: "Submit", exact: true });
  const carryOn = page.getByRole("button", { name: "Continue", exact: true });
  for (let step = 0; step < 3; step++) {
    if (await submit.count()) break;
    await expect(carryOn).toBeVisible();
    await carryOn.click();
  }
  await expect(submit).toBeVisible();
  await submit.click();
  await expect(
    page.getByRole("heading", { name: "Is this right?" }),
  ).toBeVisible();
  if (confirm) {
    await page.getByRole("button", { name: "Confirm", exact: true }).click();
  }
}
