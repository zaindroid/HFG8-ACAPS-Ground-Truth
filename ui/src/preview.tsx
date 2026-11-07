// Standalone entry for a hosted preview of the expert card.
//
// The app routes on location.pathname, and a hosted preview is served from a path of the
// host's choosing, so /e/demo never matches and the router would answer "page not found".
// This entry renders the card directly instead. Latin subsets only: the full @fontsource
// import pulls about fifty files for scripts this card does not use.
import React from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-500.css";
import "@fontsource/inter/latin-600.css";
import { ExpertCard } from "./ExpertCard";
import "./theme.css";
import "./styles.css";
import "./polish.css";
import "./risk-insights.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ExpertCard token="demo" />
  </React.StrictMode>,
);
