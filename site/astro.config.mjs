import { defineConfig } from "astro/config";

// Plain static output; deployable to Cloudflare Pages as-is (build dir: site/dist).
export default defineConfig({
  output: "static",
});
