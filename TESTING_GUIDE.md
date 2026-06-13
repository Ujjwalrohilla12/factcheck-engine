# FactCheck AI - Quick Start Guide for Testing Fixed Version

## What Was Fixed

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| **Claim Extraction Error: 'claims'** | `payload.get()` called on non-dict | Added defensive type checking |
| **Extracted Claims Show Nothing** | Errors not visible in UI | Added logging + error messages |
| **Verification Report Not Generated** | Session state not updated properly | Enhanced error handling + logging |
| **Download Button Doesn't Work** | Report generation errors hidden | Added error display for each format |

## Prerequisites

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Set environment variables
# .env file should contain:
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
LLM_MODEL=gpt-4o-mini
```

## Running the Fixed Application

### Option 1: Local Terminal
```bash
# Navigate to project directory
cd factcheck-ai

# Run Streamlit app
streamlit run app.py

# View logs in the terminal output
```

### Option 2: With Debug Logging
```bash
# Run with detailed logging
streamlit run app.py --logger.level=debug

# You'll see all logger.debug() calls in the console
```

## Complete Workflow Test

### Step 1: Upload PDF
1. Go to "PDF Upload" tab
2. Click "Choose a PDF document"
3. Select a test PDF (try [example.pdf from assets/](./assets/))
4. Verify file details show:
   - File size
   - Number of pages
   - Extracted characters

✅ **Check logs for:**
```
INFO - Starting claim extraction for file: example.pdf
DEBUG - Text split into X chunks
INFO - Successfully extracted XXXX characters from PDF
```

### Step 2: Extract Claims
1. Click "Extract Text and Claims" button
2. Watch progress bar update
3. Wait for success message

✅ **Expected result:**
```
✓ Extracted 15 factual claims.
```

✅ **Check logs for:**
```
INFO - Starting claim extraction from XXXXX characters
INFO - Total claims extracted: 20
INFO - After cleaning: 18 claims
INFO - After deduplication: 15 claims
INFO - Returning 15 claims (max 40)
```

### Step 3: View Claims
1. Go to "Extracted Claims" tab
2. Verify claims table shows all extracted claims
3. Each claim shows Type and Status

✅ **Expected:**
- Claim column: full claim text
- Type column: Market Statistic, Revenue, Date, etc.
- Status column: "Pending" (before verification)

### Step 4: Run Verification
1. In "Extracted Claims" tab, click "Begin Verification"
2. Watch progress bar (should show 0% → 100%)
3. Wait for verification complete message

✅ **Expected result:**
```
✓ Verified 14 claims.
```

✅ **Check logs for:**
```
INFO - Starting verification of 15 claims with min_confidence=0%
DEBUG - Verifying claim 1/15: ...
DEBUG - Evidence found (1256 chars), calling LLM for verification...
DEBUG - Verification complete: status=Verified, confidence=85%
INFO - Verification complete: 14 claims passed filters
```

### Step 5: View Verification Report
1. Go to "Verification Report" tab
2. Verify metrics show:
   - Total claims
   - Verified count
   - Inaccurate count
   - False count
   - Average confidence

✅ **Expected:**
- Expandable items for each claim
- Color coding (green=verified, orange=inaccurate, red=false, gray=unverifiable)
- Sources listed with links
- Evidence snippet available

### Step 6: Download Report
1. Go to "Download Report" tab
2. Click "Download CSV"
3. Click "Download PDF"
4. Click "Download Markdown"

✅ **Expected:**
- All three buttons work
- Files download successfully
- No error messages shown

✅ **Check logs for:**
```
INFO - Generating CSV report for 14 results
INFO - CSV report generated (2048 bytes)
INFO - Generating PDF report for 14 results
INFO - PDF report generated (45230 bytes)
```

## Testing Error Scenarios

### Test 1: Invalid PDF
1. Try uploading a text file (.txt)
2. Should see error: "Please upload a valid PDF file."

✅ **Check logs:**
```
ERROR - PDF validation failed: Please upload a valid PDF file.
```

### Test 2: PDF Too Large
1. Try uploading PDF > 25MB
2. Should see error: "File size exceeds the 25 MB limit."

✅ **Check logs:**
```
ERROR - PDF validation failed: File size exceeds the 25 MB limit.
```

### Test 3: No Extractable Text
1. Try uploading a scanned PDF (image only)
2. Should see error: "No extractable text was found..."

✅ **Check logs:**
```
ERROR - PDF parsing error: No extractable text was found...
```

### Test 4: Skip Claims During Extraction
1. Upload PDF
2. Don't click "Extract Text and Claims"
3. Go to "Extracted Claims" tab
4. Should see: "Claims will appear here after extraction."

### Test 5: Skip Verification
1. Extract claims successfully
2. Go directly to "Verification Report" tab
3. Should see: "Verification results will appear here."

### Test 6: No Claims After Verification
1. Extract claims
2. Lower "Minimum confidence to show" to 0% in sidebar
3. Run verification with high threshold
4. Should show claims that passed confidence filter

## Monitoring Logs

### Where Logs Appear

**Option 1: Streamlit Terminal**
```
2024-06-12 10:15:30,123 - app - INFO - Starting claim extraction for file: example.pdf
2024-06-12 10:15:31,456 - llm_service - DEBUG - Extracting claims from 5000 characters of text
```

**Option 2: Streamlit Output Area**
- Some INFO level logs may appear in Streamlit console
- All exception logs will be shown in Streamlit error messages

### Key Log Levels

- **DEBUG**: Detailed information for debugging (e.g., chunk processing)
- **INFO**: General informational messages (e.g., "Successfully extracted X claims")
- **WARNING**: Warning messages (e.g., "Invalid status, defaulting to...")
- **ERROR**: Error conditions (e.g., "PDF parsing error")
- **EXCEPTION**: Errors with full stack trace

## Performance Benchmarks

- **PDF Parsing**: < 2 seconds for average document
- **Claim Extraction**: ~1 second per chunk (average 5-8 chunks per PDF)
- **Verification**: ~2-3 seconds per claim (network dependent)
- **Total Flow**: 5-30 minutes depending on document size

## Common Issues & Solutions

### Issue: "Claim extraction error: 'claims'"
- ❌ **BEFORE FIX**: App would crash
- ✅ **AFTER FIX**: Shows proper error message + logged details

### Issue: Download button disabled with no message
- ❌ **BEFORE FIX**: No feedback to user
- ✅ **AFTER FIX**: Error message shown in red below button

### Issue: Report generation fails silently
- ❌ **BEFORE FIX**: No visibility into what went wrong
- ✅ **AFTER FIX**: Error logged + shown to user

### Issue: Verification shows wrong count
- ❌ **BEFORE FIX**: Difficult to debug
- ✅ **AFTER FIX**: Logs show filtering logic

## Advanced Testing

### Test with Different Models
1. In sidebar, change "Model" dropdown
2. Try: gpt-4o-mini (fast, cheap), gpt-4o (better quality)
3. Observe performance difference

### Test Duplicate Removal
1. Upload PDF with repeated statistics
2. Toggle "Remove duplicate claims" off
3. Notice increased claim count
4. Toggle back on
5. Notice decreased count

### Test Confidence Threshold
1. After verification, go to "Extracted Claims" tab
2. Change "Minimum confidence to show" slider
3. Re-run verification (click "Begin Verification" again)
4. Notice different number of results

## Success Criteria Checklist

- [ ] PDF uploads without error
- [ ] Claims extract successfully
- [ ] All extracted claims visible in table
- [ ] Verification runs to completion
- [ ] Report shows statistics (verified, inaccurate, false, unverifiable)
- [ ] Each claim shows status, confidence, explanation
- [ ] Sources are clickable links
- [ ] CSV download works
- [ ] PDF download works
- [ ] Markdown download works
- [ ] Logs show complete pipeline
- [ ] Error messages are helpful and specific
- [ ] No crashes or unhandled exceptions

## Debugging Tips

1. **Enable Debug Mode**
   ```bash
   streamlit run app.py --logger.level=debug
   ```

2. **Check Console Output**
   - Open browser developer tools (F12)
   - Look at Console tab for any JavaScript errors

3. **Monitor Logs**
   - Keep terminal visible while running tests
   - Search for "ERROR" or "WARNING" messages

4. **Use Print Statements**
   ```python
   # In any service, you can add:
   print(f"DEBUG: claims = {claims}")  # Shows up in Streamlit console
   logger.debug(f"DEBUG: claims = {claims}")  # Shows up in terminal
   ```

5. **Test with Minimal PDF**
   - Create a test PDF with just 2-3 facts
   - Easier to trace through logs
   - Faster to debug

## Support

For issues:
1. Check [BUGFIX_CHANGELOG.md](./BUGFIX_CHANGELOG.md) for comprehensive changes
2. Check [CORRECTED_CODE_SUMMARY.md](./CORRECTED_CODE_SUMMARY.md) for code examples
3. Review logs in terminal for specific errors
4. Ensure all required packages installed: `pip install -r requirements.txt`
5. Verify API keys are set correctly in .env file
