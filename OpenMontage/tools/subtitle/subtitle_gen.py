"""Subtitle generation tool.

Converts word-level timestamps from the transcriber into SRT, VTT,
or caption JSON formats. Pure Python — no external dependencies beyond
the standard library.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolStability,
    ToolTier,
)

# Punctuation that ends a sentence — a strong, almost-always-correct break point.
SENTENCE_END = frozenset(".!?…。！？")
# Punctuation that ends a clause — a softer break point, used once a cue is
# already reasonably full so we don't strand a couple of words on their own line.
CLAUSE_END = frozenset(",;:，、；：")


def _is_cjk_char(ch: str) -> bool:
    """True for CJK ideographs, kana, and Hangul (scripts written without spaces)."""
    code = ord(ch)
    return (
        0x3040 <= code <= 0x30FF  # Hiragana + Katakana
        or 0x3400 <= code <= 0x4DBF  # CJK Extension A
        or 0x4E00 <= code <= 0x9FFF  # CJK Unified Ideographs
        or 0xF900 <= code <= 0xFAFF  # CJK Compatibility Ideographs
        or 0xAC00 <= code <= 0xD7A3  # Hangul syllables
    )


def _is_cjk_text(text: str) -> bool:
    """Heuristic: treat text as CJK if a meaningful fraction of glyphs are CJK."""
    glyphs = [c for c in text if not c.isspace()]
    if not glyphs:
        return False
    cjk = sum(1 for c in glyphs if _is_cjk_char(c))
    return cjk / len(glyphs) >= 0.3


@dataclass
class SegmentationOptions:
    """Tunable knobs that control how words are grouped into subtitle cues."""

    max_words: int = 8
    max_chars: int = 42
    max_chars_cjk: int = 20
    max_lines: int = 2
    pause_threshold: float = 0.5
    max_duration: float = 6.0
    min_duration: float = 1.2


class SubtitleGen(BaseTool):
    name = "subtitle_gen"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "subtitle"
    provider = "openmontage"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC

    dependencies = []  # pure Python
    install_instructions = "No external dependencies required."
    agent_skills = ["remotion-best-practices"]

    capabilities = ["generate_srt", "generate_vtt", "generate_caption_json"]

    input_schema = {
        "type": "object",
        "required": ["segments"],
        "properties": {
            "segments": {
                "type": "array",
                "description": "Transcript segments from transcriber (with words and timestamps)",
            },
            "format": {
                "type": "string",
                "enum": ["srt", "vtt", "json"],
                "default": "srt",
            },
            "output_path": {"type": "string"},
            "max_chars_per_line": {
                "type": "integer",
                "default": 42,
                "description": (
                    "Max characters per displayed line for Latin scripts. A cue "
                    "may wrap across up to max_lines lines."
                ),
            },
            "max_chars_per_line_cjk": {
                "type": "integer",
                "default": 20,
                "description": (
                    "Max characters per displayed line for CJK (Chinese/Japanese/"
                    "Korean) scripts, where one glyph is one character."
                ),
            },
            "max_lines": {
                "type": "integer",
                "default": 2,
                "description": "Maximum number of lines per subtitle cue.",
            },
            "max_words_per_cue": {
                "type": "integer",
                "default": 8,
                "description": (
                    "Hard cap on words per cue (Latin scripts only; ignored for "
                    "CJK where the character budget governs)."
                ),
            },
            "pause_threshold": {
                "type": "number",
                "default": 0.5,
                "description": (
                    "Silence gap (seconds) between consecutive words that triggers "
                    "a natural cue break."
                ),
            },
            "max_duration": {
                "type": "number",
                "default": 6.0,
                "description": "Maximum on-screen duration (seconds) for a single cue.",
            },
            "min_duration": {
                "type": "number",
                "default": 1.2,
                "description": (
                    "Minimum on-screen duration (seconds). Shorter cues are merged "
                    "forward with the next cue when it does not cross a sentence "
                    "boundary or violate the length limits."
                ),
            },
            "highlight_style": {
                "type": "string",
                "enum": ["none", "word_by_word", "karaoke"],
                "default": "none",
            },
            "corrections": {
                "type": "object",
                "description": (
                    "Dictionary of word corrections for common ASR misrecognitions. "
                    "Keys are the wrong word (case-insensitive), values are the "
                    "correct replacement. Applied before generating subtitles. "
                    "Example: {\"cloud\": \"Claude\", \"co-pilot\": \"Copilot\"}."
                ),
            },
        },
    }

    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=128, vram_mb=0, disk_mb=10)
    idempotency_key_fields = ["segments", "format", "max_words_per_cue"]
    side_effects = ["writes subtitle file to output_path"]
    user_visible_verification = [
        "Play video with generated subtitles and verify timing",
    ]

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        segments = inputs["segments"]
        fmt = inputs.get("format", "srt")
        highlight_style = inputs.get("highlight_style", "none")
        output_path = inputs.get("output_path")
        corrections = inputs.get("corrections")

        opts = SegmentationOptions(
            max_words=inputs.get("max_words_per_cue", 8),
            max_chars=inputs.get("max_chars_per_line", 42),
            max_chars_cjk=inputs.get("max_chars_per_line_cjk", 20),
            max_lines=inputs.get("max_lines", 2),
            pause_threshold=inputs.get("pause_threshold", 0.5),
            max_duration=inputs.get("max_duration", 6.0),
            min_duration=inputs.get("min_duration", 1.2),
        )

        start = time.time()

        # Apply word corrections if provided
        if corrections:
            segments = self._apply_corrections(segments, corrections)

        # Build cues from word-level timestamps
        cues = self._build_cues(segments, opts)

        if fmt == "srt":
            content = self._render_srt(cues, highlight_style)
            ext = ".srt"
        elif fmt == "vtt":
            content = self._render_vtt(cues, highlight_style)
            ext = ".vtt"
        elif fmt == "json":
            content = json.dumps({"cues": cues, "highlight_style": highlight_style}, indent=2)
            ext = ".caption.json"
        else:
            return ToolResult(success=False, error=f"Unknown format: {fmt}")

        if output_path is None:
            output_path = f"subtitles{ext}"
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")

        elapsed = time.time() - start

        return ToolResult(
            success=True,
            data={
                "format": fmt,
                "cue_count": len(cues),
                "output": str(out),
            },
            artifacts=[str(out)],
            duration_seconds=round(elapsed, 2),
        )

    @staticmethod
    def _apply_corrections(
        segments: list[dict], corrections: dict[str, str]
    ) -> list[dict]:
        """Apply word-level corrections to transcript segments.

        Handles case-insensitive matching and preserves punctuation.
        """
        import copy

        corr = {k.lower(): v for k, v in corrections.items()}
        result = copy.deepcopy(segments)

        for seg in result:
            words = seg.get("words", [])
            for w in words:
                raw = w.get("word", "").strip()
                # Strip punctuation for lookup, preserve it
                stripped = raw.lower().rstrip(".,!?;:'\"")
                if stripped in corr:
                    trailing = raw[len(stripped):]
                    w["word"] = corr[stripped] + trailing
            # Also fix segment-level text
            if "text" in seg and words:
                seg["text"] = " ".join(w["word"] for w in words)
            elif "text" in seg:
                for wrong, right in corr.items():
                    import re as _re
                    seg["text"] = _re.sub(
                        r"\b" + _re.escape(wrong) + r"\b",
                        right,
                        seg["text"],
                        flags=_re.IGNORECASE,
                    )

        return result

    def _build_cues(
        self, segments: list[dict], opts: SegmentationOptions
    ) -> list[dict]:
        """Group words into readable cues at natural linguistic boundaries.

        Rather than chopping the word stream every N words, cues are broken at
        (in priority order): sentence-ending punctuation, silent pauses between
        words, and clause-ending punctuation — while always respecting the
        per-cue length (chars/line x lines) and duration limits. Transcriber
        segment boundaries are honoured (we never merge words from different
        segments into one cue) since they already mark sentence-ish units.
        """
        cues: list[dict] = []
        for seg in segments:
            words = seg.get("words")
            if words:
                cues.extend(self._split_words(words, opts))
            elif "text" in seg:
                # No word-level timing: keep the whole segment as one cue.
                cues.append(
                    self._make_cue(
                        [{
                            "word": seg["text"],
                            "start": seg["start"],
                            "end": seg["end"],
                        }],
                        opts,
                    )
                )

        cues = self._merge_short_cues(cues, opts)
        for i, cue in enumerate(cues):
            cue["index"] = i + 1
        return cues

    def _split_words(
        self, words: list[dict], opts: SegmentationOptions
    ) -> list[dict]:
        """Split a single transcriber segment's words into one or more cues."""
        cjk = _is_cjk_text("".join(w.get("word", "") for w in words))
        char_limit = (opts.max_chars_cjk if cjk else opts.max_chars) * max(opts.max_lines, 1)

        cues: list[dict] = []
        buf: list[dict] = []

        def visible_len(items: list[dict]) -> int:
            return len(self._join_words([i["word"].strip() for i in items], cjk))

        for i, w in enumerate(words):
            word_text = w["word"].strip()

            # Hard limits: flush the current buffer before it overflows.
            if buf:
                over_words = (not cjk) and len(buf) >= opts.max_words
                over_chars = visible_len(buf + [w]) > char_limit
                over_time = (w["end"] - buf[0]["start"]) > opts.max_duration
                if over_words or over_chars or over_time:
                    cues.append(self._make_cue(buf, opts))
                    buf = []

            buf.append(w)

            if i == len(words) - 1:
                break

            trailing = word_text[-1] if word_text else ""
            gap = words[i + 1]["start"] - w["end"]

            # Preferred break points, in descending priority.
            if trailing in SENTENCE_END:
                cues.append(self._make_cue(buf, opts))
                buf = []
            elif gap >= opts.pause_threshold and len(buf) >= 2:
                cues.append(self._make_cue(buf, opts))
                buf = []
            elif trailing in CLAUSE_END and visible_len(buf) >= char_limit * 0.6:
                cues.append(self._make_cue(buf, opts))
                buf = []

        if buf:
            cues.append(self._make_cue(buf, opts))
        return cues

    def _merge_short_cues(
        self, cues: list[dict], opts: SegmentationOptions
    ) -> list[dict]:
        """Merge cues that flash by too quickly into the following cue.

        Only merges when the short cue does not end a sentence and the combined
        cue still respects the word/char/duration limits, so we never undo a
        good linguistic break.
        """
        if len(cues) < 2:
            return cues

        merged: list[dict] = []
        i = 0
        while i < len(cues):
            cue = cues[i]
            duration = cue["end"] - cue["start"]
            if i + 1 < len(cues) and duration < opts.min_duration:
                nxt = cues[i + 1]
                combined = cue["words"] + nxt["words"]
                cjk = _is_cjk_text(cue["text"] + nxt["text"])
                char_limit = (
                    opts.max_chars_cjk if cjk else opts.max_chars
                ) * max(opts.max_lines, 1)
                text = cue["text"].replace("\n", " ")
                ends_sentence = bool(text) and text[-1] in SENTENCE_END
                # Don't merge back across a real pause — that gap is exactly why
                # we split here in the first place.
                across_pause = (nxt["start"] - cue["end"]) >= opts.pause_threshold
                combined_len = len(
                    self._join_words([w["word"].strip() for w in combined], cjk)
                )
                combined_dur = nxt["end"] - cue["start"]
                if (
                    not ends_sentence
                    and not across_pause
                    and combined_len <= char_limit
                    and (cjk or len(combined) <= opts.max_words)
                    and combined_dur <= opts.max_duration
                ):
                    cues[i + 1] = self._make_cue(combined, opts)
                    i += 1
                    continue
            merged.append(cue)
            i += 1
        return merged

    @staticmethod
    def _join_words(tokens: list[str], cjk: bool) -> str:
        """Join word tokens, with spaces for Latin scripts and none for CJK."""
        parts = [t for t in tokens if t]
        return "".join(parts) if cjk else " ".join(parts)

    def _wrap_lines(self, text: str, cjk: bool, opts: SegmentationOptions) -> list[str]:
        """Wrap a cue's text into <= max_lines display lines.

        Latin scripts wrap on whitespace; CJK wraps between glyphs. For the
        common two-line case we balance the line lengths instead of cramming
        the first line full and stranding a word on the second.
        """
        per_line = opts.max_chars_cjk if cjk else opts.max_chars
        tokens = list(text) if cjk else text.split()
        tokens = [t for t in tokens if cjk or t]
        if not tokens:
            return [text]

        full = self._join_words(tokens, cjk)
        if len(full) <= per_line or len(tokens) == 1 or opts.max_lines <= 1:
            return [full]

        if opts.max_lines == 2:
            # Prefer a split right after punctuation (so we never break a word
            # or phrase across lines); among those, pick the most balanced.
            best: tuple[tuple[int, int], list[str]] | None = None
            for k in range(1, len(tokens)):
                line1 = self._join_words(tokens[:k], cjk)
                line2 = self._join_words(tokens[k:], cjk)
                if len(line1) > per_line or len(line2) > per_line:
                    continue
                last = line1[-1] if line1 else ""
                on_punct = 0 if last in SENTENCE_END or last in CLAUSE_END else 1
                score = (on_punct, abs(len(line1) - len(line2)))
                if best is None or score < best[0]:
                    best = (score, [line1, line2])
            if best is not None:
                return best[1]

        # Fall back to greedy wrapping (also covers max_lines > 2).
        lines: list[str] = []
        cur: list[str] = []
        for t in tokens:
            cand = self._join_words(cur + [t], cjk)
            if cur and len(cand) > per_line:
                lines.append(self._join_words(cur, cjk))
                cur = [t]
            else:
                cur.append(t)
        if cur:
            lines.append(self._join_words(cur, cjk))
        return lines

    def _make_cue(self, buf: list[dict], opts: SegmentationOptions) -> dict:
        """Build a cue dict from a buffer of words, with wrapped display lines."""
        tokens = [b["word"].strip() for b in buf]
        cjk = _is_cjk_text("".join(tokens))
        single_line = self._join_words(tokens, cjk)
        lines = self._wrap_lines(single_line, cjk, opts)
        return {
            "index": 0,
            "start": buf[0]["start"],
            "end": buf[-1]["end"],
            "text": "\n".join(lines),
            "lines": lines,
            "words": [
                {"word": b["word"].strip(), "start": b["start"], "end": b["end"]}
                for b in buf
            ],
        }

    def _render_srt(self, cues: list[dict], highlight_style: str = "none") -> str:
        lines = []
        if highlight_style == "word_by_word":
            # Emit one cue per word for word-by-word reveal
            idx = 1
            for cue in cues:
                for word_info in cue.get("words", []):
                    lines.append(str(idx))
                    lines.append(
                        f"{self._ts_srt(word_info['start'])} --> {self._ts_srt(word_info['end'])}"
                    )
                    lines.append(word_info["word"])
                    lines.append("")
                    idx += 1
        elif highlight_style == "karaoke":
            # Show full cue text but bold the active word using SRT HTML tags
            for cue in cues:
                words = cue.get("words", [])
                if not words:
                    lines.append(str(cue["index"]))
                    lines.append(f"{self._ts_srt(cue['start'])} --> {self._ts_srt(cue['end'])}")
                    lines.append(cue["text"])
                    lines.append("")
                    continue
                for wi, word_info in enumerate(words):
                    lines.append(str(cue["index"] * 100 + wi))
                    lines.append(
                        f"{self._ts_srt(word_info['start'])} --> {self._ts_srt(word_info['end'])}"
                    )
                    parts = []
                    for wj, w in enumerate(words):
                        if wj == wi:
                            parts.append(f"<b>{w['word']}</b>")
                        else:
                            parts.append(w["word"])
                    lines.append(" ".join(parts))
                    lines.append("")
        else:
            for cue in cues:
                lines.append(str(cue["index"]))
                lines.append(f"{self._ts_srt(cue['start'])} --> {self._ts_srt(cue['end'])}")
                lines.append(cue["text"])
                lines.append("")
        return "\n".join(lines)

    def _render_vtt(self, cues: list[dict], highlight_style: str = "none") -> str:
        lines = ["WEBVTT", ""]
        if highlight_style == "word_by_word":
            for cue in cues:
                for word_info in cue.get("words", []):
                    lines.append(
                        f"{self._ts_vtt(word_info['start'])} --> {self._ts_vtt(word_info['end'])}"
                    )
                    lines.append(word_info["word"])
                    lines.append("")
        elif highlight_style == "karaoke":
            for cue in cues:
                words = cue.get("words", [])
                if not words:
                    lines.append(f"{self._ts_vtt(cue['start'])} --> {self._ts_vtt(cue['end'])}")
                    lines.append(cue["text"])
                    lines.append("")
                    continue
                for wi, word_info in enumerate(words):
                    lines.append(
                        f"{self._ts_vtt(word_info['start'])} --> {self._ts_vtt(word_info['end'])}"
                    )
                    parts = []
                    for wj, w in enumerate(words):
                        if wj == wi:
                            parts.append(f"<b>{w['word']}</b>")
                        else:
                            parts.append(w["word"])
                    lines.append(" ".join(parts))
                    lines.append("")
        else:
            for cue in cues:
                lines.append(f"{self._ts_vtt(cue['start'])} --> {self._ts_vtt(cue['end'])}")
                lines.append(cue["text"])
                lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _ts_srt(seconds: float) -> str:
        """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds % 1) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _ts_vtt(seconds: float) -> str:
        """Format seconds as VTT timestamp: HH:MM:SS.mmm"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds % 1) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
