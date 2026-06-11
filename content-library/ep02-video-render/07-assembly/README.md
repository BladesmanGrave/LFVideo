---
stage: 07-video-assembly
status: draft
source_workflow: /07-video-assembly
upstream_inputs:
  - 04-script/README.md (status: approved)
  - 05-b-roll/assets/ (status: suspended — A轨兜底)
  - 06-tts/assets/ (status: approved)
  - shared/docs/remotion-spec.md
---

# ep02 视频组装方案

## 制作概要

| 维度 | 值 |
|------|---|
| **轨道** | A 轨为主（概念动画全自动），B 轨挂起（A 轨兜底） |
| **时长** | ~10:45（基于 06-TTS 合成 553.82s + 画面过渡） |
| **分辨率** | 1920×1080 @ 30fps（B站 16:9 主版本） |
| **复用模板** | IntroScene / OutroScene / ConceptScene / TableScene / TimelineScene / SplitLayout / TerminalScene |
| **新增组件** | 无（全复用 remotion-spec.md §1.9 已有组件） |

---

## Remotion 结构（场景编排表）

| # | 时间区间 | 场景 | 组件 | 数据来源 | 轨道 |
|---|---------|------|------|---------|------|
| 1 | 0:00–0:30 | 开头钩子 | `@IntroScene` | S1_intro.wav + title/subtitle props | A |
| 2 | 0:30–1:13 | 范式与痛点 | `@ConceptScene` | S2a_paradigm.wav + bullet_points | A |
| 3 | 1:13–1:34 | 帧即状态 | `@ConceptScene` | S2b_frame_as_state.wav + diagram_data | A |
| 4 | 1:34–2:18 | 六条路线 | `@TableScene` | S2c_six_routes.wav + matrix_data | A |
| 5 | 2:18–3:19 | 判断层矩阵 | `@TableScene` | S3a_judgment_matrix.wav + evaluation_data | A |
| 6 | 3:19–4:00 | 选型四理由 | `@ConceptScene` | S3b_remotion_reasons.wav + reasons_list | A |
| 7 | 4:00–4:21 | Remotion vs HyperFrames | `@SplitLayout(@ComparisonCard)` | S3c_comparison.wav + comparison_data | A |
| 8 | 4:21–4:49 | 选型代价 | `@ConceptScene` | S3d_tradeoffs.wav + tradeoff_points | A |
| 9 | 4:49–5:20 | 七阶段流水线 | `@TimelineScene` | S4a_pipeline.wav + stages_array | A |
| 10 | 5:20–5:44 | 三件套 | `@ConceptScene` | S4b_three_piece.wav + three_piece_data | A |
| 11 | 5:44–6:08 | 编排器伪代码 | `@TerminalScene` | S4c_orchestrator.wav + code_snippet | A |
| 12 | 6:08–6:49 | A/B轨机制 | `@SplitLayout` | S4d_ab_track.wav + ab_comparison | A |
| 13 | 6:49–7:23 | 数据驱动 vs 手写 | `@SplitLayout(@ComparisonCard)` | S5a_data_driven.wav + code_comparison | A (B轨兜底) |
| 14 | 7:23–8:06 | SSR守卫 | `@SplitLayout` + `@TerminalScene` | S5b_ssr_guard.wav + guard_code | A (B轨兜底) |
| 15 | 8:06–8:45 | AI出片 | `@ConceptScene` + `@TerminalScene` | S5c_ai_render.wav + render_commands | A (B轨兜底) |
| 16 | 8:45–9:18 | 结尾CTA | `@OutroScene` | S6_cta.wav + cta_props | A |

> 时间区间基于 TTS 合成时长 + 2s 场景过渡。总计约 9:18 纯内容 + 过渡 ≈ 10:00。

---

## data.ts 结构设计

```typescript
// video/src/episodes/ep02-video-render/data.ts

import type { EpisodeData, SceneConfig } from '../../template';

export const ep02Data: EpisodeData = {
  meta: {
    id: 'ep02-video-render',
    title: '代码即视频（Video-as-Code）',
    subtitle: '【AI 视频自动化生产线】第 2 期：渲染引擎篇',
    fps: 30,
    width: 1920,
    height: 1080,
  },
  audio: {
    // TTS 合成音频，按段落 ID 对应
    segments: [
      { id: 'S1_intro', file: './assets/S1_intro.wav', startSec: 0 },
      { id: 'S2a_paradigm', file: './assets/S2a_paradigm.wav', startSec: 30 },
      { id: 'S2b_frame_as_state', file: './assets/S2b_frame_as_state.wav', startSec: 73 },
      { id: 'S2c_six_routes', file: './assets/S2c_six_routes.wav', startSec: 94 },
      { id: 'S3a_judgment_matrix', file: './assets/S3a_judgment_matrix.wav', startSec: 138 },
      { id: 'S3b_remotion_reasons', file: './assets/S3b_remotion_reasons.wav', startSec: 199 },
      { id: 'S3c_comparison', file: './assets/S3c_comparison.wav', startSec: 240 },
      { id: 'S3d_tradeoffs', file: './assets/S3d_tradeoffs.wav', startSec: 261 },
      { id: 'S4a_pipeline', file: './assets/S4a_pipeline.wav', startSec: 289 },
      { id: 'S4b_three_piece', file: './assets/S4b_three_piece.wav', startSec: 320 },
      { id: 'S4c_orchestrator', file: './assets/S4c_orchestrator.wav', startSec: 344 },
      { id: 'S4d_ab_track', file: './assets/S4d_ab_track.wav', startSec: 368 },
      { id: 'S5a_data_driven', file: './assets/S5a_data_driven.wav', startSec: 409 },
      { id: 'S5b_ssr_guard', file: './assets/S5b_ssr_guard.wav', startSec: 443 },
      { id: 'S5c_ai_render', file: './assets/S5c_ai_render.wav', startSec: 486 },
      { id: 'S6_cta', file: './assets/S6_cta.wav', startSec: 525 },
    ],
  },
  scenes: [
    {
      id: 'S1',
      component: 'IntroScene',
      durationSec: 30,
      props: {
        title: '代码即视频（Video-as-Code）',
        subtitle: '【AI 视频自动化生产线】第 2 期：渲染引擎篇',
        background: 'particles',
      },
    },
    {
      id: 'S2a',
      component: 'ConceptScene',
      durationSec: 43,
      props: {
        heading: '传统剪辑 vs Video-as-Code',
        bullets: [
          '传统：轨道 + 绝对时间轴 → 低 ROI 体力活',
          'VaC 三特性：可版本控制 / 可参数化批量复用 / AI 友好',
        ],
        animation: 'fade_bullet_sequence',
      },
    },
    {
      id: 'S2b',
      component: 'ConceptScene',
      durationSec: 21,
      props: {
        heading: '帧即状态（Frame as State）',
        diagram: 'code_data → renderer → frames → video',
        animation: 'flow_diagram',
      },
    },
    {
      id: 'S2c',
      component: 'TableScene',
      durationSec: 44,
      props: {
        title: '六条技术路线',
        columns: ['路线', '描述层', '渲染层', '适用场景'],
        rows: [
          ['Remotion', 'React/TSX', 'Puppeteer截图', '复杂排版+模板复用'],
          ['Motion Canvas', 'TypeScript', '声明式动画', '代码演示+时序'],
          ['Manim', 'Python', '几何渲染', '数学可视化'],
          ['MoviePy', 'Python', 'NumPy+FFmpeg', '简单拼接'],
          ['PixiJS/Cocos', 'JS/TS', 'Canvas', '粒子/游戏效果'],
          ['FFmpeg', 'CLI', 'filtergraph', '批量转码/字幕'],
        ],
        highlight_row: 0,
      },
    },
    {
      id: 'S3a',
      component: 'TableScene',
      durationSec: 60,
      props: {
        title: '判断层矩阵',
        columns: ['方案', '适用', '不适用/坑'],
        rows: [
          ['Remotion', '前端栈复杂排版、跨期模板', '零前端基础、window顶层读取、BUSL'],
          ['Motion Canvas', '时序动画', '网页级Flex排版'],
          ['Manim', '数学可视化', '学习曲线陡、排版弱'],
          ['MoviePy', '简单拼接', '复杂文字动效'],
          ['PixiJS', '游戏级粒子', '文本对齐'],
          ['FFmpeg', '批量转码', 'filtergraph可读性'],
        ],
      },
    },
    {
      id: 'S3b',
      component: 'ConceptScene',
      durationSec: 42,
      props: {
        heading: 'Remotion 胜出四理由',
        bullets: [
          '① 数据驱动模板（决定性）— 类型安全跨期复用',
          '② AI 友好 — 只填数据和微调CSS',
          '③ CLI 原生 — npx remotion render 一行出片',
          '④ 网页生态红利 — CSS/SVG/Flexbox 随手可用',
        ],
        animation: 'number_highlight_sequence',
      },
    },
    {
      id: 'S3c',
      component: 'SplitLayout',
      durationSec: 21,
      props: {
        left: { component: 'ComparisonCard', title: 'Remotion ✅', points: ['TypeScript约束', '跨期类型安全', 'AI只填数据'] },
        right: { component: 'ComparisonCard', title: 'HyperFrames ❌', points: ['HTML无类型', '结构漂移', '维护灾难'] },
      },
    },
    {
      id: 'S3d',
      component: 'ConceptScene',
      durationSec: 28,
      props: {
        heading: '选型代价（如实交代）',
        bullets: [
          'React技术栈 → AI写组件，人把控架构',
          'BUSL商业授权 → 当前规模无影响',
          'SSR环境约束 → MDC规则一次封死',
        ],
        animation: 'cross_fade',
      },
    },
    {
      id: 'S4a',
      component: 'TimelineScene',
      durationSec: 31,
      props: {
        title: '七阶段生产流水线',
        stages: ['01 选题', '02 策划', '03 视听', '04 脚本', '05 组装', '06 分发', '07 归档'],
        active_stage: 4,
        animation: 'sequential_highlight',
      },
    },
    {
      id: 'S4b',
      component: 'ConceptScene',
      durationSec: 24,
      props: {
        heading: '三件套',
        bullets: [
          '角色 = system_prompt',
          '工作流 = user_prompt',
          'frontmatter = 状态机',
        ],
        animation: 'stack_build',
      },
    },
    {
      id: 'S4c',
      component: 'TerminalScene',
      durationSec: 24,
      props: {
        title: '最小编排器伪代码',
        language: 'python',
        code: `import frontmatter\nfor doc in glob("content-library/**/README.md"):\n  meta = frontmatter.load(doc)\n  if meta["status"] == "approved":\n    next_stage = get_next(meta["stage"])\n    role = load_role(next_stage)\n    workflow = load_workflow(next_stage)\n    llm.run(system=role, user=workflow)`,
        typing_speed: 'medium',
      },
    },
    {
      id: 'S4d',
      component: 'SplitLayout',
      durationSec: 41,
      props: {
        left: { title: 'A轨（全自动）', description: 'AI生成数据 → Remotion渲染 → 零人工' },
        right: { title: 'B轨（真人录屏）', description: 'TAD-01 强制真录 → 挂起等待 → 素材到位后合成' },
      },
    },
    {
      id: 'S5a',
      component: 'SplitLayout',
      durationSec: 33,
      props: {
        left: { component: 'ComparisonCard', title: '❌ 从零手写', points: ['新建ComparisonScene.tsx', '手写布局/样式/动画', '违反模板复用原则'] },
        right: { component: 'ComparisonCard', title: '✅ 数据驱动', points: ['产出data对象', '丢给ComparisonCard', '下期只换数据'] },
        fallback: 'TerminalScene',
      },
    },
    {
      id: 'S5b',
      component: 'SplitLayout',
      durationSec: 43,
      props: {
        left: { title: '❌ 顶层读 window', code: 'const w = window.innerWidth // Node崩溃' },
        right: { title: '✅ typeof 守卫', code: "const w = typeof window !== 'undefined' ? window.innerWidth : 1920" },
        fallback: 'TerminalScene',
      },
    },
    {
      id: 'S5c',
      component: 'ConceptScene',
      durationSec: 40,
      props: {
        heading: '交给 AI 做好',
        bullets: [
          '① 填数据 + 套现成组件',
          '② 规则替AI兜底（MDC自动守卫）',
          '③ 渲染命令代跑（npx remotion render）',
        ],
        sub_component: 'TerminalScene',
        sub_props: { code: 'npx remotion render --composition=ep02-video-render', typing_speed: 'fast' },
      },
    },
    {
      id: 'S6',
      component: 'OutroScene',
      durationSec: 33,
      props: {
        summary: '代码即视频 + 流程即代码 = 工程流水线',
        cta: '开源仓库在简介，自取',
        next_episode: '下期：Whisper 毫秒级字幕卡点',
        subscribe_text: '关注，别错过',
      },
    },
  ],
};
```

---

## Episode.tsx 骨架

```tsx
// video/src/episodes/ep02-video-render/Episode.tsx

import { Sequence, Audio, staticFile } from 'remotion';
import {
  IntroScene, OutroScene, ConceptScene,
  TableScene, TimelineScene, TerminalScene,
  SplitLayout, ComparisonCard,
} from '../../template';
import { ep02Data } from './data';

const FPS = 30;

export const Ep02Episode: React.FC = () => {
  const { scenes, audio } = ep02Data;
  let currentFrame = 0;

  return (
    <>
      {/* 音频轨 — 连续播放所有 TTS 段落 */}
      {audio.segments.map((seg) => (
        <Sequence key={seg.id} from={Math.round(seg.startSec * FPS)}>
          <Audio src={staticFile(seg.file)} />
        </Sequence>
      ))}

      {/* 画面轨 — 按场景编排顺序 */}
      {scenes.map((scene) => {
        const from = currentFrame;
        const dur = Math.round(scene.durationSec * FPS);
        currentFrame += dur;
        return (
          <Sequence key={scene.id} from={from} durationInFrames={dur}>
            {/* 根据 scene.component 渲染对应组件 */}
            <SceneRouter component={scene.component} props={scene.props} />
          </Sequence>
        );
      })}
    </>
  );
};
```

---

## 渲染命令

```bash
# 开发预览
cd video && npx remotion studio

# 渲染 16:9 主版本
npx remotion render --composition=ep02-video-render --output=out/ep02-video-render.mp4

# 渲染 9:16 竖版（可选）
npx remotion render --composition=ep02-video-render-vertical --output=out/ep02-video-render-vertical.mp4
```

---

## 需人工提供的素材（B 轨）

> 05 B轨录屏阶段当前 `suspended`，以下 B 轨素材使用 A 轨兜底：

| 素材 ID | 描述 | A 轨兜底方案 |
|---------|------|------------|
| b-ide-data-driven | IDE 录屏：数据驱动复用 @ComparisonCard | `@TerminalScene` 渲染代码对比 |
| b-ide-ssr-guard | IDE 录屏：typeof window 守卫 | `@TerminalScene` 渲染 before/after |
| b-terminal-render | 终端录屏：npx remotion render 出片 | `@TerminalScene` 渲染命令 + 进度输出 |

---

## 产出路径

```
video/src/episodes/ep02-video-render/
├── data.ts          # 文案与组件配置数据
├── Episode.tsx      # 场景组装入口
└── assets/          # TTS 音频（从 06-tts/assets/ 复制或 symlink）
    ├── S1_intro.wav
    ├── ...
    └── S6_cta.wav

video/out/
└── ep02-video-render.mp4  # 渲染成片（待 Remotion 工程就绪后产出）
```

---

## 当前状态

- Remotion 工程（`video/`）**尚未初始化**，本文件为组装规划
- 待 Remotion 工程搭建后，按本方案执行 `data.ts` + `Episode.tsx` 编写
- A 轨场景可全自动渲染；B 轨等待 05 解除挂起后补入真实录屏

```json
{
  "stage": "07-video-assembly",
  "episode": "ep02-video-render",
  "total_scenes": 16,
  "total_duration_seconds": 558,
  "track_breakdown": {
    "a_track_only": 13,
    "a_track_with_b_fallback": 3
  },
  "components_used": [
    "IntroScene", "OutroScene", "ConceptScene", "TableScene",
    "TimelineScene", "TerminalScene", "SplitLayout", "ComparisonCard"
  ],
  "new_components_required": 0,
  "remotion_project_status": "not_initialized",
  "render_ready": false,
  "blocking_on": "Remotion project initialization (video/ directory)"
}
```
