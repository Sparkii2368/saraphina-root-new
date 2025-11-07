# Phase 30.5 Setup Guide - AI-Powered Risk Analysis

## Quick Start (5 minutes)

### 1. Install OpenAI Package

```bash
pip install openai
```

### 2. Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### 3. Set Environment Variable

**Windows (PowerShell)**:
```powershell
$env:OPENAI_API_KEY = "sk-your-key-here"
```

**Windows (Command Prompt)**:
```cmd
set OPENAI_API_KEY=sk-your-key-here
```

**Linux/Mac**:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

**Permanent (Windows)**:
```powershell
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-your-key-here', 'User')
```

**Permanent (Linux/Mac)**:
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### 4. Verify Setup

```bash
python tests/test_ai_risk_analyzer.py
```

Expected output:
```
✅ AIRiskAnalyzer imported successfully
✅ OPENAI_API_KEY found
✅ AIRiskAnalyzer initialized with model: gpt-4o
```

## Usage

### Automatic (Recommended)

AI analysis is automatically used when available:

```python
from saraphina.self_modification_engine import SelfModificationEngine

engine = SelfModificationEngine(code_factory, proposal_db, security, db)

# Automatically uses AI if available, falls back to regex
proposal = engine.propose_improvement(
    target_file='security_manager.py',
    improvement_spec='Add rate limiting'
)
# Uses hybrid AI + regex analysis
```

### Manual

```python
from saraphina.ai_risk_analyzer import AIRiskAnalyzer

analyzer = AIRiskAnalyzer()

result = analyzer.analyze_patch(
    original_code=old_code,
    modified_code=new_code,
    file_name='auth.py'
)

print(f"Risk: {result['risk_level']}")
print(f"Reasoning: {result['reasoning']}")
```

## Configuration

### Use Different Model

```python
# GPT-4o (default) - Best quality
analyzer = AIRiskAnalyzer(model='gpt-4o')

# GPT-4o-mini - Faster, cheaper (75% cost reduction)
analyzer = AIRiskAnalyzer(model='gpt-4o-mini')

# GPT-4-turbo - Alternative
analyzer = AIRiskAnalyzer(model='gpt-4-turbo')
```

### Custom API Key

```python
analyzer = AIRiskAnalyzer(api_key='sk-project-specific-key')
```

### Disable AI (Use Regex Only)

```python
engine.ai_risk_analyzer = None  # Disables AI, uses regex only
```

## Testing

### Basic Test
```bash
python tests/test_ai_risk_analyzer.py
```

### With API Key
```bash
set OPENAI_API_KEY=sk-...
python tests/test_ai_risk_analyzer.py
```

### Run Specific Test
```bash
pytest tests/test_ai_risk_analyzer.py::test_ai_understands_refactoring -v
```

## Troubleshooting

### "openai package not installed"

**Solution**:
```bash
pip install openai
```

### "OPENAI_API_KEY not set"

**Solution**: Set environment variable (see step 3 above)

**Verification**:
```bash
# Windows
echo %OPENAI_API_KEY%

# Linux/Mac
echo $OPENAI_API_KEY
```

### "API key invalid"

**Solution**: 
- Check key starts with `sk-`
- Verify key is active at https://platform.openai.com/api-keys
- Generate new key if needed

### "Rate limit exceeded"

**Solution**:
- System automatically falls back to regex
- Wait a few seconds and retry
- Upgrade OpenAI plan if frequent
- Use `gpt-4o-mini` for lower limits

### "API error: ..."

**Solution**:
- Check internet connection
- Verify OpenAI API status: https://status.openai.com
- System automatically falls back to regex on errors
- Check OpenAI account has credits

## Cost Management

### Estimate Costs

```python
from saraphina.ai_risk_analyzer import AIRiskAnalyzer

# Typical analysis:
# - Input: ~800 tokens (code + prompt)
# - Output: ~250 tokens (JSON response)
# - Cost: ~$0.003 per analysis (GPT-4o)
# - Cost: ~$0.0005 per analysis (GPT-4o-mini)

# For 100 analyses per month:
# - GPT-4o: ~$0.30/month
# - GPT-4o-mini: ~$0.05/month
```

### Monitor Usage

Check usage at: https://platform.openai.com/usage

### Reduce Costs

1. **Use GPT-4o-mini** (75% cheaper):
```python
analyzer = AIRiskAnalyzer(model='gpt-4o-mini')
```

2. **Disable for non-critical changes**:
```python
if is_critical_change:
    analyzer.analyze_patch(...)
else:
    # Use regex only
    regex_model.classify_patch(...)
```

3. **Cache results**:
```python
# Cache analyses by code hash
cache[code_hash] = analyzer.analyze_patch(...)
```

## Features Enabled

When API key is set, you get:

✅ **Context-aware risk analysis**
- Understands code intent (refactoring vs removal)
- Distinguishes adding vs removing security

✅ **Subtle vulnerability detection**
- SQL injection
- XSS vulnerabilities  
- Authentication bypass
- Race conditions

✅ **Natural language explanations**
- Why is this risky?
- What should I verify?
- What are the concerns?

✅ **Plain English diffs**
- Explain changes to non-programmers
- Summarize impact

✅ **Hybrid mode**
- AI analysis with regex fallback
- Best of both worlds

## When to Use AI vs Regex

| Scenario | Recommendation | Reason |
|----------|---------------|--------|
| Security-critical modules | **AI** | Better at detecting subtle issues |
| Refactoring | **AI** | Understands intent |
| Auto-generated code | **Regex** | Faster, predictable patterns |
| Batch processing | **Regex** | No API latency |
| Interactive use | **AI** | Worth the 2-5s delay |
| Learning/training | **AI** | Educational reasoning |

## Integration Checklist

✅ Install openai: `pip install openai`
✅ Get API key: https://platform.openai.com/api-keys
✅ Set OPENAI_API_KEY environment variable
✅ Verify: `python tests/test_ai_risk_analyzer.py`
✅ Works automatically in SelfModificationEngine
✅ Falls back gracefully to regex if unavailable

## Next Steps

1. **Test with sample code**: Run test suite to see AI in action
2. **Compare AI vs Regex**: Use `compare_with_regex_model()` to see differences
3. **Review AI reasoning**: Check approval requests for detailed explanations
4. **Monitor usage**: Track API costs at OpenAI dashboard
5. **Consider multi-agent**: Next enhancement (Phase 32) for consensus-based review

## Summary

Phase 30.5 is **optional but highly recommended**:

- **Without API key**: Falls back to regex (still safe and functional)
- **With API key**: Gets intelligent, context-aware analysis
- **Cost**: ~$0.003 per analysis (~$1/month for typical use)
- **Benefit**: Dramatically better accuracy, fewer false positives

**Recommendation**: Set up API key for development/critical changes, use regex for production automation.

## Support

Issues? Check:
- https://platform.openai.com/docs - OpenAI docs
- https://status.openai.com - Service status  
- Phase 30.5 docs: `docs/phase30.5_ai_risk_analysis.md`
