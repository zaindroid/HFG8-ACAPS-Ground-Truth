import { useEffect, useMemo, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  Check,
  Copy,
  Mail,
  MessageCircle,
  MessageSquare,
  Phone,
  Send,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";
import { Frame } from "./LiveWorkspace";
import { mock } from "./api";
import { api } from "./service";
import risksFixture from "../../fixtures/GET_risks.json";
import matchFixture from "../../fixtures/GET_panels_match.json";
import contactsFixture from "../../fixtures/GET_reach_contacts.json";
import "./ask-experts.css";

/* The analyst's step between an alert and a round: choose the risk, say how sure you are of the
   current rating, see who can speak to it, and send each expert their own link on the channel
   they chose. Profiles are synthetic. Four are ACAPS's reader personas (Emily, Jose, Pierre,
   Aisha) recast as experts on the Chad case; three seats are for the people in the room. */

type RiskRow = {
  risk_id: string;
  title: string;
  country: string;
  probability_acaps: string;
  level?: string;
};
type MatchExpert = {
  expert_id: string;
  pseudonym: string;
  theme_tags: string[];
  region: string;
  affiliation_tag: string;
  match: number;
};
type Contact = {
  expert_id: string;
  org_type: string;
  coverage_area: string;
  languages: string[];
  channel_pref: string;
  hour_pref?: number;
  tz?: string;
  status: string;
};
type Link = {
  token: string;
  pulse_id: string;
  pseudonym: string;
  region: string;
  answered: boolean;
  card_url: string;
};

type Persona = {
  name: string;
  role: string;
  base: string;
  quote: string;
  knows: string[];
};
// Synthetic profiles. Names and roles follow ACAPS's own reader personas, adapted to Chad.
const PERSONAS: Record<string, Persona> = {
  "X-syn-01": {
    name: "Emily",
    role: "Head of methodology, donor agency emergency team",
    base: "Headquarters, follows eastern Chad",
    quote:
      "I validate nutrition and health data with partners before it reaches a decision.",
    knows: ["nutrition and health data", "source reliability", "methodology"],
  },
  "X-syn-02": {
    name: "Jose",
    role: "Emergency specialist, UN regional office",
    base: "Amman, covers Sudan and Chad",
    quote:
      "My country teams see things before the platforms do. I want that fed back fast.",
    knows: ["Sudan displacement", "protection", "regional spill-over"],
  },
  "X-syn-03": {
    name: "Pierre",
    role: "MEAL officer, Red Cross and Red Crescent",
    base: "Abéché, eastern Chad",
    quote:
      "I am one of the first deployed. I need to know quickly where we are and where we will be.",
    knows: ["needs assessments", "food and displacement", "scenarios"],
  },
  "X-syn-04": {
    name: "Aisha",
    role: "Country director, international NGO",
    base: "N'Djamena, team of 150",
    quote:
      "What I don't get is someone telling me how the next months will change my programme.",
    knows: ["humanitarian access", "operations", "political outlook"],
  },
};
const JUDGE_SEATS = ["X-guest-01", "X-guest-02", "X-guest-03"];
const CONFIDENCE = ["Not sure", "Fairly sure", "Very sure"] as const;
const roundOpenFor = (riskId: string) => riskId === "R1043";

const channelLabel: Record<string, string> = {
  email: "Email",
  whatsapp: "WhatsApp",
  sms: "SMS",
  signal: "Signal",
  teams: "Teams",
  call: "Phone call",
};
function ChannelIcon({ channel }: { channel: string }) {
  const props = { size: 16, "aria-hidden": true } as const;
  if (channel === "email") return <Mail {...props} />;
  if (channel === "call") return <Phone {...props} />;
  if (channel === "sms") return <MessageSquare {...props} />;
  return <MessageCircle {...props} />;
}
function message(channel: string, name: string, country: string, url: string) {
  const hello = name ? `Hi ${name}` : "Hello";
  if (channel === "email")
    return `${hello},\n\nOne question about ${country} from the ACAPS analyst team. It takes about a minute and your answer stays sealed until the deadline.\n\n${url}\n\nReply STOP to stop receiving these.`;
  if (channel === "call")
    return `Scheduled call: the question about ${country} is read out, you answer by voice, and the analyst confirms it back. Link for the record: ${url}`;
  return `${hello}, one question about ${country} from ACAPS, about a minute: ${url} (reply STOP to stop)`;
}

export function AskExperts() {
  const [risks, setRisks] = useState<RiskRow[]>([]);
  const [riskId, setRiskId] = useState("R1043");
  const [confidence, setConfidence] =
    useState<(typeof CONFIDENCE)[number]>("Fairly sure");
  const [experts, setExperts] = useState<MatchExpert[]>([]);
  const [contacts, setContacts] = useState<Record<string, Contact>>({});
  const [links, setLinks] = useState<Link[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [copied, setCopied] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (mock) {
      setRisks((risksFixture as { risks: RiskRow[] }).risks);
      return;
    }
    api<{ risks: RiskRow[] }>("/risks")
      .then((r) => setRisks(r.risks))
      .catch((e) => setError((e as Error).message));
  }, []);

  useEffect(() => {
    setSent(false);
    if (mock) {
      setExperts((matchFixture as { experts: MatchExpert[] }).experts);
      setContacts(
        Object.fromEntries(
          (contactsFixture as { contacts: Contact[] }).contacts.map((c) => [
            c.expert_id,
            c,
          ]),
        ),
      );
      return;
    }
    api<{ experts: MatchExpert[] }>(
      `/panels/match?risk_id=${encodeURIComponent(riskId)}`,
    )
      .then((m) => setExperts(m.experts))
      .catch((e) => setError((e as Error).message));
    api<{ contacts: Contact[] }>("/reach/contacts")
      .then((c) =>
        setContacts(
          Object.fromEntries(c.contacts.map((x) => [x.expert_id, x])),
        ),
      )
      .catch(() => setContacts({}));
  }, [riskId]);

  // Links and arrivals: poll while the page is open, so judges' answers show up live.
  useEffect(() => {
    if (mock) {
      setLinks(
        ["X-syn-01", "X-syn-02", "X-syn-03", "X-syn-05", ...JUDGE_SEATS].map(
          (id, i) => ({
            token: "demo",
            pulse_id: "P-0001",
            pseudonym: id,
            region: id.startsWith("X-guest") ? "The Hague" : "",
            answered: i < 4,
            card_url: "/e/demo",
          }),
        ),
      );
      return;
    }
    let live = true;
    const load = () =>
      api<{ links: Link[] }>("/demo/links")
        .then((r) => live && setLinks(r.links))
        .catch(() => undefined);
    load();
    const timer = window.setInterval(load, 3000);
    return () => {
      live = false;
      window.clearInterval(timer);
    };
  }, []);

  const risk = risks.find((r) => r.risk_id === riskId);
  const country = risk?.country || "Chad";
  // Personas first, then the rest of the matched panel.
  const panel = useMemo(() => {
    const ids = new Set(experts.map((e) => e.expert_id));
    const extra = Object.keys(PERSONAS)
      .filter((id) => !ids.has(id))
      .map((id): MatchExpert => ({
        expert_id: id,
        pseudonym: "",
        theme_tags: [],
        region: contacts[id]?.coverage_area || "",
        affiliation_tag: contacts[id]?.org_type || "",
        match: 0,
      }));
    return [...experts, ...extra]
      .filter(
        (e) =>
          !!PERSONAS[e.expert_id] ||
          links.some(
            (l) => l.region !== "The Hague" && l.pseudonym === e.pseudonym,
          ) ||
          !roundOpenFor(riskId),
      )
      .sort(
        (a, b) =>
          Number(!!PERSONAS[b.expert_id]) - Number(!!PERSONAS[a.expert_id]),
      );
  }, [experts, contacts, links, riskId]);
  const linkFor = (pseudonym: string, expertId: string) =>
    links.find(
      (l) =>
        l.region !== "The Hague" &&
        (l.pseudonym === pseudonym || l.pseudonym === expertId),
    );
  const roundOpen = riskId === "R1043";
  const seats = links.filter((l) => l.region === "The Hague").slice(0, 3);
  const panelLinks = links.filter((l) => l.region !== "The Hague");
  const answeredPanel = panelLinks.filter((l) => l.answered).length;
  const answeredSeats = seats.filter((l) => l.answered).length;
  const origin = typeof location !== "undefined" ? location.origin : "";
  const selected = panel.find((e) => e.expert_id === open);

  const copy = async (key: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(key);
      window.setTimeout(() => setCopied(""), 1500);
    } catch {
      setCopied("");
    }
  };

  return (
    <Frame
      title="Ask experts"
      subtitle="Choose a risk, check who can speak to it, and send each expert their own link."
    >
      {error && (
        <p className="ask-error" role="alert">
          {error}
        </p>
      )}

      <section className="ask-step" aria-labelledby="ask-risk">
        <h2 id="ask-risk">
          <span className="ask-num">1</span> Which risk needs a second look?
        </h2>
        <div className="ask-risks" role="radiogroup" aria-label="Risks">
          {risks.slice(0, 6).map((r) => (
            <button
              type="button"
              role="radio"
              aria-checked={r.risk_id === riskId}
              key={r.risk_id}
              className={r.risk_id === riskId ? "ask-risk on" : "ask-risk"}
              onClick={() => setRiskId(r.risk_id)}
            >
              <span className="ask-risk-top">
                {r.country} · {r.risk_id}
                <b
                  className={`band band-${r.probability_acaps.toLowerCase().replace(/\s/g, "-")}`}
                >
                  {r.probability_acaps}
                </b>
              </span>
              <span className="ask-risk-title">{r.title}</span>
            </button>
          ))}
        </div>
        <div className="ask-confidence">
          <span id="conf-label">How sure are you of the current rating?</span>
          <div role="radiogroup" aria-labelledby="conf-label">
            {CONFIDENCE.map((c) => (
              <button
                type="button"
                role="radio"
                aria-checked={c === confidence}
                key={c}
                className={c === confidence ? "on" : ""}
                onClick={() => setConfidence(c)}
              >
                {c}
              </button>
            ))}
          </div>
          <small>
            {confidence === "Very sure"
              ? "A short check: the panel is asked to confirm or challenge."
              : "The panel is asked for its own estimate first, with the rating hidden."}
          </small>
        </div>
      </section>

      <section className="ask-step" aria-labelledby="ask-panel">
        <h2 id="ask-panel">
          <span className="ask-num">2</span> Who can speak to it
          <small>
            {panel.length} matched · at most 3 from one organisation
          </small>
        </h2>
        <div className="ask-grid">
          {panel.map((e) => {
            const persona = PERSONAS[e.expert_id];
            const contact = contacts[e.expert_id];
            const channel = contact?.channel_pref || "email";
            const stopped = contact && contact.status !== "active";
            return (
              <button
                type="button"
                key={e.expert_id}
                className={persona ? "ask-expert persona" : "ask-expert"}
                onClick={() => setOpen(e.expert_id)}
                aria-haspopup="dialog"
              >
                <span className="ask-avatar" aria-hidden="true">
                  {(persona?.name || e.pseudonym || "?")
                    .slice(0, 1)
                    .toUpperCase()}
                </span>
                <span className="ask-expert-name">
                  {persona ? persona.name : e.pseudonym}
                  <small>
                    {persona
                      ? persona.role
                      : `${e.affiliation_tag} · ${e.region}`}
                  </small>
                </span>
                <span className={stopped ? "ask-channel off" : "ask-channel"}>
                  <ChannelIcon channel={channel} />
                  {stopped ? "Paused" : channelLabel[channel] || channel}
                </span>
                {e.theme_tags.length > 0 && (
                  <span className="ask-tags">
                    {e.theme_tags.map((t) => (
                      <i key={t}>{t}</i>
                    ))}
                  </span>
                )}
              </button>
            );
          })}
        </div>
        <p className="ask-note">
          Profiles are synthetic. Four follow ACAPS&rsquo;s own reader personas,
          recast for the Chad case.
        </p>
      </section>

      <section className="ask-step" aria-labelledby="ask-send">
        <h2 id="ask-send">
          <span className="ask-num">3</span> Send one question, sealed until the
          deadline
        </h2>
        {!roundOpen ? (
          <p className="ask-note">
            The live round in this demo runs on Chad, R1043. Choosing this risk
            would open a new round with its own links.
          </p>
        ) : !sent ? (
          <button
            type="button"
            className="primary ask-send"
            onClick={() => setSent(true)}
          >
            <Send size={18} aria-hidden="true" /> Create personal links for{" "}
            {panel.length} experts
          </button>
        ) : (
          <div className="ask-outbox">
            {panel.map((e) => {
              const persona = PERSONAS[e.expert_id];
              const contact = contacts[e.expert_id];
              const channel = contact?.channel_pref || "email";
              const link = linkFor(e.pseudonym, e.expert_id);
              if (!link) return null;
              const url = `${origin}${link.card_url}`;
              const text = message(channel, persona?.name || "", country, url);
              return (
                <div className="ask-msg" key={e.expert_id}>
                  <div className="ask-msg-head">
                    <ChannelIcon channel={channel} />
                    <b>{persona?.name || e.pseudonym}</b>
                    <span>{channelLabel[channel] || channel}</span>
                    {link?.answered && (
                      <span className="ask-sealed">
                        <ShieldCheck size={14} aria-hidden="true" /> Answer
                        sealed
                      </span>
                    )}
                  </div>
                  <div className="ask-msg-body">
                    <pre>{text}</pre>
                    {/* The same one-time link the message carries, as a code.
                        A phone in the room is the fastest way onto a card, and
                        an expert reached by voice has no link to tap at all. */}
                    <QRCodeSVG
                      className="ask-msg-qr"
                      value={url}
                      size={104}
                      level="M"
                      marginSize={2}
                      title={`${persona?.name || e.pseudonym}: expert card`}
                    />
                  </div>
                  <div className="ask-msg-actions">
                    <a href={url} target="_blank" rel="noreferrer">
                      Open their card
                    </a>
                    <button
                      type="button"
                      onClick={() => copy(e.expert_id, text)}
                    >
                      {copied === e.expert_id ? (
                        <Check size={15} aria-hidden="true" />
                      ) : (
                        <Copy size={15} aria-hidden="true" />
                      )}
                      {copied === e.expert_id ? "Copied" : "Copy message"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="ask-step ask-room" aria-labelledby="ask-room">
        <h2 id="ask-room">
          <span className="ask-num">4</span> Seats in the room
          <small>Scan, answer in a minute, watch it arrive</small>
        </h2>
        <div className="ask-room-grid">
          <div className="ask-seats">
            {(seats.length
              ? seats
              : JUDGE_SEATS.map(
                  (id) =>
                    ({
                      token: "demo",
                      card_url: "/e/demo",
                      answered: false,
                      pseudonym: id,
                    }) as Link,
                )
            ).map((seat, i) => (
              <figure
                key={seat.pseudonym + i}
                className={seat.answered ? "ask-seat done" : "ask-seat"}
              >
                <QRCodeSVG
                  value={`${origin}${seat.card_url}`}
                  size={168}
                  level="M"
                  marginSize={2}
                  title={`Seat ${i + 1}: expert card`}
                />
                <figcaption>
                  Seat {i + 1}
                  <span>{seat.answered ? "Answer sealed" : "Waiting"}</span>
                </figcaption>
              </figure>
            ))}
          </div>
          <div className="ask-live" aria-live="polite">
            <div className="ask-live-row">
              <Users size={20} aria-hidden="true" />
              <b>{answeredPanel}</b> of {panelLinks.length || 8} panel experts
              sealed
            </div>
            <div className="ask-dots" aria-hidden="true">
              {panelLinks.map((l) => (
                <i key={l.token} className={l.answered ? "on" : ""} />
              ))}
              {seats.map((l) => (
                <i key={l.token} className={l.answered ? "on seat" : "seat"} />
              ))}
            </div>
            <div className="ask-live-row">
              <ShieldCheck size={20} aria-hidden="true" />
              <b>{answeredSeats}</b> of {seats.length || 3} seats in the room
              sealed
            </div>
            <p>
              Nobody, including us, sees an answer before the reveal. After it,
              the same link shows each person what their answer changed.
            </p>
            <a className="button-link primary" href="/desk">
              Open the analyst desk
            </a>
          </div>
        </div>
      </section>

      {selected && (
        <div className="ask-backdrop" onClick={() => setOpen(null)}>
          <div
            className="ask-profile"
            role="dialog"
            aria-modal="true"
            aria-labelledby="ask-profile-name"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="ask-close"
              aria-label="Close profile"
              onClick={() => setOpen(null)}
            >
              <X size={18} />
            </button>
            {(() => {
              const persona = PERSONAS[selected.expert_id];
              const contact = contacts[selected.expert_id];
              const channel = contact?.channel_pref || "email";
              return (
                <>
                  <span className="ask-avatar big" aria-hidden="true">
                    {(persona?.name || selected.pseudonym || "?")
                      .slice(0, 1)
                      .toUpperCase()}
                  </span>
                  <h3 id="ask-profile-name">
                    {persona?.name || selected.pseudonym}
                  </h3>
                  <p className="ask-profile-role">
                    {persona?.role || `${selected.affiliation_tag} expert`}
                  </p>
                  {persona && (
                    <blockquote>&ldquo;{persona.quote}&rdquo;</blockquote>
                  )}
                  <dl>
                    <div>
                      <dt>Based</dt>
                      <dd>
                        {persona?.base ||
                          contact?.coverage_area ||
                          selected.region}
                      </dd>
                    </div>
                    <div>
                      <dt>Knows</dt>
                      <dd>
                        {(persona?.knows || selected.theme_tags).join(", ") ||
                          "General"}
                      </dd>
                    </div>
                    <div>
                      <dt>Reached by</dt>
                      <dd>
                        {channelLabel[channel] || channel}
                        {contact?.hour_pref !== undefined &&
                          `, around ${contact.hour_pref}:00 local`}
                      </dd>
                    </div>
                    <div>
                      <dt>Languages</dt>
                      <dd>{(contact?.languages || ["en"]).join(", ")}</dd>
                    </div>
                    <div>
                      <dt>Shown to colleagues as</dt>
                      <dd>
                        The mask they choose per answer: known, pseudonym or
                        anonymous
                      </dd>
                    </div>
                  </dl>
                  <p className="ask-note">Synthetic profile for the demo.</p>
                </>
              );
            })()}
          </div>
        </div>
      )}
    </Frame>
  );
}
