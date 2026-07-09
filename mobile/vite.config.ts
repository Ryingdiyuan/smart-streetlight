import { defineConfig, loadEnv } from "vite";
import { fileURLToPath, URL } from "node:url";

// @dcloudio/vite-plugin-uni default export is { default: fn }
import UniModule from "@dcloudio/vite-plugin-uni";
const uni = typeof UniModule === "function" ? UniModule : (UniModule as any).default;

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [uni()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    server: {
      host: "0.0.0.0",
      port: 5174,
      proxy: env.VITE_API_PROXY_TARGET
        ? { "/api": { target: env.VITE_API_PROXY_TARGET, changeOrigin: true } }
        : undefined,
    },
  };
});
