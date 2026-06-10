# 代码即视频：用 100 行 React 在「真录屏 + 编译器」流水线里编译卡点与图表动效

## 【AI 视频自动化生产线】第 2 期：渲染引擎篇 · 企业级落地指南（对比稿）

> 📌 **本文性质**：这是 `tutorial.md` 的**对比重写稿**，用于反向打磨「内容策划师」角色与 `02-content-planning` 工作流。
> 它在选题、标题、核心技术结论上与原稿一致，但严格对齐本仓库的三处「真相源」：`CONTENTLIB.md`（TAD-01 混合架构）、`shared/docs/remotion-spec.md`（可用组件清单）、`_decisions/why-remotion-over-hyperframes.md`（数据驱动模板理念）。
> 所有技术结论都显式标注**证据状态**（`verified` / `paper_spec`）与**验收标准**，未经本机渲染验证的一律标 `paper_spec`。

---

## 一、技术背景与痛点：我们到底在自动化什么？

上一期（系列零号期）我们讲清了「AI IDE 三层认知」。从本期开始进入**实操验证篇**，主角是视频自动化生产线的**渲染引擎层**。

但在写一行代码前，必须先纠正一个最容易跑偏的认知（这也是原 `tutorial.md` 的最大隐患）：

> **本频道不是教你"让 AI 从零手写每一期的视频组件"。**
> 根据 `_decisions/why-remotion-over-hyperframes.md` 的已决策结论，本项目的核心是 **「固定模板 + 内容批量替换」（数据驱动模板）**，不是让 Agent 每期自由发挥结构。

因此本期真正要解决的痛点有两个，且**严格分层**：

| 痛点层 | 具体问题 | 本期是否处理 |
| :--- | :--- | :--- |
| **架构层（频道护城河）** | 教程视频必须 100% 真实可信，纯 AIGC 画面会让频道沦为营销号 | ✅ 用 TAD-01 混合架构解决 |
| **渲染层（本期主线）** | 用 React 描述动效时，AI 极易写出在 Node 阶段崩溃的代码（`window is not defined`） | ✅ 用 MDC Rule 被动约束解决 |
| 字幕卡点层 | Whisper 毫秒级时间戳驱动逐字高亮 | ❌ 下期处理，本期只搭好组件接口 |

把这三层拎清楚，标题里的「卡点与图表动效」才有可落地的归宿：**图表动效**用本仓库现成的 `charts/` 组件，**卡点**留到下期由字幕时间轴驱动——本期先把「图表卡片 + 对比动效」这条最短可跑通路径走完。

---

## 二、开源落地方案对比（判断层矩阵）

> 护城河原则（见 `dev-log.md` 对「判断层」的新定义）：**判断层 = 边界与验收 / 避坑指南**，不是中立百科式综述。每个方案必须回答「什么前提下成立 / 哪步会翻车 / 怎么算跑通」。

| 技术维度 | 方案 | 核心渲染机制 | 适用场景 | 不适用场景 | 已知坑 (Pitfall) | 验收标准 | 证据状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 视频代码化 | **Remotion (React)** | 在 Node 端打包并求值 Composition，再由无头 Chrome 逐帧截图，FFmpeg 合成 | 前端技术栈、复杂 CSS/SVG 排版、需类型安全的跨期模板复用 | 零前端基础、纯后台超长批处理 | 模块顶层读取 `window/document` 会在**打包/Composition 求值阶段（Node）**崩溃 | 终端 `render` 正常输出 MP4，无 `ReferenceError` | `verified`（本期验证） |
| 视频代码化 | MoviePy (Python) | NumPy 像素矩阵计算，底层 Imageio/FFmpeg | 纯 Python 环境、简单视频拼接 | 自适应弹性排版、复杂文字动效 | 文本布局繁琐、多层画布内存开销大、无热更新 | 脚本跑完输出拼接视频 | `paper_spec` |
| 视频代码化 | Cocos2d-HTML5 | HTML5 Canvas 上下文逐帧绘制 | 游戏类复杂粒子动画 | 标准网页 UI、文本对齐 | 文本换行与 DOM 对齐计算复杂 | Canvas 正确导出帧序列 | `paper_spec` |
| 模板框架选型 | Remotion vs HyperFrames | TS 类型约束 vs HTML 模板 | 数据驱动、跨期复用 | 每期结构差异极大、需自由布局 | HyperFrames 无类型检查、10 期后维护困难 | 改一处主题全期生效 | `verified`（见决策记录） |

**核心决策**：A 轨（概念动画）全面采用 **Remotion (React)**——唯一能让 Cursor 通过「改数据 + 复用类型化组件」就稳定产出高信息密度视频的方案。

> ⚠️ 与原稿的关键区别：原 `tutorial.md` 的对比表把 MoviePy/Cocos 标了 `paper_spec` 却在正文当作既定事实，本稿把每条结论的**证据状态**和**验收标准**前置，避免「纸面结论当成已验证」。

---

## 三、项目实施路线与架构设计（TAD-01 混合流水线）

这一节是原 `tutorial.md` **完全缺失**、却最重要的一节。脱离了它，读者会误以为「视频 = 自己手写一个 React 组件」。

### 1. 混合架构：真录屏（B 轨）+ 编译器（A 轨）

```
[人工 Human]  ── 手动录制真实 IDE 录屏 (Raw MP4) ──┐
                                                  ▼
[AI Agent]    ── WhisperX 转录 ── 毫秒级字幕 JSON ─►【remotion-composer 编译器】
                                                  │   (载入现成场景组件 + 主题皮肤)
[AI Agent]    ── 生成 JSON/YAML 数据配置 ─────────┘        │
                                                           ▼
                                              [输出 4K/60fps MP4]
```

- **B 轨（不可造假）**：真实 IDE 录屏、报错红屏、终端执行，必须人工录制，在脚本里用 `[B 轨占位：screen_error.mp4]` 显式标注。
- **A 轨（可编译）**：概念图、对比卡片、图表、字幕，由 `OpenMontage/remotion-composer` 用**现成组件**渲染，不手写。

### 2. 用现成组件，而不是从零造组件

`remotion-composer/src/components/` 里已经封装好可直接调用的组件（节选）：

| 组件 | 用途 | 本期用法 |
| :--- | :--- | :--- |
| `@ComparisonCard` | 横向对比卡片 | 「无规则 vs MDC 守卫」左右对比 |
| `@TerminalScene` | 终端模拟器 | 展示 `npx remotion render` 报错/通过 |
| `@ScreenshotScene` | 截图自适应变焦 | 嵌入 Cursor 界面截图并 Zoom |
| `charts/` | 图表卡片 | 标题承诺的「图表动效」 |
| `@CaptionOverlay` | 字幕高亮叠层 | 为下期「卡点」预留接口 |

> 🔑 **这正是「数据驱动模板」理念的落地**：策划阶段我们不设计新组件，只决定「调用哪个现成组件 + 喂什么数据」。原稿教读者手写一个全新的 `ComparisonScene.tsx`，恰好违反了 `why-remotion-over-hyperframes.md` 的决策。

### 3. 证据状态声明

- 本仓库当前**尚无独立 `video/` 工程目录**，A 轨组件位于 `OpenMontage/remotion-composer/`。`remotion-spec.md` 中以 `video/src/template/` 路径描述的组件清单属于**目标态规范**，落地路径以 `remotion-composer` 为准。`status: paper_spec`，需在录制前由执行工程师对齐实际导入路径。

---

## 四、Cursor 提示词链与 MDC Rule 被动约束

自动化的关键不是「手动给 AI 擦屁股」，而是**用规则一次性驯服 AI**，再用**提示词链**驱动它产出。

### 1. Prompt 提示词链（实操可复现）

本期录屏要真实跑通的两段 Prompt（按顺序）：

```text
Prompt-1（生成对比场景数据）：
基于 remotion-composer 现有的 @ComparisonCard 组件，生成一段对比卡片的数据配置，
左卡「无规则约束」、右卡「加入 MDC 守卫」。只产出数据，不要新建组件。
必须保证在 Remotion 的 Node 打包/求值阶段不读取 window/document。

Prompt-2（生成 MDC 规则）：
为 Cursor 在 .cursor/rules/ 下编写一份 mdc 规则，约束我在编写 Remotion 组件时
自动添加浏览器全局对象（window/document/navigator）的 SSR 安全守卫。
```

> 与原稿区别：原稿只给了 MDC 规则，没给**提示词链**；而提示词链正是「第四段录屏」要逐字跑给观众看的核心素材，也是角色定义里要求的 `prompt_sequence`。

### 2. MDC Rule 配置（`.cursor/rules/remotion-ssr.mdc`）

```markdown
---
description: 约束 AI 在编写 Remotion 视频组件时不要引入 Node 阶段崩溃
globs: OpenMontage/remotion-composer/src/**/*.tsx, OpenMontage/remotion-composer/src/**/*.ts
---

# Remotion 浏览器全局对象安全守卫

Remotion 在渲染第一阶段会在 Node 环境打包并求值 Composition 树，
此时 window、document、navigator、localStorage 均不存在。

## 强制要求
1. 禁止在模块顶层作用域、组件外部变量、或 useState 初始值中直接读取浏览器全局对象。
2. 需要视口尺寸时使用类型安全守卫：
   const getWidth = () => (typeof window !== 'undefined' ? window.innerWidth : 1920);
3. 依赖 DOM 的库（Canvas/Lottie）用挂载门控延后初始化：
   const [mounted, setMounted] = useState(false);
   useEffect(() => setMounted(true), []);
   if (!mounted) return null;
```

> ⚠️ **技术精度修正**：原稿说 Remotion「在 Node 下对 React 树进行首轮 SSR 预渲染」。更准确的说法是：Remotion 在 **Node 端打包并求值 Composition 列表**（拿时长/尺寸、做任务拆分），逐帧绘制其实发生在**无头 Chrome**里。崩溃点是「模块/组件求值阶段在 Node 读了浏览器全局对象」，而不是「逐帧 SSR」。这个区别会直接影响读者排查 bug 的方向。

---

## 五、核心避坑卡点与代码实操

### 1. 反面教材：会崩的写法

```tsx
// ❌ Node 打包/求值阶段直接 ReferenceError: window is not defined
const screenWidth = window.innerWidth;
const isChrome = navigator.userAgent.includes('Chrome');

export const MyScene = () => { /* ... */ };
```

### 2. 正确写法：100 行内的安全对比场景

> 说明：下面是**示意实现**，用于讲清「守卫 + spring + interpolate」三件套。生产中应优先用 `@ComparisonCard` 传数据，而非粘贴此组件。

```tsx
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import React, { useEffect, useState } from 'react';

export const ComparisonScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // SSR 安全守卫：未挂载到真实浏览器前不触碰 DOM
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  // 弹簧物理动画：spring 返回 0→1 的归一化进度
  const progress = spring({ frame, fps, config: { damping: 15, stiffness: 100, mass: 1 } });
  const translateY = interpolate(progress, [0, 1], [100, 0]); // 由 100px 弹回 0
  const opacity = interpolate(progress, [0, 1], [0, 1]);

  if (!mounted) {
    return <div style={{ backgroundColor: '#0f172a', width: '100%', height: '100%' }} />;
  }

  return (
    <div style={{
      width: '100%', height: '100%', backgroundColor: '#0f172a',
      display: 'flex', flexDirection: 'column', justifyContent: 'center',
      alignItems: 'center', fontFamily: 'system-ui, sans-serif',
    }}>
      <h1 style={{ color: '#f8fafc', fontSize: 72, marginBottom: 40, opacity, transform: `translateY(${translateY}px)` }}>
        MDC 被动约束对比
      </h1>
      <div style={{ display: 'flex', gap: 40, width: '80%', maxWidth: 1200 }}>
        <div style={{ flex: 1, backgroundColor: '#1e293b', borderRadius: 16, padding: 40, border: '2px solid #ef4444', transform: `scale(${progress})` }}>
          <h2 style={{ color: '#ef4444', fontSize: 36, marginBottom: 20 }}>无规则约束 ⚠️</h2>
          <p style={{ color: '#94a3b8', fontSize: 24, lineHeight: 1.6 }}>
            AI 易在组件求值阶段读取 window，导致 Node 端 ReferenceError 崩溃。
          </p>
        </div>
        <div style={{ flex: 1, backgroundColor: '#1e293b', borderRadius: 16, padding: 40, border: '2px solid #10b981', transform: `scale(${progress})`, boxShadow: '0 0 20px rgba(16,185,129,0.3)' }}>
          <h2 style={{ color: '#10b981', fontSize: 36, marginBottom: 20 }}>加入 MDC 守卫 ✅</h2>
          <p style={{ color: '#94a3b8', fontSize: 24, lineHeight: 1.6 }}>
            规则约束下 AI 自动补齐安全守卫，渲染顺利产出 MP4。
          </p>
        </div>
      </div>
    </div>
  );
};
```

### 3. 验收标准与待验证假设

| # | 假设 / 命令 | 验收标准 | 证据状态 |
| :--- | :--- | :--- | :--- |
| 1 | 顶层用 `typeof window === 'undefined'` 守卫能否 100% 规避 Node 端报错 | 在外层写 `window` 读取并套守卫，`render` 控制台零报错且正常出片 | `paper_spec`（录制前实测） |
| 2 | `spring` 在 60fps 下是否平滑不抖 | 配 60fps Composition，出片后逐帧检查缩放无突变 | `paper_spec`（录制前实测） |
| 3 | `@ComparisonCard` 传数据能否替代手写组件 | 仅改 data 配置即渲染出左右对比卡片 | `paper_spec`（录制前实测） |

启动预览 / 渲染（路径以 `remotion-composer` 为准，录制前需对齐 composition id）：

```bash
# 进入编译器工程
cd OpenMontage/remotion-composer

# 启动 Remotion Studio 可视化调试
npx remotion studio

# 渲染指定 composition 为 MP4（<CompositionId> 录制前确认）
npx remotion render src/index.ts <CompositionId> out/comparison.mp4
```

> ⚠️ 与原稿区别：原稿用 `npx remotion render src/index.ts ComparisonScene ...` 暗示「一键可渲染」，但本仓库并无对应工程与该 composition。本稿据实把命令标为 `paper_spec` 并要求录制前对齐，避免给观众演示一个跑不通的命令。

---

## 六、下游交付提示（给 03 视听编排 / 04 脚本）

为了让本稿直接「可拍」，按 `remotion-spec.md` 的防静止（Anti-Deadtime）红线预埋节拍：

- 第二段（原理，≈2 分钟）：口播超 15 秒的段落，配 `@ScreenshotScene` Zoom + 文字逐行高亮，避免单镜头静止超 450 帧。
- 第三段（SSR 翻车）：`[B 轨占位：screen_error.mp4]` 真实红屏录屏，禁止用 AIGC 伪报错。
- 第四段（对比）：`@ComparisonCard`（A 轨）+ 左右 `[B 轨占位：no-rule.mp4 / with-rule.mp4]` 真录屏。

---

## 七、总结

- **架构先于代码**：先讲清 TAD-01「真录屏 + 编译器」混合流水线，再讲渲染层细节——这是原稿缺失的灵魂。
- **数据驱动模板**：复用 `@ComparisonCard` 等现成组件喂数据，而非从零手写组件。
- **帧即状态**：掌握 `useCurrentFrame` → `spring/interpolate` 的数学映射。
- **规则驯服 AI**：用一条 MDC Rule 被动封杀 `window is not defined`，并配套可复现的 Prompt 提示词链。
- **据实标注**：每条结论带证据状态与验收标准，未实测一律 `paper_spec`。

下一期我们攻克「字幕与卡点」：用 Whisper 拿到毫秒级时间戳 JSON，驱动本期预留的 `@CaptionOverlay` 接口，做逐字高亮卡点。
