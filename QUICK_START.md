# Quick Start Guide - FactCheck AI

Get FactCheck AI running in 5 minutes!

## ⚡ Super Quick Start

### Step 1: Clone & Setup (1 minute)
```bash
cd factcheck-ai

# Linux/Mac
chmod +x setup.sh
./setup.sh

# Windows
setup.bat
```

### Step 2: Configure API Keys (1 minute)
```bash
# Edit .env file
nano .env

# Add these lines:
OPENAI_API_KEY=sk-your-key-here
TAVILY_API_KEY=tvly-your-key-here
```

### Step 3: Run App (30 seconds)
```bash
streamlit run app.py
```

### Step 4: Use App (2 minutes)
1. Open http://localhost:8501
2. Upload a PDF using the sidebar
3. Click "Extract Claims"
4. Click "Begin Verification"
5. Download your report!

---

## 🔑 Get API Keys (2 minutes)

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy and paste in `.env` → `OPENAI_API_KEY`

### Tavily Search API Key
1. Go to https://www.tavily.com
2. Sign up (free!)
3. Copy API key from dashboard
4. Paste in `.env` → `TAVILY_API_KEY`

---

## 🐳 Using Docker (Even Faster!)

```bash
# Copy .env.example to .env and add API keys first!

# Then run:
docker-compose up --build

# Access at http://localhost:8501
```

---

## ✅ Verify Installation

```bash
# Check Python
python --version  # Should be 3.10+

# Check dependencies installed
pip list | grep streamlit

# Test import
python -c "import streamlit; print('✅ OK')"
```

---

## 🐛 Common Issues

**Issue: "command not found: streamlit"**
- Solution: Activate virtual environment: `source venv/bin/activate`

**Issue: "API keys not configured"**
- Solution: Edit `.env` and add your keys, don't forget to save!

**Issue: Port 8501 already in use**
- Solution: `streamlit run app.py --server.port 8502`

**Issue: PDF extraction fails**
- Solution: Ensure PDF is not scanned image, has actual text

---

## 📊 Features Overview

| Feature | Status |
|---------|--------|
| PDF Upload | ✅ Working |
| Claim Extraction | ✅ Working |
| Web Search | ✅ Working |
| Verification | ✅ Working |
| Reports | ✅ Working |
| Export CSV | ✅ Working |
| Export Markdown | ✅ Working |

---

## 🚀 Next: Deploy to Cloud

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Streamlit Cloud (easiest)
- Docker deployment
- AWS, Heroku options

---

**That's it! You're ready to fact-check PDFs! 🎉**
