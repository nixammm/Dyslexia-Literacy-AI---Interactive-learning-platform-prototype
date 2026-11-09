#!/usr/bin/env python3
"""Make recorded voice files for Dyslexia Literacy AI (Azure Neural TTS, Malay).

Usage (Windows / Mac / Linux, Python 3, no extra packages):
    set AZURE_SPEECH_KEY=your-key          (Mac/Linux: export AZURE_SPEECH_KEY=your-key)
    set AZURE_SPEECH_REGION=southeastasia  (the region of your Speech resource)
    python make_audio.py            # Malay only
    python make_audio.py ms en      # Malay and English

It reads wordlist.json, writes ../audio/<lang>/<slug>.mp3 and ../audio/manifest.json.
Upload the whole audio/ folder next to index.html. The app plays these files and
falls back to the browser voice for anything that is missing.
"""
import json, os, re, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent / 'audio'
KEY = os.environ.get('AZURE_SPEECH_KEY'); REGION = os.environ.get('AZURE_SPEECH_REGION', 'southeastasia')
VOICES = {'ms': ('ms-MY', 'ms-MY-YasminNeural'), 'en': ('en-US', 'en-US-JennyNeural')}  # Yasmin = female; ms-MY-OsmanNeural = male
RATE = {'short': '-15%', 'long': '-10%'}   # a little slower for children

def slug(t):
    t = re.sub(r'[^\w\s-]', '', t.lower()).strip()
    return re.sub(r'\s+', '-', t)

def synth(text, lang):
    loc, voice = VOICES[lang]
    rate = RATE['short'] if len(text) < 8 else RATE['long']
    esc = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    ssml = f"<speak version='1.0' xml:lang='{loc}'><voice name='{voice}'><prosody rate='{rate}'>{esc}</prosody></voice></speak>"
    req = urllib.request.Request(f'https://{REGION}.tts.speech.microsoft.com/cognitiveservices/v1', data=ssml.encode('utf-8'), headers={
        'Ocp-Apim-Subscription-Key': KEY, 'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-24khz-48kbitrate-mono-mp3', 'User-Agent': 'dyslexia-literacy-ai'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def main():
    if not KEY: sys.exit('Set AZURE_SPEECH_KEY first (see the top of this file).')
    langs = sys.argv[1:] or ['ms']
    words = json.loads((HERE / 'wordlist.json').read_text(encoding='utf-8'))
    manifest = {'ms': [], 'en': []}
    mpath = OUT / 'manifest.json'
    if mpath.exists(): manifest.update(json.loads(mpath.read_text()))
    for lang in langs:
        (OUT / lang).mkdir(parents=True, exist_ok=True)
        for text in words[lang]:
            s = slug(text); f = OUT / lang / f'{s}.mp3'
            if not f.exists():
                try: f.write_bytes(synth(text, lang)); print('ok  ', lang, text); time.sleep(0.2)
                except Exception as e: print('FAIL', lang, text, e); continue
            if s not in manifest[lang]: manifest[lang].append(s)
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    print('Done. Upload the audio/ folder next to index.html.')

main()
