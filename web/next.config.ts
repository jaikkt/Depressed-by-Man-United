import path from "node:path";
import type { NextConfig } from "next";

// Static export: the whole site is plain HTML/JS/JSON, so it runs from any
// static host (or `npx serve out`) with no server. All data is pre-computed
// by the Python pipeline into public/data/*.json.
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  // Pin the workspace root so a stray lockfile in a parent folder can't confuse Turbopack.
  turbopack: { root: path.resolve(__dirname) },
};

export default nextConfig;
