import { useId, useState } from "react";
import {
  FileInput,
  LockKeyhole,
  UsersRound,
  FileCheck2,
  ShieldCheck,
  ArrowUpRight,
  Link2,
  Unplug,
} from "lucide-react";
import { CopyButton } from "./LiveWorkspace";
import { safeUrl, type LedgerEntry } from "./service";
import { date } from "./desk-model";

type Receipt = { valid: boolean; anchor: string | null };
export function VerificationTrail({
  entry,
  receipt,
  fixture = false,
  decision,
}: {
  entry: LedgerEntry;
  receipt?: Receipt;
  fixture?: boolean;
  decision?: { action: string; at: string };
}) {
  const [selected, setSelected] = useState(1);
  const id = useId();
  const n = entry.n ?? entry.honesty?.n;
  const rejected =
    entry.honesty?.panel_view_rejected || decision?.action === "reject";
  const anchor =
    !fixture && receipt?.valid && receipt.anchor
      ? safeUrl(receipt.anchor)
      : undefined;
  const steps = [
    {
      title: "Submitted",
      status: n !== undefined ? `${n} contributions` : "Count not supplied",
      icon: FileInput,
      recorded: n !== undefined,
      text: "The panel’s contribution count is recorded. Individual answers and individual submission times are not exposed in this ledger.",
      time: null,
    },
    {
      title: "Committed",
      status: "Receipt recorded",
      icon: LockKeyhole,
      recorded: true,
      text: "The ledger records a hash of the round’s sorted commitments. A commitment supports timing and consistency checks; it does not hide answers from the operator.",
      time: entry.sealed_at,
    },
    {
      title: "Revealed",
      status: "Group view available",
      icon: UsersRound,
      recorded: true,
      text: "Only an aggregate is displayed here. At least five estimates is a disclosure rule, not a guarantee of anonymity. The reveal timestamp was not supplied in this ledger entry.",
      time: null,
    },
    {
      title: "Analyst decision",
      status: rejected
        ? "Panel view rejected"
        : decision?.action === "edit"
          ? "Edited"
          : decision?.action === "accept"
            ? "Accepted"
            : "Decision published",
      icon: FileCheck2,
      recorded: true,
      text: rejected
        ? entry.honesty?.analyst_rationale ||
          "The analyst rejected the panel view. No rationale was supplied."
        : "The ledger records an analyst decision. A panel forecast never changes an ACAPS product automatically.",
      time: decision?.at || null,
    },
    {
      title: "Verified",
      status: receipt
        ? receipt.valid
          ? fixture
            ? "Receipt matched"
            : "API check passed"
          : "Check failed"
        : "Not checked",
      icon: ShieldCheck,
      recorded: receipt?.valid === true,
      text: !receipt
        ? "Use the Verify control below to check this record. Selecting a stage does not verify it."
        : !receipt.valid
          ? "The verification check failed. This record must not be treated as verified."
          : fixture
            ? "The hash matches the stored receipt. No external proof is attached."
            : "The API reports that this ledger hash matches the round’s commitments. This is the backend’s verdict, not independent proof of an on-chain transaction.",
      time: null,
    },
  ];
  const step = steps[selected];
  return (
    <section
      className="verification-trail"
      aria-labelledby={`${id}-heading ${id}-context`}
    >
      <div className="trail-heading">
        <div>
          <p id={`${id}-context`}>
            Record provenance · {entry.risk_id} / {entry.pulse_id}
          </p>
          <h3 id={`${id}-heading`}>From contribution to verification</h3>
        </div>
        <span className="trail-mode">
          {fixture ? "Receipt record" : "API record"}
        </span>
      </div>
      <ol className="trail-stages" aria-label="Verification stages">
        {steps.map((item, index) => {
          const Icon = item.icon;
          return (
            <li key={item.title}>
              <button
                type="button"
                aria-pressed={selected === index}
                aria-controls={`${id}-detail`}
                onClick={() => setSelected(index)}
                className={`${item.recorded ? "recorded" : "pending"} ${selected === index ? "selected" : ""}`}
              >
                <span className="trail-node">
                  <Icon size={22} aria-hidden="true" />
                </span>
                <span className="trail-stage-title">{item.title}</span>
                <span className="trail-stage-status">{item.status}</span>
              </button>
            </li>
          );
        })}
      </ol>
      <div className="trail-detail" id={`${id}-detail`}>
        <div>
          <h4>{step.title}</h4>
          <span className="trail-detail-status">{step.status}</span>
        </div>
        <p>{step.text}</p>
        {step.time ? (
          <p className="trail-time">
            <time dateTime={step.time}>{date(step.time)}</time>
          </p>
        ) : (
          <p className="trail-time">
            {selected === 4
              ? "Verification time not supplied"
              : "Separate timestamp not supplied"}
          </p>
        )}
        {selected === 1 && (
          <div className="trail-hash">
            <span>Ledger verification hash</span>
            <code>{entry.verify_hash}</code>
            <CopyButton
              value={entry.verify_hash}
              label="Copy verification hash"
            />
          </div>
        )}
      </div>
      <div className={`trail-anchor ${anchor ? "has-anchor" : ""}`}>
        {anchor ? (
          <Link2 size={20} aria-hidden="true" />
        ) : (
          <Unplug size={20} aria-hidden="true" />
        )}
        <div>
          <h4>
            {anchor
              ? "External anchor supplied"
              : fixture
                ? "No external anchor"
                : !receipt
                  ? "External anchor not checked"
                  : !receipt.valid
                    ? "Verification unresolved"
                    : "No external anchor"}
          </h4>
          <p>
            {fixture
              ? "No external timestamp proof is attached."
              : !receipt
                ? "Run verification to check whether the API supplies an external timestamp proof."
                : !receipt.valid
                  ? "An external proof cannot establish a valid ledger record while this check has failed."
                  : anchor
                    ? "The API supplied a proof link. Open it for independent checks; this view does not establish blockchain confirmation."
                    : "No usable external timestamp proof was supplied for this record."}
          </p>
          {anchor && (
            <a href={anchor} target="_blank" rel="noreferrer">
              Open timestamp proof <ArrowUpRight size={14} aria-hidden="true" />
            </a>
          )}
        </div>
      </div>
    </section>
  );
}
