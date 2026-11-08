export const checkedOn = "6 November 2026";
const base = "https://www.acaps.org/en/";
export const publications = [
  {
    country: "Afghanistan",
    iso: "AFG",
    date: "2026-10-28",
    title: "Community perspectives on early flood warning and preparedness",
    theme: "Natural hazards",
    slug: "afghanistan-community-perspectives-on-early-flood-warning-and-preparedness",
  },
  {
    country: "Ukraine",
    iso: "UKR",
    date: "2026-10-15",
    title: "May–August 2026 humanitarian access update",
    theme: "Humanitarian access",
    slug: "ukraine-may-august-2026-humanitarian-access-update",
  },
  {
    country: "Democratic Republic of the Congo",
    iso: "COD",
    date: "2026-10-13",
    title: "Mpox outbreak affecting Kasaï province",
    theme: "Health",
    slug: "drc-mpox-outbreak-affecting-kasai-province",
  },
  {
    country: "Colombia",
    iso: "COL",
    date: "2026-09-25",
    title: "Earthquake’s expected humanitarian impacts",
    theme: "Natural hazards",
    slug: "colombia-earthquakes-expected-humanitarian-impacts",
  },
].map((p) => ({ ...p, url: `${base}countries/archives/detail/${p.slug}` }));
