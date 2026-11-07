import { useId } from "react";
import { geoMercator, geoPath, geoCentroid } from "d3-geo";
import { feature } from "topojson-client";
import countries from "world-atlas/countries-110m.json";
import type { FeatureCollection, Geometry } from "geojson";
import type { Topology, GeometryCollection } from "topojson-specification";
import type { Match } from "./v2-types";
const world = feature(
  countries as unknown as Topology<{ countries: GeometryCollection }>,
  (countries as unknown as Topology<{ countries: GeometryCollection }>).objects
    .countries,
) as FeatureCollection<Geometry, { name: string }>;
const names: Record<string, string> = {
  TCD: "Chad",
  AFG: "Afghanistan",
  SDN: "Sudan",
  SSD: "S. Sudan",
  NER: "Niger",
  NGA: "Nigeria",
  CMR: "Cameroon",
  MLI: "Mali",
  ETH: "Ethiopia",
  KEN: "Kenya",
  SOM: "Somalia",
  MOZ: "Mozambique",
  MDG: "Madagascar",
  SYR: "Syria",
  YEM: "Yemen",
  HTI: "Haiti",
  UKR: "Ukraine",
  COL: "Colombia",
};
export function ExpertMap({
  experts,
  arrived,
}: {
  experts: Match["experts"];
  arrived?: number;
}) {
  const id = useId();
  const groups = new Map<string, { total: number; received: number }>();
  experts.forEach((e, i) => {
    const name = world.features.some((f) => f.properties.name === e.region)
      ? e.region!
      : names[e.geo_tags[0]];
    if (!name) return;
    const group = groups.get(name) || { total: 0, received: 0 };
    group.total++;
    if (arrived === undefined || i < arrived) group.received++;
    groups.set(name, group);
  });
  const selected = world.features.filter((f) => groups.has(f.properties.name));
  if (!selected.length)
    return <p>Location details are listed in the panel roster.</p>;
  const projection = geoMercator().fitExtent(
    [
      [35, 30],
      [365, 190],
    ],
    { type: "FeatureCollection", features: selected },
  );
  const path = geoPath(projection);
  return (
    <figure className="expert-map">
      <svg
        viewBox="0 0 400 245"
        role="img"
        aria-label={`Panel location map. ${[...groups].map(([name, g]) => `${name}: ${g.received} of ${g.total} experts${arrived === undefined ? " selected" : " received"}`).join(". ")}`}
      >
        <defs>
          <clipPath id={id}>
            <rect width="400" height="245" rx="8" />
          </clipPath>
        </defs>
        <g clipPath={`url(#${id})`}>
          {world.features.map((f) => (
            <path
              key={f.properties.name}
              d={path(f) || undefined}
              className={
                groups.has(f.properties.name)
                  ? "map-panel-country"
                  : "map-context-country"
              }
            />
          ))}
          {selected.map((f) => {
            const point = projection(geoCentroid(f));
            if (!point) return null;
            const group = groups.get(f.properties.name)!;
            return (
              <g
                key={f.properties.name}
                transform={`translate(${point[0]},${point[1]})`}
              >
                <circle
                  r="9"
                  className={
                    group.received ? "map-panel-dot received" : "map-panel-dot"
                  }
                />
                <text
                  x={point[0] > 250 ? -15 : 15}
                  textAnchor={point[0] > 250 ? "end" : "start"}
                  y="-4"
                >
                  {f.properties.name}
                </text>
                <text
                  x={point[0] > 250 ? -15 : 15}
                  textAnchor={point[0] > 250 ? "end" : "start"}
                  y="12"
                >
                  {group.received} / {group.total}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      <figcaption>
        Country-level locations; region details are in the roster.
      </figcaption>
    </figure>
  );
}
