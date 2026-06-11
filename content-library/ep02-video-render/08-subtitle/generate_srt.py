"""
08-subtitle 字幕生成脚本：使用 Whisper 对 06-TTS 产出的 WAV 文件做语音识别，生成 SRT 字幕。
用法：python generate_srt.py
前置：pip install openai-whisper
"""

import json
import os
import time
from pathlib import Path

# --- 配置 ---
SCRIPT_DIR = Path(__file__).parent
TTS_ASSETS = SCRIPT_DIR.parent / "06-tts" / "assets"
SUBTITLE_ASSETS = SCRIPT_DIR / "assets"
SUBTITLE_ASSETS.mkdir(exist_ok=True)

# Whisper 配置
WHISPER_MODEL = "base"  # 使用 base 模型（快速，中文基本够用；后续可升级 large-v3）
LANGUAGE = "zh"
MAX_CHARS_PER_LINE = 20  # 中文每行最多 20 字


def format_timestamp(seconds: float) -> str:
    """将秒数格式化为 SRT 时间戳 HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def split_text_lines(text: str, max_chars: int = MAX_CHARS_PER_LINE) -> str:
    """将长文本按 max_chars 分行"""
    if len(text) <= max_chars:
        return text
    # 按 max_chars 切分，最多两行
    line1 = text[:max_chars]
    line2 = text[max_chars:max_chars * 2]
    if line2:
        return f"{line1}\n{line2}"
    return line1


def generate_subtitles():
    """使用 Whisper 对所有 TTS WAV 文件生成字幕"""
    import whisper

    # 读取 manifest 获取段落顺序和时间偏移
    manifest_path = TTS_ASSETS / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Loading Whisper model: {WHISPER_MODEL}")
    model = whisper.load_model(WHISPER_MODEL)
    print("Model loaded.")

    all_srt_entries = []
    subtitle_index = 1
    cumulative_offset = 0.0  # 累计时间偏移（各段落依次拼接）

    for seg_info in manifest["segments"]:
        seg_id = seg_info["segment_id"]
        wav_file = TTS_ASSETS / seg_info["output_file"]

        if not wav_file.exists():
            print(f"  SKIP (file not found): {wav_file}")
            cumulative_offset += seg_info["duration_seconds"]
            continue

        print(f"\n--- Transcribing: {seg_id} (offset={cumulative_offset:.2f}s) ---")
        start_time = time.time()

        # Whisper 转录
        result = model.transcribe(
            str(wav_file),
            language=LANGUAGE,
            word_timestamps=True,
            verbose=False,
        )

        elapsed = time.time() - start_time
        print(f"  Transcribed in {elapsed:.2f}s, {len(result['segments'])} segments")

        # 将 Whisper segments 转为 SRT 条目
        for ws in result["segments"]:
            text = ws["text"].strip()
            if not text:
                continue

            # 加上累计偏移
            start_sec = ws["start"] + cumulative_offset
            end_sec = ws["end"] + cumulative_offset

            # 分行处理
            display_text = split_text_lines(text)

            all_srt_entries.append({
                "index": subtitle_index,
                "start": start_sec,
                "end": end_sec,
                "text": display_text,
                "segment_id": seg_id,
            })
            subtitle_index += 1

        cumulative_offset += seg_info["duration_seconds"]

    # 写入 SRT 文件
    srt_path = SUBTITLE_ASSETS / "ep02-video-render.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for entry in all_srt_entries:
            f.write(f"{entry['index']}\n")
            f.write(f"{format_timestamp(entry['start'])} --> {format_timestamp(entry['end'])}\n")
            f.write(f"{entry['text']}\n\n")

    # 写入 VTT 文件
    vtt_path = SUBTITLE_ASSETS / "ep02-video-render.vtt"
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for entry in all_srt_entries:
            start_vtt = format_timestamp(entry["start"]).replace(",", ".")
            end_vtt = format_timestamp(entry["end"]).replace(",", ".")
            f.write(f"{start_vtt} --> {end_vtt}\n")
            f.write(f"{entry['text']}\n\n")

    # 写入 JSON manifest
    subtitle_manifest = {
        "whisper_model": WHISPER_MODEL,
        "language": LANGUAGE,
        "total_entries": len(all_srt_entries),
        "total_duration_seconds": round(cumulative_offset, 2),
        "max_chars_per_line": MAX_CHARS_PER_LINE,
        "files": {
            "srt": str(srt_path.name),
            "vtt": str(vtt_path.name),
        },
        "entries_by_segment": {},
    }
    for entry in all_srt_entries:
        sid = entry["segment_id"]
        if sid not in subtitle_manifest["entries_by_segment"]:
            subtitle_manifest["entries_by_segment"][sid] = 0
        subtitle_manifest["entries_by_segment"][sid] += 1

    manifest_out = SUBTITLE_ASSETS / "subtitle_manifest.json"
    with open(manifest_out, "w", encoding="utf-8") as f:
        json.dump(subtitle_manifest, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"DONE! {len(all_srt_entries)} subtitle entries generated.")
    print(f"Total duration: {cumulative_offset:.2f}s")
    print(f"SRT: {srt_path}")
    print(f"VTT: {vtt_path}")
    print(f"Manifest: {manifest_out}")


if __name__ == "__main__":
    generate_subtitles()
