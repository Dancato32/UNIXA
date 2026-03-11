# TTS (Text-to-Speech) Fix Guide

## Problem
Your podcast generation is failing because:
1. **ElevenLabs quota exceeded** - You've used all 10,000 credits
2. **OpenRouter TTS doesn't exist** - OpenRouter doesn't have a TTS endpoint (404 error)
3. **No OpenAI API key** - The fallback to OpenAI TTS can't work without a key

## Solution

### Option 1: Add OpenAI API Key (Recommended - Cheapest)
1. Get an API key from https://platform.openai.com/api-keys
2. Add it to your `.env` file:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```
3. Restart your Django server

**Cost**: ~$15 per 1 million characters (very affordable)

### Option 2: Top Up ElevenLabs
1. Go to https://elevenlabs.io/
2. Add credits to your account
3. The system will automatically use ElevenLabs first

**Cost**: More expensive but higher quality voices

### Option 3: Use Free Alternative (Google TTS)
If you want a completely free solution, I can help you integrate Google Cloud TTS free tier (1 million characters/month free).

## What I Fixed
- Removed the broken OpenRouter TTS attempt (it was causing 404 errors)
- Simplified the fallback chain: ElevenLabs → OpenAI TTS
- The code now goes straight to OpenAI when ElevenLabs fails

## Testing
After adding your OpenAI API key:
```bash
# Restart the server
python manage.py runserver

# Try generating a podcast again
# It should now work with OpenAI's TTS
```

## Current TTS Flow
```
1. Try ElevenLabs (high quality, but quota exceeded)
   ↓ (fails)
2. Try OpenAI TTS (good quality, affordable)
   ↓ (needs API key)
3. Return error if no key available
```

## Next Steps
1. Add `OPENAI_API_KEY` to your `.env` file
2. Restart Django server
3. Test podcast generation
4. Consider which TTS service you want to use long-term based on cost/quality needs
