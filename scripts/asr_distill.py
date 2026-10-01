# -*- coding: utf-8 -*-
"""asr_distill.py — 原声批量转写（faster-whisper）
用法：python asr_distill.py <媒体目录> [--model large-v3-turbo] [--out asr.json]
扫描目录内 mp4/mp3/m4a/wav，逐个转写，输出 <目录>/_asr.json（词级时间戳+全文）。
首次运行自动下载模型（约 1.6GB，可用 HF_ENDPOINT=https://hf-mirror.com 加速）。
"""
import argparse, json, os, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media_dir")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from faster_whisper import WhisperModel
    exts = (".mp4", ".mp3", ".m4a", ".wav")
    files = sorted(f for f in os.listdir(args.media_dir) if f.lower().endswith(exts))
    if not files:
        print("no media files found"); sys.exit(1)
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    result = {}
    for f in files:
        path = os.path.join(args.media_dir, f)
        try:
            segments, info = model.transcribe(path, language="zh", vad_filter=True, word_timestamps=True)
            segs = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segments]
            result[f] = {"segs": segs, "full": "".join(s["text"] for s in segs)}
            print("%s: %d segs | %s" % (f, len(segs), result[f]["full"][:60]))
        except Exception as e:
            result[f] = {"error": str(e)[:200]}
            print("%s: ERROR %s" % (f, str(e)[:80]))
    out = args.out or os.path.join(args.media_dir, "_asr.json")
    json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("DONE ->", out)

if __name__ == "__main__":
    main()
