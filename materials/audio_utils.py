import os
import asyncio
import concurrent.futures
import edge_tts
import json
import uuid
import requests
import base64
import re
from django.conf import settings

# Voices mapping
VOICES = {
    'Alex': 'en-US-AndrewNeural',   # Male, natural and warm
    'Sam': 'en-US-AvaNeural',       # Female, natural and professional
    'Divine': 'en-US-EmmaNeural',   # Divine, smooth, melodic female voice (Singer)
    'Host 1': 'en-US-AndrewNeural',
    'Host 2': 'en-US-AvaNeural',
    'Vocal': 'en-US-EmmaNeural',
    'Singer': 'en-US-EmmaNeural',
}


def _run_async_safe(coro):
    """
    Safely run an async coroutine from synchronous Django code.

    asyncio.run() raises RuntimeError on Gunicorn/production servers that
    already have a running event loop (e.g. when using async workers or
    certain Django middleware). This helper always spawns a fresh event
    loop in a dedicated thread, which is safe in ALL environments.
    """
    def _runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_runner)
        return future.result()


async def _generate_all(segments, storage_dir):
    """Internal async helper to run all TTS tasks in parallel."""
    tasks = []
    for seg in segments:
        voice = VOICES.get(seg['speaker'], VOICES['Alex'])
        filepath = os.path.join(storage_dir, seg['filename'])
        # Edge TTS
        tasks.append(edge_tts.Communicate(seg['text'], voice).save(filepath))

    await asyncio.gather(*tasks)


async def _generate_all_premium(segments, storage_dir):
    """Use Resemble.ai to generate high-quality audio for each segment in parallel. Fallback to Edge TTS on failure."""
    api_key = os.environ.get("RESEMBLE_API_KEY") or os.getenv("RESEMBLE_API_KEY") or getattr(settings, 'RESEMBLE_API_KEY', None)
    if not api_key:
        # Fallback to standard if no key
        return await _generate_all(segments, storage_dir)

    voice_uuid = "f644f59c"  # NEXA Divine Custom Voice

    async def _bake_one(seg):
        try:
            filepath = os.path.join(storage_dir, seg['filename'])
            response = requests.post(
                "https://f.cluster.resemble.ai/synthesize",
                headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
                json={"voice_uuid": voice_uuid, "data": seg['text'], "output_format": "mp3"},
                timeout=60
            )
            if response.status_code == 200:
                audio_b64 = response.json().get("audio_content")
                if audio_b64:
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(audio_b64))
                    return  # Success

            # Fallback to Edge TTS for this segment if premium fails
            voice = VOICES.get(seg['speaker'], VOICES['Alex'])
            await edge_tts.Communicate(seg['text'], voice).save(filepath)

        except Exception as e:
            print(f"Premium/Fallback Bake Error: {e}")
            # Ensure file exists at least as fallback
            try:
                filepath = os.path.join(storage_dir, seg['filename'])
                if not os.path.exists(filepath):
                    voice = VOICES.get(seg['speaker'], VOICES['Alex'])
                    await edge_tts.Communicate(seg['text'], voice).save(filepath)
            except Exception:
                pass

    tasks = [asyncio.create_task(_bake_one(seg)) for seg in segments]
    await asyncio.gather(*tasks)


def generate_podcast_segments(script_text, material_id, fixed_voice=None, use_premium=False):
    """
    Parses a podcast script and generates MP3 segments for each line in parallel.
    Returns a list of dicts: [{'speaker': '...', 'text': '...', 'audio_url': '...'}]
    """
    folder_name = f"podcast_{material_id}_{uuid.uuid4().hex[:8]}"
    storage_dir = os.path.join(settings.MEDIA_ROOT, 'podcast_segments', folder_name)
    os.makedirs(storage_dir, exist_ok=True)

    lines = [l.strip() for l in script_text.split('\n') if l.strip()]
    segments_to_bake = []

    # Optional: Add Intro Music if it exists in media folder
    intro_path = os.path.join(settings.MEDIA_ROOT, 'podcast_intro.mp3')
    if os.path.exists(intro_path):
        segments_to_bake.append({
            'speaker': 'Music',
            'text': '[Intro Music]',
            'filename': None,  # Don't bake, just use the URL
            'audio_url': f"{settings.MEDIA_URL}podcast_intro.mp3"
        })

    for i, line in enumerate(lines):
        # 1. Identify Speaker but don't include it in voice text
        # Support Alex, Sam, Host, Divine, Vocal, Singer
        m = re.match(r'^(Alex|Sam|Host \d|Host|Divine|Vocal|Singer):\s*(.*)', line, re.I)
        speaker = m.group(1).title() if m else 'Alex'
        raw_text = m.group(2) if m else line

        # 2. Strong Recursive Name/Vocal/Section Stripping
        # Ensure 'Alex: [Verse 1]: Hello' becomes 'Hello'
        clean_text = raw_text
        while True:
            # Matches names, Vocal:, Lyric:, Verse 1:, Chorus:, etc.
            new_text = re.sub(r'^(Alex|Sam|Host \d|Host|Vocal|Lyric|Verse \d?|Chorus|Intro|Outro|Bridge|Hook):\s*', '', clean_text, flags=re.I).strip()
            if new_text == clean_text:
                break
            clean_text = new_text

        # 3. Final cleanup (stars, directions)
        clean_text = clean_text.replace('**', '').replace('[', '').replace(']', '').strip()

        if not clean_text:
            continue

        filename = f"seg_{i}_{speaker.lower().replace(' ', '_')}.mp3"

        segments_to_bake.append({
            'speaker': speaker,
            'text': clean_text,
            'filename': filename,
            'audio_url': f"{settings.MEDIA_URL}podcast_segments/{folder_name}/{filename}"
        })

    # Run all TTS tasks (skip those with no filename like music)
    # Use _run_async_safe instead of asyncio.run() to avoid event loop conflicts on Gunicorn
    tasks_to_bake = [s for s in segments_to_bake if s.get('filename')]
    if tasks_to_bake:
        try:
            if use_premium:
                _run_async_safe(_generate_all_premium(tasks_to_bake, storage_dir))
            else:
                _run_async_safe(_generate_all(tasks_to_bake, storage_dir))
        except Exception as e:
            print(f"[AUDIO_UTILS] TTS generation error: {e}")

    return segments_to_bake
