# FactCheck AI - Troubleshooting & FAQ

## 🔧 Common Issues & Solutions

### Installation Issues

#### Problem: "Python version too old"
```
Error: Python 3.10+ required, you have 3.8
```
**Solution:**
1. Download Python 3.10+ from python.org
2. Install and add to PATH
3. Verify: `python --version`

---

#### Problem: "pip: command not found"
```
Error: pip is not installed
```
**Solution:**
```bash
python -m pip install --upgrade pip
# Or reinstall Python with pip selected
```

---

#### Problem: "Permission denied" on setup.sh
```
Error: Permission denied: './setup.sh'
```
**Solution:**
```bash
chmod +x setup.sh
./setup.sh
```

---

### Configuration Issues

#### Problem: "API keys not configured"
```
Error: API keys not configured. Please set OPENAI_API_KEY and TAVILY_API_KEY
```
**Solution:**
1. Copy `.env.example` to `.env`
2. Edit `.env` with your keys:
   ```
   OPENAI_API_KEY=sk-...
   TAVILY_API_KEY=tvly-...
   ```
3. Save and restart the app
4. Verify: `grep -c OPENAI_API_KEY .env`

---

#### Problem: "Invalid API key"
```
Error: Incorrect API key provided
```
**Solution:**
1. Verify key from OpenAI dashboard: https://platform.openai.com/api-keys
2. Check for extra spaces in `.env`
3. Ensure key hasn't been revoked
4. Try creating a new key

---

#### Problem: "API quota exceeded"
```
Error: Rate limited by OpenAI
```
**Solution:**
- Check usage: https://platform.openai.com/usage
- Wait 1-2 minutes before retrying
- Upgrade your API plan for higher limits
- Implement request batching

---

### PDF Processing Issues

#### Problem: "File size exceeds limit"
```
Error: File size exceeds 25 MB limit
```
**Solution:**
- Compress PDF using: https://www.ilovepdf.com/compress_pdf
- Split large PDF into smaller files
- Remove images/embedded media
- Contact admin to increase limit

---

#### Problem: "Failed to extract text"
```
Error: Failed to extract text from PDF. Please ensure it's a valid PDF file.
```
**Causes & Solutions:**
1. **Scanned image PDF** → Convert using OCR
2. **Corrupted PDF** → Try opening in Acrobat Reader first
3. **Encrypted PDF** → Remove password protection
4. **Very old PDF** → Try newer PDF reader format

**Test extraction:**
```bash
python -c "
from services.pdf_parser import PDFParser
# Try extracting with test file
"
```

---

#### Problem: "No text extracted"
```
Empty or very few claims extracted
```
**Solution:**
- Ensure PDF has actual text (not images)
- Check that PDF opens in reader
- Try different PDF or sample document
- Enable debug mode to see raw extracted text

---

### Claim Extraction Issues

#### Problem: "No claims found"
```
Warning: No factual claims found in the document.
```
**Causes & Solutions:**
1. **Too little text** → PDF must have 100+ words
2. **No statistics** → Document lacks numerical claims
3. **Wrong format** → Try different PDF type
4. **LLM not focused** → Check prompt in constants.py

---

#### Problem: "Claims too short/long"
```
Some claims filtered out as invalid
```
**Solution:**
- Adjust length limits in `utils/constants.py`
- `CLAIM_MIN_LENGTH = 10`
- `CLAIM_MAX_LENGTH = 500`

---

#### Problem: "Too many duplicate claims"
```
Many identical claims after extraction
```
**Solution:**
- Enable "Remove duplicate claims" checkbox
- Adjust similarity threshold in `remove_duplicate_claims()`
- Check PDF for repeated sections

---

### Verification Issues

#### Problem: "Verification very slow"
```
Processing taking 5-10 minutes for 20 claims
```
**Causes & Solutions:**
1. **API latency** → Check Tavily/OpenAI status
2. **Network slow** → Check internet connection
3. **Too many claims** → Extract fewer claims
4. **Low confidence threshold** → Increase threshold

**Optimization:**
```python
# In app.py, adjust:
min_confidence = st.slider(..., value=70)  # Higher threshold
```

---

#### Problem: "Verification failed"
```
Error: Verification process failed. Please try again.
```
**Debug steps:**
1. Check internet connection
2. Verify API keys are valid
3. Check API status pages
4. Try with simpler claim
5. Check logs: `streamlit run app.py --logger.level=debug`

---

#### Problem: "Low confidence scores"
```
All results show 0-20% confidence
```
**Solution:**
- Evidence may not clearly match claims
- Try with more specific/common claims
- Check if search results are relevant
- Adjust confidence calculation in verifier.py

---

#### Problem: "Wrong verification status"
```
Claim marked as "False" but should be "Verified"
```
**Solution:**
- Search results may not contain evidence
- Try with different claim phrasing
- Check web for authoritative source
- Adjust LLM prompt in constants.py for better reasoning

---

### Web Search Issues

#### Problem: "No search results"
```
Error: No search results found.
```
**Solution:**
1. Claim too vague → Try more specific claim
2. Claim too new → May not be indexed yet
3. API rate limited → Wait and retry
4. API key invalid → Verify Tavily API key

---

#### Problem: "Search timeout"
```
Error: Search request timed out.
```
**Solution:**
```bash
# Check internet connection
ping 8.8.8.8

# Check if Tavily is down
# Visit: https://status.tavily.com

# Retry with longer timeout:
# Adjust VERIFICATION_TIMEOUT in constants.py
```

---

#### Problem: "Wrong search results"
```
Results not relevant to claim
```
**Solution:**
- Improve claim phrasing in extraction prompt
- Add more context to search query
- Use more specific search terms
- Manually adjust search query format in search_service.py

---

### Report Generation Issues

#### Problem: "CSV download fails"
```
Error downloading CSV report
```
**Solution:**
1. Check if results exist (run verification first)
2. Verify file permissions
3. Try different browser
4. Check disk space
5. Try direct file access

---

#### Problem: "Markdown formatting wrong"
```
Report doesn't look correct
```
**Solution:**
- Check markdown in text editor (not Word)
- Verify character encoding is UTF-8
- Open in markdown viewer
- Check report_generator.py for formatting

---

### UI/Display Issues

#### Problem: "Streamlit not responding"
```
App freezes or becomes unresponsive
```
**Solution:**
```bash
# Kill and restart
ps aux | grep streamlit
kill -9 <PID>

# Or with different port
streamlit run app.py --server.port 8502
```

---

#### Problem: "Pages not loading"
```
Some tabs or sections not visible
```
**Solution:**
- Clear browser cache: Ctrl+Shift+Delete
- Use private/incognito window
- Try different browser
- Check browser console for errors (F12)

---

#### Problem: "Upload button not responding"
```
File picker not working
```
**Solution:**
```bash
# Recreate .streamlit directory
rm -rf .streamlit
mkdir -p .streamlit
cp .streamlit/config.toml.backup .streamlit/config.toml
streamlit run app.py
```

---

### Deployment Issues

#### Problem: "Docker build fails"
```
Error building Docker image
```
**Solution:**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild with verbose output
docker-compose up --build --verbose

# Check logs
docker-compose logs -f
```

---

#### Problem: "Port 8501 already in use"
```
Error: Address already in use
```
**Solution:**
```bash
# Find process using port
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different port
streamlit run app.py --server.port 8502
```

---

#### Problem: "Streamlit Cloud deployment fails"
```
Error during deployment
```
**Solution:**
1. Check requirements.txt is correct
2. Verify all imports work locally
3. Check for .env file (should only be .env.example)
4. Verify secrets configured in dashboard
5. Check build logs in Streamlit Cloud

---

## ❓ FAQ

### Q: How much does it cost to run?
**A:** 
- Streamlit Cloud: Free ($7/month for premium)
- OpenAI API: ~$0.01-0.05 per claim
- Tavily Search: Free-$10/month depending on usage
- **Typical:** $20-100/month for small usage

### Q: Can I use this offline?
**A:** No, requires internet for:
- OpenAI API calls
- Tavily web search
- Streamlit Cloud (if deployed there)

### Q: What's the maximum document size?
**A:** 25 MB per file, but practically 5-10 MB for reasonable processing time.

### Q: Can I verify claims in other languages?
**A:** Yes! GPT-4o-mini supports 100+ languages. Extract and verify works in any language with PDF text.

### Q: How accurate is the verification?
**A:** ~70-90% confidence on average. Depends on:
- Claim clarity
- Availability of web sources
- LLM reasoning quality
- Search result relevance

### Q: Can I batch process multiple PDFs?
**A:** Not in current UI, but can modify code to:
1. Loop through files
2. Process each
3. Combine results
4. See DEPLOYMENT.md for async processing

### Q: How do I reduce costs?
**A:** 
1. Use gpt-4o-mini instead of gpt-4
2. Increase confidence threshold (fewer verifications)
3. Batch similar claims
4. Use Tavily's free tier

### Q: Can I use a different LLM?
**A:** Yes! Modify `LLM_MODEL` in constants.py to:
- `gpt-4` (more accurate, more expensive)
- Could integrate Claude or other LLMs

### Q: Is my data secure?
**A:** 
- No local persistence
- Data sent to OpenAI/Tavily APIs only
- Clear .env file with secrets
- HTTPS for all connections

### Q: Can I customize the UI?
**A:** Yes! Modify app.py:
- Colors in CSS styling
- Button labels and positions
- Report formats
- Verification statuses

### Q: How do I add more claim types?
**A:** 
1. Add to CLAIM_TYPES in constants.py
2. Update CLAIM_EXTRACTION_PROMPT
3. Modify report generation if needed

### Q: Can I integrate with a database?
**A:** Yes! Add to services/:
1. Create database_service.py
2. Store results in PostgreSQL/MongoDB
3. Add history/analytics features

---

## 🚀 Performance Tips

### Faster Processing
1. Increase confidence threshold (skip low-confidence)
2. Limit claims to top 20 most important
3. Use local caching for repeated searches
4. Implement parallel processing

### Lower Costs
1. Use cheaper LLM model
2. Reduce search results per claim (5 → 3)
3. Filter claims before verification
4. Batch similar claims

### Better Accuracy
1. Improve extraction prompt
2. Use GPT-4 instead of GPT-4o-mini
3. Add source quality scoring
4. Implement fact-checking database integration

---

## 📞 Getting Help

### Before Contacting Support

1. **Check this document** - Most issues covered here
2. **Check logs** - Run with debug mode: `--logger.level=debug`
3. **Search GitHub Issues** - Your problem likely solved
4. **Test locally** - Rule out environment issues

### Support Channels

- **GitHub Issues:** https://github.com/yourusername/factcheck-ai/issues
- **Streamlit Community:** https://discuss.streamlit.io
- **OpenAI Support:** https://help.openai.com
- **Tavily Support:** https://www.tavily.com/support

---

## 📝 Reporting Bugs

Include:
1. Error message (exact copy)
2. Steps to reproduce
3. Your environment (OS, Python version)
4. `.env` redacted (with API keys removed)
5. Full stack trace if available

Example:
```
OS: Ubuntu 22.04
Python: 3.10.5
Error: PDF extraction failed
Steps:
1. Upload marketing_report.pdf
2. Click Extract Claims
3. Error appears

Stack trace:
[Full error message here]
```

---

**Still stuck? Create an issue with full details and we'll help!** 🎉
