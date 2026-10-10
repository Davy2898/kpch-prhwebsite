import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { createReadStream, statSync } from "node:fs";
import { extname, relative, resolve } from "node:path";

const flaskStaticDir = resolve("app/static");
const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".gif": "image/gif",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".js": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

function flaskStaticPlugin() {
  return {
    name: "flask-static-dev",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (!req.url?.startsWith("/static/")) {
          next();
          return;
        }

        try {
          const pathname = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
          const filePath = resolve(flaskStaticDir, pathname.replace(/^\/static\//, ""));
          const rel = relative(flaskStaticDir, filePath);

          if (rel.startsWith("..") || rel === "") {
            next();
            return;
          }

          const stat = statSync(filePath);
          if (!stat.isFile()) {
            next();
            return;
          }

          res.statusCode = 200;
          res.setHeader("Content-Type", contentTypes[extname(filePath).toLowerCase()] || "application/octet-stream");
          res.setHeader("Cache-Control", "no-cache");
          createReadStream(filePath).pipe(res);
        } catch (error) {
          next();
        }
      });
    },
  };
}

export default defineConfig(({ command }) => ({
  plugins: [vue(), flaskStaticPlugin()],
  root: "frontend",
  base: command === "serve" ? "/" : "/static/vue/",
  server: {
    host: "0.0.0.0",
    allowedHosts: true,
    proxy: {
      "/api": "http://127.0.0.1:5001",
      "/admin": "http://127.0.0.1:5001",
    },
  },
  build: {
    outDir: "../app/static/vue",
    emptyOutDir: true,
    rollupOptions: {
      input: "frontend/src/main.js",
      output: {
        entryFileNames: "assets/app.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith(".css")) {
            return "assets/app.css";
          }
          return "assets/[name][extname]";
        },
      },
    },
  },
}));
