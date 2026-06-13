import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import {
  AbsoluteFill,
  continueRender,
  delayRender,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import {
  VRM,
  VRMLoaderPlugin,
  VRMUtils,
  VRMExpressionPresetName,
  VRMHumanBoneName,
} from "@pixiv/three-vrm";
import type { WordCaption } from "./CaptionOverlay";

// ---------------------------------------------------------------------------
// Audio-driven mouth (deterministic, derived from the caption word timeline)
// ---------------------------------------------------------------------------
// We do not read the waveform; instead the existing Whisper word-level captions
// ({ word, startMs, endMs }) drive the mouth so it is 100% frame-deterministic
// and stays in sync with the same data that drives the on-screen subtitles.

const VISEMES: VRMExpressionPresetName[] = [
  VRMExpressionPresetName.Aa,
  VRMExpressionPresetName.Ih,
  VRMExpressionPresetName.Ou,
  VRMExpressionPresetName.Ee,
  VRMExpressionPresetName.Oh,
];

// Pick a viseme deterministically from a character's code point so different
// syllables produce visibly different mouth shapes without a pinyin dependency.
function visemeIndexForChar(ch: string): number {
  const code = ch.codePointAt(0) ?? 0;
  return code % VISEMES.length;
}

interface MouthState {
  viseme: VRMExpressionPresetName;
  open: number; // 0..1
}

function mouthStateAt(
  ms: number,
  captions: WordCaption[] | undefined
): MouthState {
  const closed: MouthState = { viseme: VRMExpressionPresetName.Aa, open: 0 };
  if (!captions || captions.length === 0) return closed;

  // Find the word currently being spoken.
  const word = captions.find((w) => ms >= w.startMs && ms < w.endMs);
  if (!word) return closed;

  const chars = Array.from(word.word.replace(/\s+/g, ""));
  if (chars.length === 0) return closed;

  const span = Math.max(1, word.endMs - word.startMs);
  const charDur = span / chars.length;
  const local = ms - word.startMs;
  const charIndex = Math.min(chars.length - 1, Math.floor(local / charDur));
  const within = (local - charIndex * charDur) / charDur; // 0..1 inside char

  // Smooth open/close bump per character → looks like articulating syllables.
  const open = Math.sin(Math.PI * within) * 0.85;
  const viseme = VISEMES[visemeIndexForChar(chars[charIndex])];
  return { viseme, open: Math.max(0, open) };
}

// ---------------------------------------------------------------------------
// Auto-animations (blink / breathing), all pure functions of time
// ---------------------------------------------------------------------------
function blinkAt(timeSec: number): number {
  const period = 4.2; // seconds between blinks
  const dur = 0.13; // blink duration
  const t = timeSec % period;
  if (t > dur) return 0;
  return Math.sin((Math.PI * t) / dur); // 0 → 1 → 0
}

function breathAt(timeSec: number): number {
  const period = 4.8;
  return Math.sin((2 * Math.PI * timeSec) / period); // -1..1
}

// ---------------------------------------------------------------------------
// VRM model — loads the .vrm and drives it from the current Remotion frame
// ---------------------------------------------------------------------------
interface VRMModelProps {
  captions?: WordCaption[];
  /** vertical offset to frame the upper body in the panel */
  modelY?: number;
}

const VRMModel: React.FC<VRMModelProps> = ({ captions, modelY = -0.95 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // R3F render is on-demand (frameloop="never") while Remotion renders, so we
  // must explicitly advance/render once the model has mounted and been posed —
  // otherwise the late (async-loaded) model is never drawn into the framebuffer.
  const advance = useThree((s) => s.advance);

  const [vrm, setVrm] = useState<VRM | null>(null);
  const [handle] = useState(() => delayRender("Loading host-avatar.vrm"));
  const continued = useRef(false);

  useEffect(() => {
    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));
    let disposed = false;
    loader.load(
      staticFile("avatars/host-avatar.vrm"),
      (gltf) => {
        if (disposed) return;
        const loaded = gltf.userData.vrm as VRM;
        // Make VRM0 models face +Z (toward the camera).
        VRMUtils.rotateVRM0(loaded);
        loaded.update(1 / 30);
        loaded.scene.traverse((obj) => {
          obj.frustumCulled = false;
        });
        loaded.scene.updateMatrixWorld(true);
        setVrm(loaded);
      },
      undefined,
      (err) => {
        // eslint-disable-next-line no-console
        console.error("Failed to load VRM:", err);
        continueRender(handle);
        continued.current = true;
      }
    );
    return () => {
      disposed = true;
    };
  }, [handle]);


  // Drive the avatar purely from the current frame (no useFrame / wall clock).
  useLayoutEffect(() => {
    if (!vrm) return;
    const timeSec = frame / fps;
    const ms = timeSec * 1000;

    const em = vrm.expressionManager;
    if (em) {
      // Reset mouth visemes, then apply the active one.
      for (const v of VISEMES) em.setValue(v, 0);
      const mouth = mouthStateAt(ms, captions);
      em.setValue(mouth.viseme, mouth.open);

      // Blink.
      em.setValue(VRMExpressionPresetName.Blink, blinkAt(timeSec));

      // Gentle resting smile so the host looks friendly.
      em.setValue(VRMExpressionPresetName.Happy, 0.12);
    }

    // Lower the arms from the default T-pose into a natural resting pose.
    const h = vrm.humanoid;
    const lUpper = h.getNormalizedBoneNode(VRMHumanBoneName.LeftUpperArm);
    const rUpper = h.getNormalizedBoneNode(VRMHumanBoneName.RightUpperArm);
    const lLower = h.getNormalizedBoneNode(VRMHumanBoneName.LeftLowerArm);
    const rLower = h.getNormalizedBoneNode(VRMHumanBoneName.RightLowerArm);
    const breath = breathAt(timeSec);
    if (lUpper) {
      lUpper.rotation.z = -1.2 - breath * 0.02;
      lUpper.rotation.y = -0.05;
    }
    if (rUpper) {
      rUpper.rotation.z = 1.2 + breath * 0.02;
      rUpper.rotation.y = 0.05;
    }
    if (lLower) lLower.rotation.z = -0.2;
    if (rLower) rLower.rotation.z = 0.2;

    // Breathing + subtle idle sway on the upper spine / chest.
    const chest =
      vrm.humanoid.getNormalizedBoneNode(VRMHumanBoneName.Chest) ??
      vrm.humanoid.getNormalizedBoneNode(VRMHumanBoneName.Spine);
    if (chest) {
      chest.rotation.x = breath * 0.025;
    }
    const head = vrm.humanoid.getNormalizedBoneNode(VRMHumanBoneName.Head);
    if (head) {
      head.rotation.z = Math.sin((2 * Math.PI * timeSec) / 7) * 0.02;
      head.rotation.y = Math.sin((2 * Math.PI * timeSec) / 9) * 0.03;
    }

    // Apply expression morphs + skeleton update for this frame. Keep spring
    // bones at rest so hair does not introduce non-deterministic jitter.
    vrm.update(1 / fps);
    vrm.springBoneManager?.reset();
    vrm.scene.updateMatrixWorld(true);

    // Force an on-demand render now that the model is posed for this frame,
    // then release the frame for capture.
    advance(performance.now());
    if (!continued.current) {
      continueRender(handle);
      continued.current = true;
    }
  }, [vrm, frame, fps, captions, advance, handle]);

  return (
    <>
      {vrm && <primitive object={vrm.scene} position={[0, modelY, 0]} />}
    </>
  );
};

// ---------------------------------------------------------------------------
// Public component — right-side half-body PiP host
// ---------------------------------------------------------------------------
export interface VRMAvatarProps {
  captions?: WordCaption[];
  /** Panel width as a fraction of the composition width. */
  widthFraction?: number;
}

export const VRMAvatar: React.FC<VRMAvatarProps> = ({
  captions,
  widthFraction = 0.3,
}) => {
  const { width, height } = useVideoConfig();
  const panelW = Math.round(width * widthFraction);
  const panelH = height;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", zIndex: 50 }}>
      <div
        style={{
          position: "absolute",
          right: 0,
          bottom: 0,
          width: panelW,
          height: panelH,
        }}
      >
        <ThreeCanvas
          width={panelW}
          height={panelH}
          style={{ background: "transparent" }}
          gl={{ alpha: true, preserveDrawingBuffer: true }}
          camera={{ fov: 30, near: 0.1, far: 20, position: [0, 0, 2.2] }}
        >
          <ambientLight intensity={1.1} />
          <directionalLight position={[1, 2, 2]} intensity={1.4} />
          <directionalLight position={[-1.5, 1, 1.5]} intensity={0.6} />
          <VRMModel captions={captions} />
        </ThreeCanvas>
      </div>
    </AbsoluteFill>
  );
};
