# FactCheck AI - Architecture Guide

## 🏗️ System Architecture

### High-Level Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        User Interface Layer                  │
│                       (Streamlit Web UI)                     │
│  - File Upload  - Claim Display  - Report Export             │
└────────┬─────────────────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌─────────────────┐  ┌──────────────────┐                  │
│  │   PDF Parser    │  │ Claim Extractor  │                  │
│  └────────┬────────┘  └──────────┬───────┘                  │
│           │                      │                          │
│  ┌────────▼──────────────────────▼────────────┐             │
│  │          Verifier (Orchestrator)           │             │
│  │  - Coordinates workflow                    │             │
│  │  - Manages state                           │             │
│  │  - Handles errors                          │             │
│  └────────┬─────────────────────────────────┬─┘             │
│           │                                 │               │
│           ▼                                 ▼               │
│  ┌─────────────────┐  ┌──────────────────┐                │
│  │ Report Generator│  │ Error Handler    │                │
│  └─────────────────┘  └──────────────────┘                │
└────────┬─────────────────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────┐
│                    External API Layer                        │
│  ┌──────────────┐  ┌────────────────────────────────────┐   │
│  │ OpenAI API   │  │ Tavily Search API                  │   │
│  │ - GPT-4o-min │  │ - Web Search Results              │   │
│  │ - Claim      │  │ - Source Attribution              │   │
│  │ - Verification│ │ - Evidence Snippets               │   │
│  └──────────────┘  └────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Dependencies

```
app.py (Main)
├── services.verifier
│   ├── services.llm_service
│   │   └── utils.constants
│   └── services.search_service
│       └── utils.constants
├── services.claim_extractor
│   ├── services.llm_service
│   └── utils.helpers
├── services.pdf_parser
│   └── utils.helpers
├── services.report_generator
│   └── utils.helpers
└── utils.helpers
```

---

## 🔄 Claim Verification Workflow

### Step 1: PDF Input
```
User uploads PDF file
    ↓
Validation (size, type, format)
    ↓
File accepted or error returned
```

**Code Location:** `app.py`, line ~170

### Step 2: Text Extraction
```
PDF bytes received
    ↓
Try pdfplumber extraction
    ↓
If insufficient text, try PyPDF2
    ↓
Sanitize and normalize
    ↓
Return extracted text
```

**Code Location:** `services/pdf_parser.py`

### Step 3: Claim Identification
```
Extracted text (max 8000 chars per call)
    ↓
Send to GPT-4o-mini with extraction prompt
    ↓
Parse JSON response
    ↓
Validate claims (length, format, duplicates)
    ↓
Return list of claims with types
```

**Code Location:** `services/claim_extractor.py`, `services/llm_service.py`

### Step 4: Web Search
```
For each claim:
    ↓
Format search query: "Verify: {claim}"
    ↓
Send to Tavily Search API
    ↓
Extract top 5 results
    ↓
Compile evidence snippets
    ↓
Return combined evidence text
```

**Code Location:** `services/search_service.py`

### Step 5: LLM Verification
```
Claim + Evidence (max 4000 chars)
    ↓
Send to GPT-4o-mini with verification prompt
    ↓
LLM analyzes: Does evidence support claim?
    ↓
Return: Status + Confidence + Explanation
    ↓
Validate response (0-100 confidence)
    ↓
Return verification result
```

**Code Location:** `services/verifier.py`, `services/llm_service.py`

### Step 6: Report Generation
```
Collect all verification results
    ↓
Calculate statistics
    ↓
Format for export (CSV or Markdown)
    ↓
User downloads report
```

**Code Location:** `services/report_generator.py`

---

## 🎯 Data Structures

### Claim Object
```python
{
    "claim": str,          # The factual claim
    "type": str            # Category (Market Statistic, etc.)
}
```

### Verification Result
```python
{
    "claim": str,                    # Original claim
    "type": str,                     # Claim type
    "status": str,                   # Verified/Inaccurate/False/Unverifiable
    "confidence": int,               # 0-100
    "explanation": str,              # Why this status
    "evidence_snippet": str,         # Preview of evidence
    "sources": [                     # Attribution
        {
            "title": str,
            "url": str
        }
    ]
}
```

### Search Result
```python
{
    "title": str,          # Page title
    "url": str,            # Source URL
    "content": str         # Text snippet
}
```

---

## 🔐 Error Handling Strategy

### File Upload Errors
```python
if file_size > MAX_PDF_SIZE:
    return error  # Handled in helpers.validate_pdf_file()
if file_type != "pdf":
    return error  # Type validation
```

### API Errors
```python
try:
    response = api_call()
except RateLimitError:
    return default_response with message
except APIError:
    return default_response with message
except Exception:
    return default_response with generic message
```

### Extraction Errors
```python
# If pdfplumber fails, try PyPDF2
# If both fail, return error message
# If result too small, also try other method
```

---

## 🚀 Performance Optimization

### 1. Text Chunking
- Large documents split into 5000-word chunks
- Process up to 3 chunks per document
- Prevents hitting token limits

**Location:** `services/claim_extractor.py:_chunk_text()`

### 2. Duplicate Detection
- Normalize claim text (lowercase, punctuation)
- Use set for O(1) lookups
- Remove ~20-30% of duplicate claims

**Location:** `utils/helpers.py:remove_duplicate_claims()`

### 3. API Call Optimization
- Batch web searches where possible
- Reuse search results across multiple claims
- Cache search queries

**Location:** `services/search_service.py`

### 4. Progress Feedback
- Show progress bar during processing
- Update status after each claim
- Improve UX for long operations

**Location:** `app.py:~280-320`

---

## 💾 State Management

### Session State Variables
```python
st.session_state:
    - extracted_text        # Raw text from PDF
    - extracted_claims      # List of identified claims
    - verification_results  # List of verification results
    - processing            # Boolean flag for UI state
```

**Location:** `app.py:initialize_session_state()`

### No Database
- Stateless processing (no persistence)
- Each session independent
- Results stored in session state only
- Users download reports manually

---

## 🔌 API Integration

### OpenAI Configuration
```python
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini"  # Can change to "gpt-4"
temperature = 0.3       # Low randomness for consistency
```

**Location:** `services/llm_service.py:__init__`

### Tavily Search Configuration
```python
payload = {
    "api_key": api_key,
    "query": search_query,
    "max_results": 5,
    "include_answer": True
}
```

**Location:** `services/search_service.py:search()`

---

## 📊 Configuration System

### Constants Hierarchy
```
utils/constants.py
├── File Limits (MAX_PDF_SIZE_MB)
├── API Settings (SEARCH_RESULTS_COUNT)
├── LLM Settings (MODEL, TEMPERATURE)
├── Verification Statuses (VERIFIED, INACCURATE, FALSE)
├── Error Messages
├── Prompt Templates
└── Display Configuration (STATUS_COLORS)
```

### Environment Variables
```
.env
├── OPENAI_API_KEY     (Required)
├── TAVILY_API_KEY     (Required)
├── LLM_MODEL          (Optional, default: gpt-4o-mini)
└── LOG_LEVEL          (Optional, default: INFO)
```

---

## 🧪 Testing Strategy

### Unit Test Areas
```
1. PDF Parser
   - Valid PDF extraction
   - Invalid PDF handling
   - Large file handling

2. Claim Extraction
   - JSON parsing
   - Duplicate detection
   - Text cleaning

3. Search Service
   - Query formatting
   - Result parsing
   - Error handling

4. Verification
   - Status classification
   - Confidence scoring
   - Source attribution

5. Report Generator
   - CSV formatting
   - Markdown generation
   - Statistics calculation
```

### Integration Tests
```
1. End-to-end workflow
2. API rate limiting
3. Timeout handling
4. Error recovery
```

---

## 🚀 Scaling Considerations

### Current Limitations
- Single instance (one user at a time in Streamlit)
- No database (stateless)
- Limited to API rate limits
- Processing memory bounded

### Scaling Strategies

**Horizontal Scaling:**
- Deploy multiple instances behind load balancer
- Use shared database for results
- Implement session management

**Vertical Scaling:**
- Increase instance memory
- Optimize code for speed
- Add caching layer (Redis)

**Asynchronous Processing:**
- Use Celery + RabbitMQ for task queue
- Process claims in background
- Notify user when complete

---

## 📈 Monitoring & Observability

### Key Metrics
```
1. Claim extraction success rate
2. Verification success rate
3. Average processing time per claim
4. API error rates
5. User engagement
```

### Logging
```python
# Add to each module for production
logger = logging.getLogger(__name__)
logger.info("Processing claim...")
logger.error("API Error:", exc_info=True)
```

### Error Tracking
- Sentry integration (recommended)
- CloudWatch logs (AWS)
- Application Insights (Azure)

---

## 🔒 Security Architecture

### Data Flows
```
User Input
    ↓ (Validated)
Processing Layer
    ↓ (Sanitized)
External APIs
    ↓ (HTTPS only)
Response
    ↓ (No persistence)
User Display
    ↓ (Downloaded/Deleted)
```

### API Key Security
- Never logged or displayed
- Stored only in .env (local) or secrets (cloud)
- Rotated regularly
- Monitored for unusual usage

---

## 📝 Code Organization Principles

1. **Single Responsibility**
   - Each module has one purpose
   - PDFParser only parses PDFs
   - LLMService only calls OpenAI

2. **Dependency Injection**
   - Services receive dependencies in __init__
   - Easy to mock for testing

3. **Error Propagation**
   - Errors bubble up with context
   - Graceful degradation where possible

4. **Configuration Externalization**
   - All constants in constants.py
   - Environment variables for secrets
   - No hardcoded values

---

## 🎓 Learning Resources

### For Developers
- [Streamlit Documentation](https://docs.streamlit.io)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [Tavily Search Docs](https://www.tavily.com/docs)
- [Python Best Practices](https://pep8.org)

### For Operators
- [Docker Documentation](https://docs.docker.com)
- [Streamlit Cloud Guide](https://docs.streamlit.io/deploy/streamlit-cloud)
- [AWS Deployment](https://aws.amazon.com)

---

## 🔄 Development Workflow

### Adding New Feature
1. Add constants to `utils/constants.py`
2. Create service module or update existing
3. Add utility functions to `utils/helpers.py`
4. Update `app.py` UI
5. Test locally with `streamlit run app.py`
6. Push to GitHub and deploy

### Modifying Verification Logic
1. Update prompt in `constants.py`
2. Adjust verification in `services/verifier.py`
3. Update result handling in `app.py`
4. Test with sample PDFs
5. Deploy to production

---

This architecture prioritizes:
✅ Simplicity - Easy to understand
✅ Maintainability - Clear separation of concerns
✅ Scalability - Can grow with demand
✅ Reliability - Comprehensive error handling
✅ Security - API keys protected, data validated
