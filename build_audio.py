#!/usr/bin/env python3
"""Génère un MP3 « français → allemand » à partir de spoken_<name>.py via ElevenLabs.

Séquence par mot : FR · pause (pour deviner) · DE · pause courte · DE · pause.
Les clips sont mis en cache dans clips/<name>/ pour ne pas repayer à chaque rebuild.

Usage : .venv/bin/python build_audio.py [kapitel1]
"""
import importlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

name = sys.argv[1] if len(sys.argv) > 1 else "kapitel1"
SPOKEN = importlib.import_module(f"spoken_{name}").SPOKEN

KEY = next(l.split("=", 1)[1].strip() for l in open(os.path.expanduser("~/Documents/capinter-video-ads/.env"))
           if l.startswith("ELEVENLABS_API_KEY="))
VOICES = {"fr": "ICk609TItINMseDpChFt",  # Léa formatrice – ton posé et pédagogue
          "de": "FTNCalFNG5bRnkkaP5Ug"}  # Otto – voix allemande native (bibliothèque)
MODEL = "eleven_flash_v2_5"  # accepte language_code
PAUSE_GUESS, PAUSE_REPEAT, PAUSE_NEXT = 2.0, 0.7, 1.6

clips = Path("clips") / name
clips.mkdir(parents=True, exist_ok=True)


def tts(text, lang, path):
    if path.exists():
        return
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICES[lang]}?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": MODEL, "language_code": lang,
                         "voice_settings": {"stability": 0.6, "similarity_boost": 0.8, "speed": 0.9}}).encode(),
        headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        path.write_bytes(r.read())
    print(f"  {lang} {text}")


def silence(sec, path):
    if not path.exists():
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                        "-t", str(sec), path], check=True)


sil = {}
for tag, sec in (("guess", PAUSE_GUESS), ("repeat", PAUSE_REPEAT), ("next", PAUSE_NEXT)):
    p = clips / f"sil_{tag}.wav"
    silence(sec, p)
    sil[tag] = p

order = []
for i, (fr, de) in enumerate(SPOKEN, 1):
    f_fr, f_de = clips / f"{i:02d}_fr.mp3", clips / f"{i:02d}_de.mp3"
    tts(fr, "fr", f_fr)
    tts(de, "de", f_de)
    order += [f_fr, sil["guess"], f_de, sil["repeat"], f_de, sil["next"]]

# concat : décodage en wav mono 44.1k puis encodage mp3
lst = clips / "concat.txt"
lst.write_text("".join(f"file '{p.resolve()}'\n" for p in order))
out = f"vocab_{name}_fr-de.mp3"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                "-ar", "44100", "-ac", "1", "-b:a", "96k",
                "-metadata", f"title=Wortschatz {name} – FR → DE", "-metadata", "artist=Flashcards allemand",
                "-metadata", "album=Allemand", out], check=True)
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                     capture_output=True, text=True).stdout.strip()
print(f"{out} : {len(SPOKEN)} mots, {float(dur)/60:.1f} min")
