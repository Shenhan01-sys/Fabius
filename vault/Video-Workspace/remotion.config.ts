// Remotion CLI settings (studio, still, render). See README.md for the commands.
import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setOverwriteOutput(true);
Config.setPixelFormat('yuv420p');
// Pages draw a lot of SVG and CSS filters: the GPU-less software path is the one that works everywhere.
Config.setChromiumOpenGlRenderer('swangle');
// Machines without network access to Remotion's browser download can point at any Chromium build.
if (process.env.REMOTION_BROWSER_EXECUTABLE) Config.setBrowserExecutable(process.env.REMOTION_BROWSER_EXECUTABLE);
