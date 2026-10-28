// Remotion CLI settings (studio, still, render). See README.md for the commands.
import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setOverwriteOutput(true);
Config.setPixelFormat('yuv420p');
// WebGL (the 3D ports in src/three, @remotion/effects) needs the GPU: ANGLE on Windows (D3D11). Machines without a GPU:
// REMOTION_GL=swangle (software, slow but works everywhere).
Config.setChromiumOpenGlRenderer((process.env.REMOTION_GL as 'angle' | 'swangle' | undefined) ?? 'angle');
// Machines without network access to Remotion's browser download can point at any Chromium build.
if (process.env.REMOTION_BROWSER_EXECUTABLE) Config.setBrowserExecutable(process.env.REMOTION_BROWSER_EXECUTABLE);
