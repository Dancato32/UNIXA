# Podcast Raise Hand Feature - Implementation Complete

## Overview
Added an interactive "raise hand" feature to the podcast player that allows students to pause the podcast, ask questions about the content, and receive AI-powered answers with text-to-speech.

## Features Implemented

### 1. Floating Raise Hand Button (✋)
- Appears only when podcast is actively playing
- Fixed position in bottom-right corner
- Animated pulse effect to draw attention
- Mobile-responsive sizing

### 2. Question Modal
- Clean, modern modal overlay
- Text input for student questions
- AI-powered answer generation
- Text-to-speech for answers (ElevenLabs → OpenAI fallback)
- "Continue Podcast" button to resume playback

### 3. Smart Playback Management
- Automatically pauses podcast when question modal opens
- Saves playback position
- Resumes from exact position when continuing
- Stops answer audio when resuming podcast

### 4. Backend Integration
- New endpoint: `/materials/podcast/question/` - handles question submission
- Uses podcast transcript as context for AI answers
- Generates audio answers using same TTS system as main podcast
- Separate audio storage for answers: `media/podcast_answers/`

## User Flow

1. Student starts listening to podcast
2. Raise hand button (✋) appears during playback
3. Student clicks button → podcast pauses
4. Modal opens with question input
5. Student types question and clicks "Ask AI"
6. AI generates answer based on podcast context
7. Answer displayed as text + played as audio
8. Student clicks "Continue Podcast"
9. Podcast resumes from exact position

## Technical Details

### Frontend (podcast.html)
- CSS styles for button and modal
- JavaScript functions:
  - `openQuestionModal()` - pauses podcast, shows modal
  - `submitQuestion()` - sends question to backend
  - `playAnswerAudio()` - plays TTS answer
  - `continuePodcast()` - resumes podcast playback
  - `updateRaiseHandButton()` - shows/hides button based on playback state

### Backend (views.py)
- `podcast_question_ajax()` - main endpoint for questions
- `generate_answer_audio_elevenlabs()` - ElevenLabs TTS for answers
- `generate_answer_audio_openai()` - OpenAI TTS fallback
- `serve_answer_audio()` - serves generated answer audio files

### URL Routes (urls.py)
- `podcast/question/` - question submission endpoint
- `podcast/answer-audio/<material_id>/<filename>/` - answer audio serving

## TTS Fallback System
1. Try ElevenLabs (high quality, Rachel voice)
2. Fall back to OpenAI TTS (nova voice)
3. If both fail, text-only answer displayed

## Mobile Responsive
- Button size adjusts for mobile (60px vs 70px)
- Modal padding optimized for small screens
- Touch-friendly tap targets
- Proper z-index layering

## Files Modified
1. `nexa/materials/templates/materials/podcast.html` - UI and JavaScript
2. `nexa/materials/views.py` - backend endpoints
3. `nexa/materials/urls.py` - URL routing

## Testing Checklist
- [ ] Raise hand button appears during playback
- [ ] Button hidden when podcast paused/stopped
- [ ] Modal opens and pauses podcast
- [ ] Question submission works
- [ ] AI answer generated correctly
- [ ] Answer audio plays (if TTS available)
- [ ] Continue button resumes podcast from correct position
- [ ] Works on mobile devices
- [ ] Works with both ElevenLabs and OpenAI TTS

## Future Enhancements
- Add question history/bookmarks
- Allow multiple questions without closing modal
- Show transcript highlighting for relevant sections
- Add voice input for questions
- Save Q&A pairs for later review
