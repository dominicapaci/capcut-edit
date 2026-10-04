#!/usr/bin/env python3
"""transcribe.py <video> [out_dir] — word-level timestamps for placing captions and graphics on the beat.
Writes words.txt (one '  time word' per line), words.json and words.srt. Engines, first found wins:
mlx_whisper (Apple Silicon, fast) → faster-whisper → openai-whisper."""
import sys, os, json, subprocess, shutil
video = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(video))
os.makedirs(out, exist_ok=True); wav = os.path.join(out, "audio16k.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video], capture_output=True, text=True).stdout)
words = []
mlx = shutil.which("mlx_whisper") or os.path.expanduser("~/.local/bin/mlx_whisper")
if os.path.exists(mlx):
    subprocess.run([mlx, "--model", "mlx-community/whisper-large-v3-turbo", "--language", "en", "--word-timestamps", "True",
                    "--output-format", "json", "--output-name", "words", "-o", out, wav], check=True, capture_output=True)
    d = json.load(open(os.path.join(out, "words.json")))
    for s in d["segments"]:
        for w in s.get("words", []): words.append((w["start"], w["end"], w["word"].strip()))
else:
    try:
        from faster_whisper import WhisperModel
        segs, _ = WhisperModel("large-v3-turbo", compute_type="int8").transcribe(wav, word_timestamps=True, language="en")
        for s in segs:
            for w in s.words or []: words.append((w.start, w.end, w.word.strip()))
    except ImportError:
        import whisper
        r = whisper.load_model("turbo").transcribe(wav, word_timestamps=True, language="en")
        for s in r["segments"]:
            for w in s.get("words", []): words.append((w["start"], w["end"], w["word"].strip()))
words = [w for w in words if w[0] <= dur + 0.5]                          # whisper hallucinates past the end of the audio
open(os.path.join(out, "words.txt"), "w").write("".join(f"{a:6.2f} {w}\n" for a, b, w in words))
json.dump([{"start": a, "end": b, "word": w} for a, b, w in words], open(os.path.join(out, "words.json"), "w"))
def ts(t): return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}".replace(".", ",")
with open(os.path.join(out, "words.srt"), "w") as f:                    # one cue per ~6 words, for capcut detect-retakes
    for i in range(0, len(words), 6):
        chunk = words[i:i + 6]; f.write(f"{i // 6 + 1}\n{ts(chunk[0][0])} --> {ts(chunk[-1][1])}\n{' '.join(w for _, _, w in chunk)}\n\n")
os.remove(wav); print(f"{len(words)} words → {out}/words.txt   (video {dur:.1f}s)")
