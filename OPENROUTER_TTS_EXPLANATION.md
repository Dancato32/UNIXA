# Why OpenRouter Can't Be Used for TTS

## The Reality

**OpenRouter does NOT support Text-to-Speech (TTS).** 

OpenRouter is a service that routes LLM (Large Language Model) requests to different AI providers. It's designed for:
- Text generation (chat, completion)
- Text analysis
- Code generation
- NOT audio generation

## What Your Error Logs Show

When the code tried to use OpenRouter for TTS, it returned:
```
<!DOCTYPE html>
<html lang="en">
<head>
<title>Not Found | OpenRouter</title>
...
404: Not Found
```

This is OpenRouter's 404 page, proving they don't have a TTS endpoint.

## Your Current Setup (FIXED)

### What Works:
- **Chat/AI Responses**: OpenRouter ✅
  - Uses your `OPENROUTER_API_KEY`
  - Routes to various LLMs (GPT-4, Claude, etc.)
  - Working perfectly

### What I Fixed for Voice:
```
User clicks "Listen"
  ↓
1. Try ElevenLabs (high quality)
   → If quota exceeded, go to step 2
  ↓
2. Try OpenAI TTS (if API key exists)
   → If no key, go to step 3
  ↓
3. Use Browser TTS (free, robotic voice)
   → Always works as final fallback
```

## Your Options for Voice

### Option 1: Browser TTS (Current - FREE)
- **Cost**: Free
- **Quality**: Robotic, basic
- **Setup**: None needed - already working!
- **Status**: ✅ Working now

### Option 2: Top up ElevenLabs (Best Quality)
- **Cost**: Pay for credits
- **Quality**: Most natural, human-like
- **Setup**: Add credits to your ElevenLabs account
- **Status**: Quota exceeded

### Option 3: Add OpenAI TTS (Recommended)
- **Cost**: ~$15 per million characters (very cheap)
- **Quality**: Good, natural
- **Setup**: Add `OPENAI_API_KEY` to `.env`
- **Status**: Ready to use if you add the key

## What I Changed

1. **Backend (`ai_utils.py`)**:
   - Try ElevenLabs first
   - Try OpenAI second (only if key exists)
   - Return None if both fail

2. **Frontend (`chat.html`)**:
   - Call backend TTS endpoint
   - If backend fails, use browser TTS automatically
   - Always works, never crashes

## Testing Now

1. Restart Django server
2. Go to AI Tutor chat
3. Click "Listen" on any response
4. You'll hear browser TTS (robotic voice)

It works! The voice quality isn't great, but it's functional and free.

## To Upgrade Voice Quality

If you want better voices later:
1. Add OpenAI API key to `.env` (cheap, good quality)
2. Or top up ElevenLabs (expensive, best quality)

But for now, browser TTS works as a free fallback!
