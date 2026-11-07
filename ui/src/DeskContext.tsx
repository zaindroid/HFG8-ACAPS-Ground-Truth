import {
  Children,
  useId,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
} from "react";
import {
  Target,
  UsersRound,
  ScanSearch,
  GitBranch,
  ClipboardCheck,
} from "lucide-react";
const views = {
  Question: { icon: Target, description: "What are we forecasting?" },
  "Panel details": { icon: UsersRound, description: "Who covers this risk?" },
  "Review notes": {
    icon: ScanSearch,
    description: "What needs a closer look?",
  },
  Method: { icon: GitBranch, description: "How is the forecast calculated?" },
  Outcome: { icon: ClipboardCheck, description: "What happened afterward?" },
};
export function ContextSection({
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return <>{children}</>;
}
export function DeskContext({ children }: { children: ReactNode }) {
  const groups = Children.toArray(children) as ReactElement<{
    label: string;
  }>[];
  const [active, setActive] = useState(0);
  const id = useId();
  const tabs = useRef<HTMLDivElement>(null);
  return (
    <section className="desk-context" aria-label="Analysis context">
      <div className="desk-context-heading">
        <h2>Forecast brief</h2>
        <p>
          The question, the people behind it and the checks that keep it
          accountable.
        </p>
      </div>
      <div role="tablist" aria-label="Context views" ref={tabs}>
        {groups.map((group, i) => (
          <button
            key={group.props.label}
            type="button"
            role="tab"
            aria-label={group.props.label}
            id={`${id}-tab-${i}`}
            aria-controls={`${id}-panel-${i}`}
            aria-selected={i === active}
            tabIndex={i === active ? 0 : -1}
            onClick={() => setActive(i)}
            onKeyDown={(e) => {
              let next = i;
              if (e.key === "ArrowRight") next = (i + 1) % groups.length;
              else if (e.key === "ArrowLeft")
                next = (i - 1 + groups.length) % groups.length;
              else if (e.key === "Home") next = 0;
              else if (e.key === "End") next = groups.length - 1;
              else return;
              e.preventDefault();
              setActive(next);
              (tabs.current?.children[next] as HTMLElement)?.focus();
            }}
          >
            {(() => {
              const view = views[group.props.label as keyof typeof views];
              const Icon = view?.icon || Target;
              return (
                <>
                  <Icon size={19} aria-hidden="true" />
                  <span>
                    <strong>{group.props.label}</strong>
                    <small>{view?.description}</small>
                  </span>
                </>
              );
            })()}
          </button>
        ))}
      </div>
      {groups.map((group, i) => (
        <div
          role="tabpanel"
          key={group.props.label}
          id={`${id}-panel-${i}`}
          aria-labelledby={`${id}-tab-${i}`}
          hidden={i !== active}
          className="desk-context-body"
        >
          {group}
        </div>
      ))}
    </section>
  );
}
