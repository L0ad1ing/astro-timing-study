# data/

Not committed. The pipeline reads a cleaned extract of Astro-Databank (https://www.astro.com/astro-databank)
as a SQLite file at `data/astro_master_data.db`, or wherever the `ASTRO_SOURCE_DB` environment variable points.

Expected table `ml_features`, one row per person per event:
- `name`, `event_category`, `event_date` (ISO), `event_label` (Astro-Databank's label; `'born on'` marks the birth row),
  `birth_jd` (Julian Day, UT);
- on the birth row: `natal_<Sun|Moon|Mercury|Venus|Mars|Jupiter|Saturn|Rahu>_deg` and `natal_asc_deg` (sidereal,
  Lahiri), `birth_time_known`, `rodden_rating`, `birth_lat`, `birth_lon`.
`scripts/run_rao.py` also reads `charts.raw_html` (the raw page) for gender.

Astro-Databank's terms of use apply: the data is not redistributed here. To reproduce the study, build the extract
from Astro-Databank yourself (the parsers for its coordinate and timezone notation are in `src/preprocessing.py`).
