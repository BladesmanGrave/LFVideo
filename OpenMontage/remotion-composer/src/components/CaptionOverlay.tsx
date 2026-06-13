import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Word-level caption for TikTok-style highlight display
export interface WordCaption {
  word: string;
  startMs: number;
  endMs: number;
}

interface CaptionOverlayProps {
  words: WordCaption[];
  // Hard cap on words per page (Latin scripts); CJK is governed by chars.
  wordsPerPage?: number;
  // Max characters per page before forcing a break (Latin / CJK).
  maxCharsLatin?: number;
  maxCharsCjk?: number;
  // Silence gap (ms) between words that triggers a natural break.
  pauseThresholdMs?: number;
  // Max on-screen duration (ms) for a single page.
  maxDurationMs?: number;
  fontSize?: number;
  color?: string;
  highlightColor?: string;
  backgroundColor?: string;
  fontFamily?: string;
}

interface CaptionPage {
  words: WordCaption[];
  startMs: number;
  endMs: number;
}

// Punctuation that ends a sentence (strong break) / clause (soft break).
// Kept in sync with tools/subtitle/subtitle_gen.py so the burned-in captions
// segment identically to the generated SRT/VTT files.
const SENTENCE_END = new Set([".", "!", "?", "…", "。", "！", "？"]);
const CLAUSE_END = new Set([",", ";", ":", "，", "、", "；", "："]);

function isCJKText(text: string): boolean {
  const glyphs = [...text].filter((c) => !/\s/.test(c));
  if (glyphs.length === 0) return false;
  const cjk = glyphs.filter((c) => /[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uac00-\ud7a3]/.test(c)).length;
  return cjk / glyphs.length >= 0.3;
}

interface PageBreakOptions {
  wordsPerPage: number;
  maxCharsLatin: number;
  maxCharsCjk: number;
  pauseThresholdMs: number;
  maxDurationMs: number;
  maxLines: number;
}

function buildPages(words: WordCaption[], opts: PageBreakOptions): CaptionPage[] {
  if (words.length === 0) return [];
  const cjk = isCJKText(words.map((w) => w.word).join(""));
  const join = (items: WordCaption[]) =>
    cjk
      ? items.map((w) => w.word.trim()).join("")
      : items.map((w) => w.word.trim()).join(" ");
  const charLimit = (cjk ? opts.maxCharsCjk : opts.maxCharsLatin) * Math.max(opts.maxLines, 1);

  const pages: CaptionPage[] = [];
  let buf: WordCaption[] = [];
  const flush = () => {
    if (buf.length === 0) return;
    pages.push({
      words: buf,
      startMs: buf[0].startMs,
      endMs: buf[buf.length - 1].endMs,
    });
    buf = [];
  };

  for (let i = 0; i < words.length; i++) {
    const w = words[i];
    const wtext = w.word.trim();

    if (buf.length > 0) {
      const overWords = !cjk && buf.length >= opts.wordsPerPage;
      const overChars = join([...buf, w]).length > charLimit;
      const overTime = w.endMs - buf[0].startMs > opts.maxDurationMs;
      if (overWords || overChars || overTime) flush();
    }

    buf.push(w);
    if (i === words.length - 1) break;

    const trailing = wtext.slice(-1);
    const gap = words[i + 1].startMs - w.endMs;
    if (SENTENCE_END.has(trailing)) {
      flush();
    } else if (gap >= opts.pauseThresholdMs && buf.length >= 2) {
      flush();
    } else if (CLAUSE_END.has(trailing) && join(buf).length >= charLimit * 0.6) {
      flush();
    }
  }
  flush();
  return pages;
}

const PageRenderer: React.FC<{
  page: CaptionPage;
  fontSize: number;
  color: string;
  highlightColor: string;
  backgroundColor: string;
  fontFamily: string;
}> = ({ page, fontSize, color, highlightColor, backgroundColor, fontFamily }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentMs = page.startMs + (frame / fps) * 1000;
  // CJK scripts are written without spaces between glyphs.
  const cjk = isCJKText(page.words.map((w) => w.word).join(""));
  const wordSep = cjk ? "" : " ";

  // Spring entrance
  const entrance = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 120 },
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 80,
      }}
    >
      <div
        style={{
          opacity: entrance,
          transform: `translateY(${interpolate(entrance, [0, 1], [20, 0])}px)`,
          backgroundColor,
          borderRadius: 12,
          padding: "14px 28px",
          maxWidth: "80%",
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontSize,
            fontWeight: 700,
            fontFamily,
            lineHeight: 1.4,
            whiteSpace: "pre-wrap",
          }}
        >
          {page.words.map((w, i) => {
            const isActive = w.startMs <= currentMs && w.endMs > currentMs;
            const isPast = w.endMs <= currentMs;
            return (
              <span
                key={`${w.startMs}-${i}`}
                style={{
                  color: isActive ? highlightColor : isPast ? color : `${color}99`,
                  transition: "none", // CSS transitions forbidden in Remotion
                  textShadow: isActive
                    ? `0 0 20px ${highlightColor}66, 0 2px 4px rgba(0,0,0,0.5)`
                    : "0 2px 4px rgba(0,0,0,0.5)",
                }}
              >
                {w.word}{i < page.words.length - 1 ? wordSep : ""}
              </span>
            );
          })}
        </span>
      </div>
    </AbsoluteFill>
  );
};

export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  words,
  wordsPerPage = 6,
  maxCharsLatin = 42,
  maxCharsCjk = 20,
  pauseThresholdMs = 500,
  maxDurationMs = 6000,
  fontSize = 42,
  color = "#F8FAFC",
  highlightColor = "#22D3EE",
  backgroundColor = "rgba(15, 23, 42, 0.75)",
  fontFamily = "Space Grotesk, Inter, system-ui, sans-serif",
}) => {
  const { fps } = useVideoConfig();
  const pages = buildPages(words, {
    wordsPerPage,
    maxCharsLatin,
    maxCharsCjk,
    pauseThresholdMs,
    maxDurationMs,
    maxLines: 2,
  });

  return (
    <AbsoluteFill>
      {pages.map((page, i) => {
        const fromFrame = Math.round((page.startMs / 1000) * fps);
        const nextStart = pages[i + 1]?.startMs ?? page.endMs + 500;
        const duration = Math.max(
          1,
          Math.round(((nextStart - page.startMs) / 1000) * fps)
        );

        return (
          <Sequence key={i} from={fromFrame} durationInFrames={duration}>
            <PageRenderer
              page={page}
              fontSize={fontSize}
              color={color}
              highlightColor={highlightColor}
              backgroundColor={backgroundColor}
              fontFamily={fontFamily}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
