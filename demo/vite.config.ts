import { defineConfig } from "vite";

export default defineConfig({
  base: "./", // works from any folder, e.g. GitHub Pages under /quote-distill/
  server: { fs: { allow: [".."] } }, // the sample quotations are read from ../data/pilot
  optimizeDeps: { exclude: ["@huggingface/transformers"] }, // keeps onnxruntime-web's wasm files resolvable
});
