import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.png"],
      manifest: {
        name: "Payme",
        short_name: "Payme",
        description: "Stripe Connect payment platform",
        theme_color: "#0ea5e9",
        background_color: "#f8fafc",
        display: "standalone",
        icons: [
          {
            src: "favicon.png",
            sizes: "any",
            type: "image/png+xml"
          }
        ]
      }
    })
  ],
  server: {
    port: 5173
  }
});
