# Global Website Lead Generation Bot

A daily research assistant for discovering public business opportunities for AxonixIT services:
- Website development and redesign
- SEO and digital marketing
- Business automation and CRM
- E-commerce development
- Social media management

It discovers candidate businesses from public search results, checks their websites for basic opportunity signals, scores and deduplicates candidates, and exports a CSV plus a Markdown report. It does **not** contact prospects or send messages.

## Important limitations
- This is a starter MVP, not a guarantee of verified sales intent. Every result is a candidate and should be reviewed manually.
- Public search providers can rate-limit or change HTML. For reliable operation, configure a supported search API.
- Only publicly published business contact information is collected. Do not collect sensitive personal information, bypass access controls, or ignore a site's terms/robots rules.
- The repository is public. Daily lead files are generated as workflow artifacts and are **not committed** to the repository.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main --config config/settings.example.json --output-dir output
```

The default discovery adapter uses DuckDuckGo's public HTML search interface on a best-effort basis. It may be blocked or change. Set `SERPAPI_API_KEY` to use SerpAPI instead.

## GitHub Actions daily run

The workflow runs daily at 02:30 UTC (08:00 India Standard Time) and can also be started manually from the Actions tab. Add this repository secret for SerpAPI:
- `SERPAPI_API_KEY` (optional but recommended)

The workflow uploads `leads.csv` and `daily_report.md` as an artifact. It does not publish lead data to the public repository or automatically email anyone.

## Configuration

Edit `config/settings.example.json` or create your own private config file. Configure target regions, business categories, search phrases, and score thresholds. Avoid putting API keys in JSON or committing secrets.

## Output fields

The CSV includes business name, website, source URL, evidence snippets, detected opportunity signals, score, confidence, public business email/phone when clearly found, and a suggested next step. The score is a prioritization aid—not proof that the business wants to buy.

## Project structure

```
config/                  Example settings
src/lead_discovery/       Search and website inspection
src/lead_scoring/         Transparent heuristic scoring
src/deduplication/        URL/domain deduplication
src/reporting/            CSV and Markdown outputs
tests/                    Unit tests
.github/workflows/        Scheduled GitHub Actions job
```

## Responsible use
Review each lead before outreach, personalize messages, honor opt-outs, follow applicable privacy and anti-spam laws, and keep prospect data private. Never store credentials or private customer information in this repository.
