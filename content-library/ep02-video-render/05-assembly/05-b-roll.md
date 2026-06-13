---
stage: 05-b-roll-recording
status: suspended
source_workflow: /05-b-roll-recording
upstream_inputs:
  - 04-script/README.md (status: approved)
---

# ep02 B 轨录屏（05-b-roll）

> 状态：**suspended（挂起）** —— 本期采用 **A 轨兜底**：04 脚本中所有标注 `[B 轨]` 的录屏镜头都给出了对应的 `[A 轨兜底]` Remotion 画面（`@TerminalScene` + 代码 Props），因此 B 轨录屏暂不录制，整片由 Remotion 全自动渲染。
>
> 本文件是流水线 `05` 槽位（职责 = B 轨录屏素材，workflow `/05-b-roll-recording`）的**唯一**正确产物。历史上曾有一份越权的「视频组装」草稿误占本槽位（旧 `05-assembly/README.md`，已删除）；视频组装的唯一阶段是 `07-assembly`，不在 05。

## 文件约定

- 本阶段文档名为 `05-b-roll.md`，与所在文件夹 `05-assembly/` 同级（沿用历史文件夹名，文档职责以 frontmatter 的 `stage: 05-b-roll-recording` 为准，`pipeline_lint.py` 已支持识别该命名）。
- 若后续补录真实素材，放到 `05-assembly/assets/<clip_id>.mp4`，并把本阶段 `status` 改为 `approved`；`07-assembly` 会用录屏替换对应的 A 轨兜底镜头。

## 需要的 B 轨镜头（逐条映射 04 `b_track_assets_required`，禁改写）

下表 1:1 来自 04 脚本契约块的 `b_track_assets_required`，仅新增「消费段落 / A 轨兜底」两列做可追溯映射，不改写 04 的 `clip_id` 与描述：

| clip_id | 04 描述 | 消费段落（04 section） | A 轨兜底 |
|:--|:--|:--|:--|
| `b-ide-data-driven` | IDE 录屏：数据驱动复用 @ComparisonCard（正面 ✅）+ 从零手写（反面 ❌） | 5a 数据驱动 vs 从零手写 | `@TerminalScene` 渲染代码对比 |
| `b-ide-ssr-guard` | IDE 录屏：SSR window 崩溃 → typeof 守卫 → `.cursor/rules/remotion-ssr.mdc` | 5b SSR 守卫避坑 | `@SplitLayout` + `@TerminalScene` before/after |
| `b-terminal-render` | 终端录屏：`npx remotion render` 执行并输出 MP4（可选，有 A 轨兜底） | 5c 交给 AI + render 出片 | `@TerminalScene` 命令 + 进度动画 |

### 分镜（zoom/crop 指令，逐条保留自 04）

**b-ide-data-driven**
- 0:00–0:15 · zoom 1.0：全貌——打开 data 配置文件
- 0:15–0:30 · zoom 1.3：聚焦——data 对象 left/right 结构
- 0:30–0:45 · zoom 1.2：展示——`<ComparisonCard />` 渲染结果

**b-ide-ssr-guard**
- 0:00–0:10 · zoom 1.0：展示含 `window.innerWidth` 的组件代码
- 0:10–0:20 · zoom 1.4：聚焦终端——`ReferenceError` 红屏
- 0:20–0:30 · zoom 1.3：聚焦代码——`typeof window` 守卫
- 0:30–0:40 · zoom 1.2：展示 `.cursor/rules/remotion-ssr.mdc`

**b-terminal-render**（可选）
- 0:00–0:10 · zoom 1.0：输入命令 `npx remotion render`
- 0:10–0:20 · zoom 1.3：聚焦渲染进度条与帧计数

## 录制纪律（TAD-01）

- B 轨真实 IDE/终端录屏**强制真人录制**，禁止 AIGC 伪造界面。
- 素材到位前本阶段保持 `suspended`，由 A 轨兜底；恢复录制时改回 `draft → approved` 并在 `PIPELINE.md` 同步。

```json
{
  "stage": "05-b-roll-recording",
  "episode": "ep02-video-render",
  "status": "suspended",
  "reason": "A-track fallback covers every [B 轨] shot; no screen recording required this episode",
  "fallback_track": "A",
  "assets_dir": "05-assembly/assets/",
  "assets_present": false,
  "b_track_assets_required": [
    {"clip_id": "b-ide-data-driven", "consumed_by_section": "5a", "fallback": "@TerminalScene"},
    {"clip_id": "b-ide-ssr-guard", "consumed_by_section": "5b", "fallback": "@SplitLayout + @TerminalScene"},
    {"clip_id": "b-terminal-render", "consumed_by_section": "5c", "fallback": "@TerminalScene", "optional": true}
  ]
}
```
