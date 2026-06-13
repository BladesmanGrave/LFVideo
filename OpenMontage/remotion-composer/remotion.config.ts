import { Config } from "@remotion/cli/config";

// Three.js / WebGL needs the ANGLE renderer for correct, deterministic
// offline rendering of the VRM avatar (see @remotion/three docs).
Config.setChromiumOpenGlRenderer("angle");
