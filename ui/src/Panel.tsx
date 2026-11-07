import type { ReactNode } from "react";

/** The standard panel wrapper. Lives in its own module so components can use it
    without importing from LiveWorkspace, which would create an import cycle. */
export function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="workspace-panel">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}
