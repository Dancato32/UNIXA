# Voice Mode Not Working - URGENT FIX

## The Problem
Voice mode is failing with "Internal Server Error" because:
1. ElevenLabs quota is exceeded (0 credits remaining)
2. OpenAI fallback isn't working because you don't have an OPENAI_API_KEY
3. The system is trying to use OpenRouter key for TTS, which doesn't work

## The Solution

### You MUST add an OpenAI API key:

1. **Get an OpenAI API key**:
   - Go to https://platform.openai.com/api-keys
   - Create a new API key
   - Copy it

2. **Add it to your `.env` file**:
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

3. **Restart Django server**:
```bash
# Stop the server (Ctrl+C)
python manage.py runserver
```

## Why This Happens

Your current flow:
```
User clicks "Listen"
  ↓
Try ElevenLabs → FAILS (quota exceeded)
  ↓
Try OpenAI fallback → FAILS (no API key)
  ↓
ERROR 500
```

After adding OpenAI key:
```
User clicks "Listen"
  ↓
Try ElevenLabs → FAILS (quota exceeded)
  ↓
Try OpenAI fallback → SUCCESS ✅
  ↓
Voice plays!
```

## Cost Information

### OpenAI TTS Pricing:
- **$15 per 1 million characters**
- Very affordable for testing
- Good quality voices
- Example: 1000 words ≈ 5000 characters ≈ $0.075 (less than 8 cents!)

### ElevenLabs Pricing:
- You've used all 10,000 free credits
- Need to top up or upgrade plan
- Higher quality but more expensive

## Quick Test

After adding the key and restarting:

1. Go to http://localhost:8000/ai-tutor/chat/
2. Type a question
3. Click "Listen" button
4. You should hear OpenAI's voice (not as good as ElevenLabs, but it works!)

## What I Fixed

1. ✅ Updated JavaScript to call backend TTS endpoint
2. ✅ Backend tries ElevenLabs first, then OpenAI
3. ✅ Added proper error handling
4. ❌ **YOU NEED TO**: Add OPENAI_API_KEY to `.env`

## Without OpenAI Key

If you don't want to add an OpenAI key, your only options are:
1. Top up ElevenLabs credits
2. No voice mode at all

The choice is yours, but OpenAI TTS is the cheapest and easiest solution for now.
