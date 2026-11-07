import { expect, type Page } from "@playwright/test";
import { test } from "./workspace-session";
import AxeBuilder from "@axe-core/playwright";
import risks from "../../fixtures/GET_risks.json" with { type: "json" };
// Every P-0001 route in this file is the demo round, so the pulse body must be that round and
// not whichever pulse POST /pulses created when the fixtures were last regenerated.
import pulse from "../../fixtures/GET_pulses_demo.json" with { type: "json" };
import alertPulseFixture from "../../fixtures/POST_alerts_pulse_response.json" with { type: "json" };
import result from "../../fixtures/GET_pulses_result.json" with { type: "json" };
import draft from "../../fixtures/POST_pulses_draft_response.json" with { type: "json" };
import scoring from "../../fixtures/GET_committee_scoring.json" with { type: "json" };
import ledger from "../../fixtures/GET_ledger.json" with { type: "json" };
import calibration from "../../fixtures/GET_me_calibration.json" with { type: "json" };
import card from "../../fixtures/GET_e_token.json" with { type: "json" };
import answerDraft from "../../fixtures/POST_e_token_answer_response.json" with { type: "json" };
import seal from "../../fixtures/POST_e_token_confirm_response.json" with { type: "json" };
import integrity from "../../fixtures/GET_integrity_pulse.json" with { type: "json" };

/** The group mean as the UI prints it. Derived, because a literal here went stale the moment the
 *  fixtures were regenerated from the real engine. */
const meanPercent = `${Math.round(result.mean * 100)}%`;
import radar from "../../fixtures/GET_radar_status.json" with { type: "json" };
import matched from "../../fixtures/GET_panels_match.json" with { type: "json" };
import alerts from "../../fixtures/GET_alerts.json" with { type: "json" };
import crisis from "../../fixtures/GET_crises_TCD005.json" with { type: "json" };
import alertPulse from "../../fixtures/POST_alerts_pulse_response.json" with { type: "json" };
import { submitCard } from "./card-flow";

test("edition history reports an unavailable API and retries without cached fallback", async ({
  page,
}) => {
  await contractApi(page);
  let available = false;
  await page.route("**/radar/editions", (route) =>
    route.fulfill({
      status: available ? 200 : 501,
      json: available
        ? { "inform-severity-index": ["Mar2026", "Nov2026", "Apr2026"] }
        : {},
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.goto("/radar");
  await page.getByText("Edition history", { exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("not available");
  await expect(page.locator(".edition-months a")).toHaveCount(0);
  available = true;
  await page.getByRole("button", { name: "Refresh editions" }).click();
  await expect(page.locator(".edition-months a")).toHaveText([
    "Nov2026",
    "Apr2026",
    "Mar2026",
  ]);
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("risk links require a stored crisis mapping before alert routing changes", async ({
  page,
}) => {
  await contractApi(page);
  let state: "unsupported" | "unconfirmed" | "confirmed" = "unsupported";
  const writes: unknown[] = [];
  await page.route("http://127.0.0.1:18000/alerts", (route) =>
    route.fulfill({
      json: {
        events: alerts.events.map((e) => ({
          ...e,
          risk_id: state === "confirmed" ? "R1043" : null,
        })),
      },
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.route("http://127.0.0.1:18000/crises/TCD005", (route) =>
    route.fulfill({
      json: { ...crisis, linked_risks: state === "confirmed" ? ["R1043"] : [] },
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.route("http://127.0.0.1:18000/risks/R1043/link", (route) => {
    if (route.request().method() === "OPTIONS")
      return route.fulfill({
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "content-type",
          "Access-Control-Allow-Methods": "POST",
        },
      });
    writes.push(route.request().postDataJSON());
    return route.fulfill({
      status: state === "unsupported" ? 501 : 200,
      json: { risk_id: "R1043", crisis_id: "TCD005" },
      headers: { "Access-Control-Allow-Origin": "*" },
    });
  });
  await page.goto("/alerts");
  await expect(
    page.getByRole("button", { name: "Ask experts", exact: true }),
  ).toBeDisabled();
  await page.getByText("Review risk link", { exact: true }).click();
  await page
    .getByLabel("The geography and risk triggers match this crisis.")
    .check();
  await page.getByRole("button", { name: "Confirm risk link" }).click();
  await expect(page.getByRole("alert")).toContainText("not available");
  await expect(page.locator(".risk-link-confirmed")).toHaveCount(0);
  state = "unconfirmed";
  await page.getByRole("button", { name: "Confirm risk link" }).click();
  await expect(page.getByRole("alert")).toContainText("has not confirmed");
  await expect(
    page.getByRole("button", { name: "Ask experts", exact: true }),
  ).toBeDisabled();
  state = "confirmed";
  await page.getByRole("button", { name: "Confirm risk link" }).click();
  await expect(page.locator(".risk-link-confirmed")).toHaveText(
    "R1043 linked to TCD005.",
  );
  await expect(
    page.getByRole("button", { name: "Ask experts", exact: true }),
  ).toBeEnabled();
  expect(writes).toEqual([
    { crisis_id: "TCD005" },
    { crisis_id: "TCD005" },
    { crisis_id: "TCD005" },
  ]);
});

test("alert API failures retain the proposed alert and confirmed pulse opens the desk", async ({
  page,
}) => {
  const writes: { path: string; body: unknown }[] = [];
  await contractApi(page);
  await page.route("http://127.0.0.1:18000/alerts**", async (route) => {
    const request = route.request(),
      path = new URL(request.url()).pathname;
    if (request.method() === "OPTIONS")
      return route.fulfill({
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "content-type",
          "Access-Control-Allow-Methods": "GET, POST",
        },
      });
    if (request.method() === "POST")
      writes.push({ path, body: request.postDataJSON() });
    return route.fulfill({
      status: path.endsWith("/dismiss") ? 501 : 200,
      json: path.endsWith("/pulse") ? alertPulse : alerts,
      headers: { "Access-Control-Allow-Origin": "*" },
    });
  });
  await page.route("http://127.0.0.1:18000/crises/*", (route) =>
    route.fulfill({
      json: crisis,
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.goto("/alerts");
  await page.getByRole("button", { name: "Dismiss", exact: true }).click();
  await page
    .getByLabel("Why dismiss this change?")
    .fill("Covered in the current assessment.");
  await page.getByRole("button", { name: "Save dismissal" }).click();
  await expect(page.getByRole("alert")).toContainText("not available");
  await expect(
    page.getByRole("button", { name: "Ask experts", exact: true }),
  ).toBeVisible();
  expect(writes[0]).toEqual({
    path: "/alerts/S-0001/dismiss",
    body: { note: "Covered in the current assessment." },
  });
  await page.getByRole("button", { name: "Ask experts", exact: true }).click();
  await page.getByRole("link", { name: "Open analyst desk" }).click();
  // Approving an alert opens a NEW pulse, so the desk shows that one, not the seeded round.
  await expect(page.getByLabel("Pulse ID", { exact: true })).toHaveValue(
    alertPulseFixture.pulse.id,
  );
  await page.getByRole("button", { name: "Open pulse", exact: true }).click();
  await expect(
    revealButton(page),
  ).toBeEnabled();
  expect(writes[1]).toEqual({ path: "/alerts/S-0001/pulse", body: {} });
});

/** The reveal button, whichever label the deadline put on it.
 *
 * The round opens at pulse.expires_at and the engine refuses a plain reveal before then, so the
 * desk offers "Reveal (deadline passed)" or "Reveal now (before the deadline)" and sends the
 * recorded override only in the second case. A test matching one fixed label would pass or fail
 * on what time the fixture was generated. */
function revealButton(page: Page) {
  return page.getByRole("button", { name: /^Reveal (\(deadline passed\)|now \(before the deadline\))$/ });
}

async function contractApi(page: Page) {
  const writes: { path: string; body: any }[] = [];
  await page.route("http://127.0.0.1:18000/**", async (route) => {
    const request = route.request(),
      path = new URL(request.url()).pathname;
    const body = request.method() === "POST" ? request.postDataJSON() : null;
    if (body) writes.push({ path, body });
    const respond = (json: unknown, status = 200) =>
      route.fulfill({
        status,
        json,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    if (request.method() === "OPTIONS")
      return route.fulfill({
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "content-type",
          "Access-Control-Allow-Methods": "GET, POST",
        },
      });
    if (path === "/events")
      return route.fulfill({
        contentType: "text/event-stream",
        body: 'event: answer_sealed\ndata: {"pulse_id":"P-0001","n_answers":8}\n\n',
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    if (path === "/radar/status") return respond(radar);
    if (path.startsWith("/integrity/")) return respond(integrity);
    if (path === "/panels/match") return respond(matched);
    if (path === "/experts/apply")
      return respond({ expert_id: "X-0009", status: "applied" });
    if (path === "/experts/X-0009/approve")
      return respond({
        expert_id: "X-0009",
        status: "applied",
        approved_by: ["admin-a"],
      });
    if (path === "/risks") return respond(risks);
    if (path.endsWith("/contract"))
      return respond({
        ...body,
        risk_id: "R1043",
        frozen_at: "2026-11-06T09:00:00Z",
      });
    if (path.endsWith("/outcome-report"))
      return respond({
        pulse_id: "P-0001",
        group_mean: result.mean,
        outcome: "materialised",
        analyst_decision_summary: "Retained High.",
      });
    if (path === "/committee/scoring") return respond(scoring);
    if (path === "/pulses" && body) return respond(pulse, 201);
    if (path === "/pulses/P-0001") return respond({ ...pulse, n_answers: 8 });
    if (path.endsWith("/reveal") || path.endsWith("/result"))
      return respond(result);
    if (path.endsWith("/draft"))
      return respond({
        ...draft,
        claims: [
          {
            claim_id: "c1",
            text: `The equal-weight panel mean is ${meanPercent}.`,
            evidence_kind: "panel",
            evidence_ref: "P-0001:mean",
            numbers: [result.mean, result.n],
          },
        ],
        skeptic: [
          {
            claim_id: "c1",
            verdict: "supported",
            checks: ["Eight contributions confirmed."],
          },
        ],
        judge: {
          coverage: 1,
          numbers_match: 1,
          overall: 1,
          flagged_claim_ids: [],
        },
      });
    if (path.endsWith("/decision"))
      return respond({
        ...draft,
        status:
          body.action === "edit"
            ? "edited"
            : body.action === "accept"
              ? "accepted"
              : "rejected",
        proposed_probability: body.edited_probability || "High",
        note: body.note,
        decided_at: "2026-11-06T12:00:00Z",
      });
    if (path === "/ledger")
      return respond({
        ...ledger,
        entries: [
          { ...ledger.entries[0], n: 8 },
          {
            ...ledger.entries[1],
            n: 4,
            honesty: { ...ledger.entries[1].honesty, n: 4 },
          },
        ],
      });
    if (path === "/ledger/verify")
      return respond({
        valid: false,
        sealed_at: ledger.entries[0].sealed_at,
        anchor: null,
      });
    if (path.endsWith("/resolve"))
      return respond({ scores_written: 8, weights_updated: 8 });
    if (path.endsWith("/calibration")) return respond(calibration);
    // Two steps since v3.4: the draft commits nothing, the confirmation does.
    if (path.startsWith("/e/") && path.endsWith("/answer"))
      return respond(answerDraft);
    if (path.startsWith("/e/") && path.endsWith("/confirm"))
      return respond(seal, 201);
    if (path.startsWith("/e/")) return respond(card);
    if (path === "/pulses/doorbell/run")
      return respond({ shifts: [{}], pulses_fired: ["P-0001"] });
    return respond({ detail: "Not available" }, 404);
  });
  return writes;
}
test("API pulse, SSE, reveal, checked draft, decision and resolution", async ({
  page,
}, info) => {
  const writes = await contractApi(page);
  await page.goto("/desk");
  await page.getByRole("button", { name: "Ask panel" }).click();
  await expect(
    page.getByText("P-0001 · Round 1 · 8 sealed answers", { exact: true }),
  ).toBeVisible();
  await revealButton(page).click();
  // The engine fixes the reveal at pulse.expires_at and refuses a plain reveal before it. The
  // seeded round's deadline is a day out, so the desk has to send the recorded override or the
  // button 409s -- which is exactly what it did until this assertion existed.
  const revealWrite = writes.find((w) => w.path.endsWith("/reveal"));
  expect(revealWrite).toBeTruthy();
  expect(revealWrite!.body).toEqual({ force: true });
  await expect(
    page.getByText(meanPercent, { exact: true }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Prepare draft" }).click();
  await page.locator(".draft-verification > summary").click();
  await expect(page.getByText("c1 · supported", { exact: true })).toBeVisible();
  await page
    .getByLabel("Decision note")
    .fill("Reviewed panel and indicator evidence.");
  await page
    .getByLabel("Decision to inform", { exact: true })
    .fill("Pre-position shelter");
  await page
    .getByLabel("Decision owner", { exact: true })
    .fill("NGO preparedness lead");
  await page
    .getByLabel("Decision needed by", { exact: true })
    .fill("2026-11-20");
  await page.getByRole("button", { name: "Edit probability" }).click();
  await page.getByLabel("Edited probability").selectOption("Very High");
  await page.getByRole("button", { name: "Save edited decision" }).click();
  await expect(
    page.getByRole("heading", { name: "Decision log" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Resolve risk and score forecasts" }),
  ).toBeDisabled();
  await page
    .getByText("Edit question and resolution rules", { exact: true })
    .click();
  await page.getByRole("button", { name: "Freeze question contract" }).click();
  await expect(
    page.getByText("Contract frozen and confirmed by the API."),
  ).toBeVisible();
  await page.getByLabel("Resolution date (UTC)").fill("2026-11-05");
  await page.getByLabel("I confirm this is an observed outcome.").check();
  await page
    .getByRole("button", { name: "Resolve risk and score forecasts" })
    .click();
  await expect(
    page.getByRole("status").filter({ hasText: "8 scores written" }),
  ).toBeVisible();
  expect(writes.find((w) => w.path === "/pulses")?.body).toEqual({
    risk_id: "R1043",
    reason: "analyst",
  });
  expect(writes.find((w) => w.path.endsWith("/decision"))?.body).toMatchObject({
    action: "edit",
    edited_probability: "Very High",
  });
  expect(writes.find((w) => w.path.endsWith("/resolve"))?.body).toEqual({
    outcome: "materialised",
    resolved_at: "2026-11-05T00:00:00Z",
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `test-results/live-desk-${info.project.name}.png`,
    fullPage: true,
  });
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});
test("ledger suppresses small groups and reports failed verification; calibration stays private", async ({
  page,
}, info) => {
  await contractApi(page);
  await page.goto("/ledger");
  await page.locator(".ledger-record > summary").first().click();
  await expect(
    page.locator(".ledger-stats").getByText("8 contributions", { exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: /R0987/ })).toHaveCount(0);
  await expect(page.getByText("quiet-heron")).toHaveCount(0);
  await page.getByRole("button", { name: "Verify entry" }).click();
  await expect(page.getByRole("status").first()).toContainText("hash mismatch");
  await page.goto("/me/private-invitation/calibration");
  await page
    .getByRole("button", { name: "View my private calibration" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Resolved forecast calibration" }),
  ).toBeVisible();
  await expect(
    page.getByText(calibration.mean_brier.toFixed(2), { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: `test-results/calibration-${info.project.name}.png`,
    fullPage: true,
  });
  await page.goto("/calibration");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Private calibration",
  );
  await expect(
    page.getByText(calibration.mean_brier.toFixed(2), { exact: true }),
  ).toHaveCount(0);
  await page.goto("/expert");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Expert card",
  );
  await expect(
    page.getByRole("button", { name: "Submit", exact: true }),
  ).toHaveCount(0);
});
test("network errors retry without fixture fallback and expert answers use selected values", async ({
  page,
}) => {
  await page.route("http://127.0.0.1:18000/**", (route) =>
    route.abort("connectionrefused"),
  );
  await page.goto("/desk");
  await expect(page.getByRole("alert")).toContainText("Cannot reach the API");
  await expect(page.getByRole("button", { name: "Load answers" })).toHaveCount(
    0,
  );
  await page.unrouteAll();
  const writes = await contractApi(page);
  await page.getByRole("button", { name: "Refresh risks" }).click();
  await expect(page.getByRole("button", { name: "Ask panel" })).toBeEnabled();
  await page.goto("/e/private-invitation");
  await page
    .getByRole("button", { name: "Pseudonym Nickname to peers" })
    .click();
  await submitCard(page);
  await expect(
    page.getByRole("heading", {
      name: "Submitted. You’ll get the group outcome.",
    }),
  ).toBeVisible();
  expect(writes.find((w) => w.path.endsWith("/answer"))?.body).toMatchObject({
    mask: "pseudonym",
    probability: 0.5,
    panel_share_yes: 0.5,
    changed_mind: false,
    stance: "estimate",
    round: 1,
    confidence: 3,
    source_tag: null,
  });
  await expect(page.getByText("Fixture receipt · not a live seal")).toHaveCount(
    0,
  );
});

test("v2 application and committee requests do not invent approval or credentials", async ({
  page,
}) => {
  const writes = await contractApi(page);
  await page.goto("/apply");
  await page
    .getByLabel("This is a synthetic expert application.", { exact: false })
    .check();
  await page
    .getByRole("button", { name: "Apply for committee review" })
    .click();
  await page
    .getByRole("link", { name: "Review synthetic application" })
    .click();
  await page.getByRole("button", { name: "Record my approval" }).click();
  await expect(
    page.getByRole("heading", { name: "Awaiting second approval" }),
  ).toBeVisible();
  expect(writes.find((w) => w.path === "/experts/apply")?.body).toMatchObject({
    geo_tags: ["TCD", "SDN"],
    theme_tags: ["conflict"],
    channel: "email",
  });
  expect(
    writes.find((w) => w.path === "/experts/X-0009/approve")?.body,
  ).toEqual({});
});

test("uncorroborated API claims remain to verify and block publication", async ({
  page,
}) => {
  await contractApi(page);
  await page.route("**/pulses/P-0001/draft", (route) =>
    route.fulfill({
      json: draft,
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.goto("/desk");
  await page.getByRole("button", { name: "Ask panel" }).click();
  await expect(
    revealButton(page),
  ).toBeEnabled();
  await revealButton(page).click();
  await page.getByRole("button", { name: "Prepare draft" }).click();
  await expect(
    page.getByRole("heading", { name: "To verify before inclusion" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Accept draft" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Reject draft" }),
  ).toBeEnabled();
});

test("a result for another pulse is not revealed on the selected desk", async ({
  page,
}) => {
  await contractApi(page);
  await page.route("**/pulses/P-0001/reveal", (route) =>
    route.fulfill({
      json: { ...result, pulse_id: "P-another" },
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.goto("/desk");
  await page.getByRole("button", { name: "Ask panel" }).click();
  await revealButton(page).click();
  await expect(page.getByRole("alert")).toContainText("different pulse");
  await expect(
    page.getByRole("button", { name: "Prepare draft" }),
  ).toBeDisabled();
  await expect(
    page.getByText("Equal-weight mean", { exact: true }),
  ).toHaveCount(0);
});

test("verification trail distinguishes backend validity, usable anchors and mismatched timestamps", async ({
  page,
}) => {
  await contractApi(page);
  let receipt = {
    valid: true,
    sealed_at: ledger.entries[0].sealed_at,
    anchor: null as string | null,
  };
  await page.route("**/ledger/verify", (route) =>
    route.fulfill({
      json: receipt,
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.goto("/ledger");
  await page.locator(".ledger-record > summary").first().click();
  const trail = page.getByRole("region", {
    name: "From contribution to verification",
  });
  await expect(
    trail.getByRole("heading", { name: "External anchor not checked" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Verify entry", exact: true }).click();
  await expect(
    trail.getByRole("button", {
      name: "Verified API check passed",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    trail.getByRole("heading", { name: "No external anchor", exact: true }),
  ).toBeVisible();
  receipt = { ...receipt, anchor: "https://example.org/proof/round-1" };
  await page.getByRole("button", { name: "Verify entry", exact: true }).click();
  await expect(
    trail.getByRole("link", { name: "Open timestamp proof" }),
  ).toHaveAttribute("href", receipt.anchor);
  await expect(
    trail.getByRole("heading", { name: "External anchor supplied" }),
  ).toBeVisible();
  receipt = { ...receipt, anchor: "javascript:alert(1)" };
  await page.getByRole("button", { name: "Verify entry", exact: true }).click();
  await expect(
    trail.getByRole("heading", { name: "No external anchor", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /timestamp proof|Timestamp anchor/ }),
  ).toHaveCount(0);
  receipt = {
    ...receipt,
    valid: false,
    anchor: "https://example.org/proof/round-1",
  };
  await page.getByRole("button", { name: "Verify entry", exact: true }).click();
  await expect(
    trail.getByRole("button", { name: "Verified Check failed", exact: true }),
  ).toBeVisible();
  await expect(
    trail.getByRole("link", { name: "Open timestamp proof" }),
  ).toHaveCount(0);
  receipt = { ...receipt, valid: true, sealed_at: "2020-01-01T00:00:00Z" };
  await page.getByRole("button", { name: "Verify entry", exact: true }).click();
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "receipt timestamp does not match" }),
  ).toBeVisible();
  await expect(
    trail.getByRole("button", { name: "Verified Check failed", exact: true }),
  ).toBeVisible();
});

test("v3 abstentions submit null estimates and calibration waits for opt-in and five resolutions", async ({
  page,
}) => {
  const writes = await contractApi(page);
  await page.goto("/e/private-invitation");
  await page
    .getByRole("button", { name: "Not enough evidence", exact: true })
    .click();
  await expect(page.getByRole("slider")).toHaveCount(0);
  await submitCard(page);
  await expect(
    page.getByRole("heading", {
      name: "Submitted. You’ll get the group outcome.",
    }),
  ).toBeVisible();
  expect(writes.find((w) => w.path.endsWith("/answer"))?.body).toMatchObject({
    stance: "not_enough_evidence",
    probability: null,
    confidence: null,
    panel_share_yes: null,
    round: 1,
  });
  let requests = 0;
  await page.route(
    "http://127.0.0.1:18000/me/private-invitation/calibration",
    (route) => {
      requests++;
      return route.fulfill({
        json: { ...calibration, n_resolved: 4 },
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    },
  );
  await page.goto("/me/private-invitation/calibration");
  await expect(
    page.getByRole("button", { name: "View my private calibration" }),
  ).toBeVisible();
  expect(requests).toBe(0);
  await page
    .getByRole("button", { name: "View my private calibration" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Five resolutions required" }),
  ).toBeVisible();
  expect(requests).toBe(1);
  await expect(
    page.getByText(calibration.mean_brier.toFixed(2), { exact: true }),
  ).toHaveCount(0);
});

test("v3 aggregate stays primary and mismatched outcome reports are withheld", async ({
  page,
}) => {
  await contractApi(page);
  // A weighted mean deliberately far from the equal-weight one, to prove which of the two the
  // desk leads with. Held in a const so the number below cannot drift from the number served.
  const overriddenWeighted = 0.83;
  await page.route("**/pulses/P-0001/reveal", (route) =>
    route.fulfill({
      json: { ...result, weighted_mean: overriddenWeighted },
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.goto("/desk");
  await page.getByRole("button", { name: "Ask panel", exact: true }).click();
  await revealButton(page).click();
  await expect(
    page
      .getByText("Equal-weight mean", { exact: true })
      .locator("..")
      .getByText(meanPercent, { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(
      `Secondary weighted mean: ${Math.round(overriddenWeighted * 100)}%.`,
      { exact: false },
    ),
  ).toBeVisible();
  // The verbatim minority rationale is gone from the result (v3.4). What the desk shows is the
  // unattributed summary, written from themes; the sentences live in the verification queue.
  await expect(
    page.getByText(result.disagreement[0].summary, { exact: false }),
  ).toBeVisible();
  await page
    .getByText("Edit question and resolution rules", { exact: true })
    .click();
  await page.getByRole("tab", { name: "Outcome", exact: true }).click();
  await page.getByRole("button", { name: "Open group outcome report" }).click();
  await expect(page.locator(".outcome-report")).toContainText(
    `Equal-weight group mean: ${meanPercent}`,
  );
  await page.route("**/pulses/P-0001/outcome-report", (route) =>
    route.fulfill({
      json: {
        pulse_id: "P-other",
        group_mean: result.mean,
        outcome: "materialised",
        analyst_decision_summary: "Must not render",
      },
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.getByRole("button", { name: "Open group outcome report" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "does not match a confirmed group",
  );
  await expect(page.locator(".outcome-report")).toHaveCount(0);
  await expect(page.getByText("Must not render", { exact: true })).toHaveCount(
    0,
  );
});

test("a successful status without a frozen contract cannot unlock scoring", async ({
  page,
}) => {
  const writes = await contractApi(page);
  await page.route("**/risks/R1043/contract", (route) =>
    route.fulfill({
      json: risks.risks[0],
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.goto("/desk");
  await page.getByRole("button", { name: "Ask panel", exact: true }).click();
  await page
    .getByText("Edit question and resolution rules", { exact: true })
    .click();
  await page.getByRole("button", { name: "Freeze question contract" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "did not confirm this frozen contract",
  );
  await revealButton(page).click();
  await page.getByRole("button", { name: "Prepare draft" }).click();
  await page.getByLabel("Decision note").fill("Keep High for the demo.");
  await page
    .getByLabel("Decision to inform", { exact: true })
    .fill("Pre-position shelter");
  await page
    .getByLabel("Decision owner", { exact: true })
    .fill("Preparedness lead");
  await page
    .getByLabel("Decision needed by", { exact: true })
    .fill("2026-11-20");
  await page.getByRole("button", { name: "Accept draft", exact: true }).click();
  await page.getByLabel("Resolution date (UTC)").fill("2026-11-05");
  await page.getByLabel("I confirm this is an observed outcome.").check();
  await expect(
    page.getByRole("button", { name: "Resolve risk and score forecasts" }),
  ).toBeDisabled();
  expect(writes.some((w) => w.path.endsWith("/resolve"))).toBe(false);
});
