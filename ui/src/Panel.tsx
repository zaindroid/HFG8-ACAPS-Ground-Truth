import type { ReactNode } from "react";

/** The standard panel wrapper. Lives in its own module so components can use it
    without importing from LiveWorkspace, which would create an import cycle. */
export function Section({
  title,
  children,
  className = "",
  id,
}: {
  title: string;
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={`workspace-panel ${className}`}>
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}
