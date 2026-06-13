#!/usr/bin/env python3
"""Build ep02-video-render.json Remotion props from the ep02 SSOT.

Unlike the legacy ``align_episode.py`` (which hard-coded the on-screen content of
each scene and therefore froze an outdated narrative), this generator derives
everything from the current ep02 pipeline artifacts:

* On-screen scene props (titles / items / table rows / terminal code / …) come
  from the **04 script** ``[画面]`` specs, transcribed into the structures the
  Remotion ``Explainer`` scene components actually consume.
* Per-scene timing comes from the **06-tts** ``assets/manifest.json``
  (real Piper-TTS segment durations), so the composition length matches the
  narration instead of a simulated cadence.
* Burned-in captions come from the **08-subtitle** proofread SRT, so the
  on-screen subtitles are identical to the published subtitle files.

The 16 cuts map 1:1 to the 04 contract block's 16 ``sections`` (no add / drop /
merge / reorder), keeping the Remotion render aligned with the SSOT.

Usage:
    python build_ep02_props.py                 # write props (no audio block)
    python build_ep02_props.py --with-audio    # also concat narration .wav into
                                               # public/ and reference it (for a
                                               # full local render; the .wav is
                                               # git-ignored by repo policy)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
EP_DIR = REPO_ROOT / "content-library" / "ep02-video-render"
TTS_MANIFEST = EP_DIR / "06-tts" / "assets" / "manifest.json"
TTS_ASSETS = EP_DIR / "06-tts" / "assets"
PROOFREAD_SRT = EP_DIR / "08-subtitle" / "assets" / "ep02-video-render-proofread.srt"
COMPOSER_DIR = Path(__file__).resolve().parent / "remotion-composer"
OUTPUT_JSON = COMPOSER_DIR / "public" / "demo-props" / "ep02-video-render.json"
NARRATION_WAV = COMPOSER_DIR / "public" / "ep02-narration.wav"

FPS = 30
THEME = "flat-motion-graphics"

# 04 section id -> 06-tts segment_id (defines order + duration source).
SECTION_TO_SEGMENT: list[tuple[str, str]] = [
    ("1", "S1_intro"),
    ("2a", "S2a_paradigm"),
    ("2b", "S2b_frame_as_state"),
    ("2c", "S2c_six_routes"),
    ("3a", "S3a_judgment_matrix"),
    ("3b", "S3b_remotion_reasons"),
    ("3c", "S3c_comparison"),
    ("3d", "S3d_tradeoffs"),
    ("4a", "S4a_pipeline"),
    ("4b", "S4b_three_piece"),
    ("4c", "S4c_orchestrator"),
    ("4d", "S4d_ab_track"),
    ("5a", "S5a_data_driven"),
    ("5b", "S5b_ssr_guard"),
    ("5c", "S5c_ai_render"),
    ("6", "S6_cta"),
]


def _terminal_out(code: str) -> list[dict[str, Any]]:
    """Render a code block as TerminalScene `out` steps (one per line)."""
    return [{"kind": "out", "text": line} for line in code.split("\n")]


# On-screen content for each 04 section, transcribed from 04-script/README.md.
# Keys map to the Remotion `Explainer` Cut props (see src/Explainer.tsx +
# src/custom-templates/scenes/*). `type` selects the scene component.
SCENE_PROPS: dict[str, dict[str, Any]] = {
    "1": {
        "type": "intro_scene",
        "title": "代码即视频（Video-as-Code）",
        "subtitle": "【AI 视频自动化生产线】第 2 期：渲染引擎篇",
        "background": "particles",
    },
    "2a": {
        "type": "concept_scene",
        "eyebrow": "核心概念：范式与痛点",
        "title": "传统剪辑 = 轨道 + 绝对时间轴 → 低 ROI 体力活",
        "background": "gradient",
        "items": [
            {"label": "VERSION", "title": "可版本控制", "desc": "视频就是文本（代码/JSON/YAML），能 diff、能 review、能 git 回滚", "icon": "📝"},
            {"label": "BATCH", "title": "可参数化批量复用", "desc": "同一套模板换一份数据，批量产出几十期结构一致的视频", "icon": "🔁"},
            {"label": "AI", "title": "AI 友好", "desc": "让 AI 拖时间轴很难，让 AI 写代码/改数据/调 CSS 是它最擅长的事", "icon": "🤖"},
        ],
    },
    "2b": {
        "type": "concept_scene",
        "eyebrow": "一句话本质",
        "title": "帧即状态（Frame as State）",
        "background": "gradient",
        "items": [
            {"label": "INPUT", "title": "声明式代码/数据", "desc": "用代码或数据把画面描述出来", "icon": "📄"},
            {"label": "COMPILE", "title": "渲染器编译成帧", "desc": "给定时间点，渲染器算出该时刻画面长什么样", "icon": "⚙️"},
            {"label": "OUTPUT", "title": "合成视频", "desc": "帧序列合成高清 MP4，全流程可自动化", "icon": "🎬"},
        ],
    },
    "2c": {
        "type": "table_scene",
        "eyebrow": "不止 Remotion",
        "title": "Video-as-Code 六条技术路线",
        "background": "grid",
        "headers": ["路线", "代表项目", "典型场景"],
        "rows": [
            {"feature": "DOM / React 渲染", "cursor": "Remotion", "windsurf": "前端栈、复杂排版、模板复用", "win": "neutral"},
            {"feature": "TS 声明式动画", "cursor": "Motion Canvas / Revideo", "windsurf": "代码演示、时序动画", "win": "neutral"},
            {"feature": "程序化数学动画", "cursor": "Manim", "windsurf": "数学/算法可视化", "win": "neutral"},
            {"feature": "像素/合成脚本", "cursor": "MoviePy", "windsurf": "纯 Python、简单拼接", "win": "neutral"},
            {"feature": "Canvas/游戏引擎", "cursor": "PixiJS / Cocos2d", "windsurf": "粒子、游戏化动画", "win": "neutral"},
            {"feature": "命令式合成", "cursor": "FFmpeg + 脚本", "windsurf": "批量转码、字幕烧录", "win": "neutral"},
        ],
    },
    "3a": {
        "type": "table_scene",
        "eyebrow": "判断层 = 边界，非中立百科",
        "title": "六个方案：适用场景 / 已知坑",
        "background": "grid",
        "headers": ["方案", "适用场景", "已知坑"],
        "rows": [
            {"feature": "Remotion", "cursor": "前端栈、复杂 CSS/SVG、跨期模板复用", "windsurf": "顶层读 window/document 崩溃；BUSL 授权", "win": "neutral"},
            {"feature": "Motion Canvas / Revideo", "cursor": "代码演示、精确时序编排", "windsurf": "生态较小，模板需自建", "win": "neutral"},
            {"feature": "Manim", "cursor": "数学/算法/公式可视化", "windsurf": "学习曲线陡、排版弱、渲染慢", "win": "neutral"},
            {"feature": "MoviePy", "cursor": "纯 Python、简单拼接/裁剪", "windsurf": "文本布局繁琐、多层内存大", "win": "neutral"},
            {"feature": "PixiJS / Cocos2d", "cursor": "游戏类复杂粒子动画", "windsurf": "文本换行与 DOM 对齐复杂", "win": "neutral"},
            {"feature": "FFmpeg + 脚本", "cursor": "批量转码、轻量字幕烧录", "windsurf": "filtergraph 晦涩、调试困难", "win": "neutral"},
        ],
    },
    "3b": {
        "type": "concept_scene",
        "eyebrow": "核心约束：固定模板 + AI 接管 + 跨期可维护",
        "title": "为什么选 Remotion？",
        "background": "gradient",
        "items": [
            {"label": "DECISIVE", "title": "数据驱动模板，类型安全跨期复用", "desc": "data.ts → Episode.tsx → template/ 四层结构，TS 保证换数据时格式不出错，改一处主题全期生效", "icon": "🏗️"},
            {"label": "AI+CLI", "title": "AI Agent 友好 + CLI 原生自动化", "desc": "AI 只填数据+微调 CSS，幻觉最小；npx remotion render 纯命令行可 subprocess", "icon": "🤖"},
            {"label": "WEB", "title": "网页生态红利", "desc": "完整 CSS/SVG/Flexbox/动效库随手可用，信息密度与排版自由度远超像素/Canvas 方案", "icon": "🌐"},
        ],
    },
    "3c": {
        "type": "table_scene",
        "eyebrow": "模板复用 + AI 接管维度",
        "title": "Remotion ✅ vs HyperFrames ❌",
        "background": "grid",
        "headers": ["对比维度", "Remotion ✅", "HyperFrames ❌"],
        "rows": [
            {"feature": "模板复用 / 类型安全", "cursor": "TS 约束、跨期安全", "windsurf": "HTML 无类型检查", "win": "cursor"},
            {"feature": "AI 友好度", "cursor": "结构稳定、AI 只填数据", "windsurf": "直接写 HTML，结构易漂移", "win": "cursor"},
            {"feature": "长期维护", "cursor": "改一处全期生效", "windsurf": "10 期后维护困难", "win": "cursor"},
        ],
    },
    "3d": {
        "type": "concept_scene",
        "eyebrow": "如实交代",
        "title": "选型代价（都能兜住）",
        "background": "gradient",
        "items": [
            {"label": "REACT", "title": "基于 React 技术栈", "desc": "本项目让 AI 写组件、填数据，人只把控架构与内容取舍", "icon": "⚛️"},
            {"label": "BUSL", "title": "BUSL 商业授权", "desc": "规模化商用需付费，当前规模无影响", "icon": "📜"},
            {"label": "SSR", "title": "SSR 环境约束", "desc": "Node 端求值读 window 会崩——用一条 MDC 规则交给 AI 自动规避，落地见第五段", "icon": "🛡️"},
        ],
    },
    "4a": {
        "type": "timeline_scene",
        "eyebrow": "流程即代码（Process-as-Code）",
        "title": "七阶段流水线（01 → 07）",
        "background": "grid",
        "events": [
            {"year": "01", "title": "选题分析", "desc": "选题分析师", "icon": "✅"},
            {"year": "02", "title": "内容策划", "desc": "内容策划师", "icon": "✅"},
            {"year": "03", "title": "B站视听策划", "desc": "视觉策划师 · 当前", "icon": "🎬"},
            {"year": "04", "title": "脚本撰写", "desc": "文案撰稿人", "icon": "✍️"},
            {"year": "05", "title": "视频组装", "desc": "视频工程师", "icon": "🛠️"},
            {"year": "06", "title": "分发适配", "desc": "分发助手", "icon": "📤"},
            {"year": "07", "title": "资源归档", "desc": "归档", "icon": "📦"},
        ],
    },
    "4b": {
        "type": "concept_scene",
        "eyebrow": "三件套",
        "title": "角色 × 工作流 × 状态机",
        "background": "gradient",
        "items": [
            {"label": "ROLE", "title": "角色 = system_prompt", "desc": "思考视角与边界（shared/roles/）", "icon": "🎭"},
            {"label": "WORKFLOW", "title": "工作流 = user_prompt", "desc": "每阶段标准步骤（.windsurf/workflows/01→07）", "icon": "📋"},
            {"label": "STATE", "title": "frontmatter = 状态机", "desc": "文件即数据的唯一进度真相源（stage/status + PIPELINE.md）", "icon": "🔄"},
        ],
    },
    "4c": {
        "type": "terminal_scene",
        "terminalTitle": "python-frontmatter 最小编排器",
        "prompt": "$",
        "steps": _terminal_out(
            "import frontmatter, glob\n"
            "\n"
            "for path in glob.glob(\"content-library/**/README.md\", recursive=True):\n"
            "    post = frontmatter.load(path)\n"
            "    if post.get(\"status\") == \"approved\":\n"
            "        stage = post[\"stage\"]\n"
            "        role  = load_role(stage)       # 角色 = system_prompt\n"
            "        steps = load_workflow(stage)   # 工作流 = user_prompt\n"
            "        run_agent(system=role, user=steps)"
        ),
    },
    "4d": {
        "type": "concept_scene",
        "eyebrow": "多模态物理限制",
        "title": "A 轨 vs B 轨 + 提示词链",
        "background": "gradient",
        "items": [
            {"label": "A 轨", "title": "可全自动", "desc": "概念动画由 Remotion 组件渲染，AI 端到端生成数据+套模板，无需人工干预", "icon": "🅰️"},
            {"label": "B 轨", "title": "须真人录屏", "desc": "真实 IDE 录屏，TAD-01 强制真人录制，设计「挂起等待」机制", "icon": "🅱️"},
            {"label": "PROMPT", "title": "可复现提示词链", "desc": "Prompt-1：基于 @ComparisonCard 生成对比数据；Prompt-2：为 .cursor/rules/ 编写 MDC 规则约束", "icon": "⛓️"},
        ],
    },
    "5a": {
        "type": "terminal_scene",
        "terminalTitle": "✅ 只传数据，复用 @ComparisonCard（A 轨兜底）",
        "prompt": "$",
        "steps": _terminal_out(
            "// ✅ 正确示例：数据与模板分离\n"
            "const comparison = {\n"
            "  left:  { title: 'MoviePy',  points: ['纯 Python', '简单拼接'],     status: 'error' },\n"
            "  right: { title: 'Remotion', points: ['TS 类型安全', '模板复用'], status: 'success' },\n"
            "};\n"
            "// <ComparisonCard {...comparison} />  —— 下一期只换数据"
        ),
    },
    "5b": {
        "type": "terminal_scene",
        "terminalTitle": "✅ typeof window 守卫 + MDC 规则（A 轨兜底）",
        "prompt": "$",
        "steps": _terminal_out(
            "// ✅ 类型安全守卫：SSR 时用默认值\n"
            "const getWidth = () =>\n"
            "  typeof window !== 'undefined'\n"
            "    ? window.innerWidth\n"
            "    : 1920;\n"
            "\n"
            "// .cursor/rules/remotion-ssr.mdc:\n"
            "// \"任何 Remotion 组件不得在顶层读 window/document\""
        ),
    },
    "5c": {
        "type": "concept_scene",
        "eyebrow": "这一步怎么交给 AI 做好",
        "title": "人把控架构，AI 干活",
        "background": "gradient",
        "items": [
            {"label": "DATA", "title": "AI 填数据、套现成组件", "desc": "人给出每段要展示什么，AI 按范式产出 data，复用 @ComparisonCard/charts/ 等", "icon": "📊"},
            {"label": "RULE", "title": "用规则替 AI 兜底边界", "desc": "SSR 守卫写进 .cursor/rules/remotion-ssr.mdc，AI 生成组件时自动带", "icon": "🛡️"},
            {"label": "RUN", "title": "渲染命令交给 AI/脚本代跑", "desc": "npx remotion render — 纯命令行，可 CI，人只看产物", "icon": "▶️"},
        ],
    },
    "6": {
        "type": "outro_scene",
        "headline": "代码即视频 + 流程即代码 = 把内容生产做成可维护的工程流水线",
        "cta": "关注 · 下期解密 Whisper 毫秒级字幕与卡点",
        "background": "gradient",
    },
}


def load_segment_durations() -> dict[str, float]:
    data = json.loads(TTS_MANIFEST.read_text(encoding="utf-8"))
    return {seg["segment_id"]: float(seg["duration_seconds"]) for seg in data["segments"]}


def _srt_ts_to_ms(ts: str) -> int:
    # HH:MM:SS,mmm
    hms, ms = ts.strip().split(",")
    h, m, s = hms.split(":")
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)


def _is_cjk(text: str) -> bool:
    glyphs = [c for c in text if not c.isspace()]
    if not glyphs:
        return False
    cjk = sum(1 for c in glyphs if "\u4e00" <= c <= "\u9fff")
    return cjk / len(glyphs) >= 0.3


def load_captions() -> list[dict[str, Any]]:
    """Parse the proofread SRT into one WordCaption per cue.

    Each cue becomes a single {word, startMs, endMs} entry. The Remotion
    `CaptionOverlay` re-paginates using the same break rules as the subtitle
    generator, so feeding whole proofread cues reproduces the published lines.
    """
    raw = PROOFREAD_SRT.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", raw.strip())
    captions: list[dict[str, Any]] = []
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        # find the timing line
        ts_idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if ts_idx is None:
            continue
        start_s, end_s = lines[ts_idx].split("-->")
        text_lines = lines[ts_idx + 1:]
        if not text_lines:
            continue
        sep = "" if _is_cjk("".join(text_lines)) else " "
        text = sep.join(t.strip() for t in text_lines)
        if not text:
            continue
        captions.append({
            "word": text,
            "startMs": _srt_ts_to_ms(start_s),
            "endMs": _srt_ts_to_ms(end_s),
        })
    return captions


def build_cuts(durations: dict[str, float]) -> tuple[list[dict[str, Any]], float]:
    cuts: list[dict[str, Any]] = []
    cursor = 0.0
    for sec_id, seg_id in SECTION_TO_SEGMENT:
        if seg_id not in durations:
            raise SystemExit(f"06 manifest missing duration for segment {seg_id}")
        if sec_id not in SCENE_PROPS:
            raise SystemExit(f"No authored scene props for 04 section {sec_id}")
        # round to whole frames so cuts land on frame boundaries
        frames = int(round(durations[seg_id] * FPS))
        dur = frames / FPS
        props = dict(SCENE_PROPS[sec_id])
        cut = {
            "id": f"scene-{sec_id}",
            "source": "",
            "in_seconds": round(cursor, 3),
            "out_seconds": round(cursor + dur, 3),
            **props,
        }
        cuts.append(cut)
        cursor += dur
    return cuts, cursor


def build_narration_wav(durations: dict[str, float]) -> None:
    """Concatenate the 16 segment wavs (in section order) into one narration."""
    seg_files = [TTS_ASSETS / f"{seg_id}.wav" for _sec, seg_id in SECTION_TO_SEGMENT]
    missing = [str(p) for p in seg_files if not p.exists()]
    if missing:
        raise SystemExit(f"Missing TTS wav(s): {missing}")
    NARRATION_WAV.parent.mkdir(parents=True, exist_ok=True)
    concat_list = NARRATION_WAV.parent / "_ep02_concat.txt"
    concat_list.write_text(
        "".join(f"file '{p.as_posix()}'\n" for p in seg_files), encoding="utf-8"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c", "copy", str(NARRATION_WAV)],
        check=True,
    )
    concat_list.unlink(missing_ok=True)
    print(f"Wrote narration: {NARRATION_WAV}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ep02 Remotion props from SSOT")
    parser.add_argument("--with-audio", action="store_true",
                        help="concat narration wav into public/ and add audio block "
                             "(wav is git-ignored; for full local renders)")
    parser.add_argument("--no-avatar", action="store_true",
                        help="omit the VRM digital host (right-side half-body PiP)")
    args = parser.parse_args()

    durations = load_segment_durations()
    cuts, total = build_cuts(durations)
    captions = load_captions()

    payload: dict[str, Any] = {
        "theme": THEME,
        "cuts": cuts,
        "overlays": [],
        "captions": captions,
    }

    if not args.no_avatar:
        # VRM digital host driven by the caption word-timeline (mouth) + auto
        # blink / breathing. Asset: public/avatars/host-avatar.vrm.
        payload["avatar"] = {"enabled": True, "widthFraction": 0.3}

    if args.with_audio:
        build_narration_wav(durations)
        payload["audio"] = {"narration": {"src": NARRATION_WAV.name, "volume": 1}}

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("=" * 60)
    print(f"Wrote {OUTPUT_JSON.relative_to(REPO_ROOT)}")
    print(f"Cuts: {len(cuts)} | Captions: {len(captions)} | "
          f"Duration: {total:.2f}s ({int(round(total * FPS))} frames @ {FPS}fps)")
    print("Scene types:", ", ".join(f"{c['id']}={c['type']}" for c in cuts))
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
