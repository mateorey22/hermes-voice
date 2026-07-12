import path from 'path';
import fs from 'fs';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
        https: {
          key: fs.readFileSync(path.resolve(__dirname, 'certs/key.pem')),
          cert: fs.readFileSync(path.resolve(__dirname, 'certs/cert.pem')),
        },
        proxy: {
          // Hermes API relay (avoids mixed-content HTTPS->HTTP)
          '/hermes': {
            target: 'http://127.0.0.1:8642',
            changeOrigin: true,
            rewrite: (p: string) => p.replace(/^\/hermes/, ''),
          },
          // Relay /mcp requests to the Tailscale HTTPS server
          '/mcp': {
            target: 'https://agentzero.tail335dec.ts.net', // Your Tailscale URL
            changeOrigin: true,
            secure: false, // Accept self-signed or internal Tailscale certs
          }
        }
      },
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(process.cwd(), '.'),
        }
      }
    };
});