# ACAPS API cache (fetched 7 Nov 2026 with a registered token; ACAPS terms of use apply)

Base `https://api.acaps.org/api/v1/`; auth `POST token-auth/ {username, password}` -> `{"token"}`; header `Authorization: Token <t>`;
pages of 25 with `next`; one request per second.

| File | Endpoint | Notes |
| --- | --- | --- |
| risk-list.json | risk-list/ | 214 published risks, 21 fields; last update Jul 2025; no R1000+ ids. Filters: status, iso3, country, ordering |
| crises.json | crises/ | 388 crises: name, drivers, adm1_name, connected_crises, active |
| countries.json | countries/ | 248 countries: crises list, overview text |
| inform-severity-index-<Mon2026>.json | inform-severity-index/<MonYYYY>/ | monthly severity per crisis (index, category, Human Impact, Conditions, People in need, Reliability, Last updated). Nov2026 is current; editions exist back to at least Nov 2024 |
| inform-severity-index-TCD-history.json | 23 monthly editions filtered iso3=TCD | TCD005 jumps 6.1 (Mar 2026) -> 6.9 (Apr 2026), largest move of 123 crises that month |
| humanitarian-access-Nov2026.json | humanitarian-access/<MonYYYY>/ | access score and sub-indicators per crisis |

The engine reads these when ACAPS_API_TOKEN is unset, so the whole demo runs offline. With a token it fetches live and
updates the cache.
