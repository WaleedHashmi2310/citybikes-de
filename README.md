# CityBikes DE — European Bikeshare Data Pipeline

> End-to-end data engineering project for the
> [DataTalks Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp).
> Ingests real-time bikeshare station data from 6 European cities,
> transforms it in BigQuery using dbt, and visualises commute patterns
> and occupancy trends in Looker Studio.

## Live dashboard
🔗 [View on Looker Studio](#) ← *updated after Phase 4*

## Architecture
> Diagram added after Phase 5

## Tech stack

| Layer | Technology |
|---|---|
| Orchestration | Kestra |
| Ingestion | Python · Pydantic · Cloud Run Jobs |
| Historical load | PySpark · Dataproc Serverless |
| Data lake | Google Cloud Storage |
| Warehouse | BigQuery |
| Transformation | dbt Core |
| Infrastructure as Code | Terraform |
| CI/CD | GitHub Actions |
| Visualisation | Looker Studio · Power BI |
| Local development | Docker Compose · DuckDB |

## Cities covered

| City | Network ID | Stations |
|---|---|---|
| Paris, France | velib | ~1,400 |
| Barcelona, Spain | bicing | ~530 |
| London, UK | tfl-cycle-hire | ~800 |
| Berlin, Germany | nextbike-de | ~200 |
| Koblenz, Germany | nextbike-de | ~50 |

## Quick start

### Run locally (no GCP required)
```bash
git clone https://github.com/YOUR_USERNAME/citybikes-de.git
cd citybikes-de
cp .env.example .env        # edit with your values
docker compose up           # starts Kestra + PostgreSQL locally
```

### Deploy to GCP
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars  # edit with your values
terraform init
terraform plan
terraform apply
```

## Project status

- [x] Phase 0 — Repository setup and configuration
- [ ] Phase 1 — Ingestion layer (Pydantic · Cloud Run · Kestra)
- [ ] Phase 2 — PySpark historical bulk load
- [ ] Phase 3 — dbt warehouse (staging · dims · facts)
- [ ] Phase 4 — Looker Studio and Power BI dashboards
- [ ] Phase 5 — Hardening, documentation, portability test

## Repository structure
```
citybikes-de/
├── terraform/        Infrastructure as Code (GCP resources)
├── docker/           Docker Compose for local development
├── kestra/flows/     Orchestration flow definitions
├── ingestion/        Python ingestion package
├── spark/            PySpark historical bulk load script
├── dbt/              Data transformation models and tests
├── dashboards/       Power BI file and PDF exports
└── data/snapshots/   Monthly mart exports (post-GCP fallback)
```

## Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) — design decisions and trade-offs
- dbt docs — *link added after Phase 3*

## Data source
- [CityBikes API](https://api.citybik.es/v2) — live station status, no auth required
- [data.citybik.es](https://data.citybik.es) — historical Parquet archives
