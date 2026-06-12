# FactCheck AI

Automated PDF claim verification system built with Streamlit, Python, OpenAI, LangChain-ready dependencies, Tavily Search, PyMuPDF, pdfplumber, BeautifulSoup, and Requests.

FactCheck AI lets users upload PDFs such as marketing reports, research papers, financial reports, blogs, company documents, whitepapers, and articles. The app extracts text, identifies factual claims, verifies each claim against live web evidence, classifies results, and exports a final report.

## Project Overview

The application verifies factual claims containing:

- Statistics and percentages
- Dates and timelines
- Financial numbers and revenue figures
- Market size and market share figures
- Growth rates
- Technical figures and specifications
- User counts and adoption metrics

Each claim is classified as:

- `Verified`: credible evidence directly matches the claim
- `Inaccurate`: partially correct but outdated, incomplete, or materially modified
- `False`: contradicted by credible evidence or unsupported as stated
- `Unverifiable`: insufficient evidence returned from search

## Architecture

```text
Streamlit UI
  -> PDFParser
      -> pdfplumber primary extraction
      -> PyMuPDF fallback extraction
  -> ClaimExtractor
      -> OpenAI JSON claim extraction
      -> duplicate removal and claim validation
  -> Verifier
      -> Tavily query: "Verify claim: {claim}"
      -> evidence bundle with top source snippets
      -> OpenAI JSON verification reasoning
  -> ReportGenerator
      -> CSV, Markdown, and PDF exports
```

## Project Structure

```text
factcheck-ai/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── services/
│   ├── pdf_parser.py
│   ├── claim_extractor.py
│   ├── verifier.py
│   ├── search_service.py
│   ├── report_generator.py
│   └── llm_service.py
├── utils/
│   ├── helpers.py
│   └── constants.py
├── assets/
│   └── logo.png
└── output/
```

## Installation

```bash
git clone https://github.com/your-username/factcheck-ai.git
cd factcheck-ai
python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Required:

```text
OPENAI_API_KEY=sk-your-openai-api-key
TAVILY_API_KEY=tvly-your-tavily-api-key
```

Optional:

```text
LLM_MODEL=gpt-4o-mini
SEARCH_RESULTS_COUNT=5
REQUEST_TIMEOUT_SECONDS=30
```

Never commit `.env`. It is ignored by `.gitignore`.

## Running Locally

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, usually:

```text
http://localhost:8501
```

## Workflow

1. Upload a PDF up to 25 MB.
2. Extract text with pdfplumber and PyMuPDF fallback.
3. Use OpenAI to extract factual claims as JSON.
4. Remove duplicate or near-duplicate claims.
5. Search Tavily with `Verify claim: {claim}`.
6. Compare the claim against web evidence with OpenAI.
7. Classify each claim as `Verified`, `Inaccurate`, `False`, or `Unverifiable`.
8. Export CSV, PDF, or Markdown reports.

## Streamlit UI

The app includes:

- Sidebar PDF uploader
- Verification settings
- Model selection
- Multi-page PDF support
- Progress bars
- Extracted claims table
- Expandable verification report cards
- Source links
- Confidence scores
- CSV, PDF, and Markdown downloads

## Deployment

Deploy on Streamlit Cloud:

1. Push this project to GitHub.
2. Go to https://share.streamlit.io.
3. Click **New app**.
4. Select the GitHub repository and branch.
5. Set the main file path to `app.py`.
6. Add secrets in the Streamlit Cloud app settings:

```toml
OPENAI_API_KEY = "sk-your-openai-api-key"
TAVILY_API_KEY = "tvly-your-tavily-api-key"
LLM_MODEL = "gpt-4o-mini"
```

7. Deploy the app.

After deployment, Streamlit Cloud will provide the live URL.

## Screenshots

Add screenshots after your first deployment:

- `screenshots/upload.png`
- `screenshots/claims.png`
- `screenshots/report.png`

## Security

- Uploaded files are validated by MIME type or `.pdf` extension.
- PDFs are limited to 25 MB.
- Extracted text is sanitized before LLM processing.
- API keys are loaded from `.env` locally or Streamlit secrets in production.
- Reports are generated in memory and are not persisted by default.

## Troubleshooting

Missing API keys:

```text
Missing API configuration. Set OPENAI_API_KEY and TAVILY_API_KEY.
```

Fix: add keys to `.env` locally or Streamlit Cloud secrets.

No extractable text:

```text
No extractable text was found. Scanned PDFs need OCR before upload.
```

Fix: upload a text-based PDF or run OCR before using the app.

Rate limits:

Fix: wait and retry, reduce the maximum number of claims, or use a higher API tier.

## Future Enhancements

- OCR for scanned PDFs
- Batch PDF processing
- Source credibility scoring
- Fact-checking database integrations
- Domain allowlists and blocklists
- Organization-level audit logs
- User authentication
- Background job queue for large documents
- Multi-language claim extraction
- A REST API for programmatic verification
