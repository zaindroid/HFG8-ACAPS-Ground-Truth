import { useId, useMemo, useState, useEffect } from "react";
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
const projection = geoMercator()
  .scale(400 / (2 * Math.PI))
  .translate([200, 125]);
const path = geoPath(projection);
const worldPaths = world.features.map((country) => ({
  country,
  outline: path(country) || undefined,
}));
type Camera = { x: number; y: number; scale: number };
const worldView: Camera = { x: 0, y: 0, scale: 1 };

function useMapCamera(target: Camera) {
  const [camera, setCamera] = useState(worldView);
  useEffect(() => {
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0;
    const start = performance.now();
    // Functional state reads the current pose if another location arrives mid-move.
    let origin: Camera | undefined;
    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / 450);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCamera((current) => {
        origin ??= current;
        return {
          x: origin.x + (target.x - origin.x) * eased,
          y: origin.y + (target.y - origin.y) * eased,
          scale: origin.scale + (target.scale - origin.scale) * eased,
        };
      });
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    const finish = () => {
      cancelAnimationFrame(frame);
      setCamera(target);
    };
    const changed = () => {
      if (motion.matches) finish();
    };
    if (motion.matches) finish();
    else frame = requestAnimationFrame(tick);
    motion.addEventListener("change", changed);
    return () => {
      cancelAnimationFrame(frame);
      motion.removeEventListener("change", changed);
    };
  }, [target.x, target.y, target.scale]);
  return camera;
}
export function ExpertMap({
  experts,
  arrived,
}: {
  experts: Match["experts"];
  arrived?: number;
}) {
  const id = useId();
  const groups = useMemo(() => {
    const locations = new Map<string, number>();
    (arrived === undefined
      ? experts
      : experts.slice(0, Math.max(0, arrived))
    ).forEach((e) => {
      const name = world.features.some((f) => f.properties.name === e.region)
        ? e.region!
        : names[e.geo_tags[0]];
      if (!name) return;
      locations.set(name, (locations.get(name) || 0) + 1);
    });
    return locations;
  }, [experts, arrived]);
  const selected = useMemo(
    () => world.features.filter((f) => groups.has(f.properties.name)),
    [groups],
  );
  const target = useMemo(() => {
    if (!selected.length) return worldView;
    const [[left, top], [right, bottom]] = path.bounds({
      type: "FeatureCollection",
      features: selected,
    });
    const scale = Math.max(
      1,
      Math.min(
        4.5,
        300 / Math.max(1, right - left),
        155 / Math.max(1, bottom - top),
      ),
    );
    return {
      scale,
      x: 200 - ((left + right) / 2) * scale,
      y: 118 - ((top + bottom) / 2) * scale,
    };
  }, [selected]);
  const camera = useMapCamera(target);
  return (
    <figure className="expert-map">
      <svg
        viewBox="0 0 400 245"
        role="img"
        aria-label={
          groups.size
            ? `Panel location map. ${[...groups].map(([name, count]) => `${name}: ${count} experts${arrived === undefined ? " selected" : " received"}`).join(". ")}`
            : "World map. Waiting for expert responses; no locations received yet."
        }
      >
        <defs>
          <clipPath id={id}>
            <rect width="400" height="245" rx="8" />
          </clipPath>
        </defs>
        <g clipPath={`url(#${id})`}>
          <g
            className="map-viewport"
            transform={`translate(${camera.x},${camera.y}) scale(${camera.scale})`}
          >
            {worldPaths.map(({ country: f, outline }) => (
              <path
                key={f.properties.name}
                d={outline}
                vectorEffect="non-scaling-stroke"
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
              const count = groups.get(f.properties.name)!;
              return (
                <g
                  key={f.properties.name}
                  className="map-marker"
                  transform={`translate(${point[0]},${point[1]}) scale(${1 / camera.scale})`}
                >
                  <title>
                    {f.properties.name}: {count}{" "}
                    {arrived === undefined
                      ? "selected experts"
                      : "responses received"}
                  </title>
                  <circle r="9" className="map-panel-dot received" />
                  <text
                    x={point[0] * camera.scale + camera.x > 250 ? -15 : 15}
                    textAnchor={
                      point[0] * camera.scale + camera.x > 250 ? "end" : "start"
                    }
                    y="-4"
                  >
                    {f.properties.name}
                  </text>
                  <text
                    x={point[0] * camera.scale + camera.x > 250 ? -15 : 15}
                    textAnchor={
                      point[0] * camera.scale + camera.x > 250 ? "end" : "start"
                    }
                    y="12"
                  >
                    {count}{" "}
                    {arrived === undefined
                      ? "experts"
                      : count === 1
                        ? "reply"
                        : "replies"}
                  </text>
                </g>
              );
            })}
          </g>
        </g>
      </svg>
      <figcaption>
        {arrived === 0
          ? "Locations appear as responses arrive."
          : "Country-level locations; region details are in the roster."}
      </figcaption>
    </figure>
  );
}
