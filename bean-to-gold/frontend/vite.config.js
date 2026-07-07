import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const workspaceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5180,
    host: '127.0.0.1',
    fs: {
      allow: [workspaceRoot]
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8085',
        changeOrigin: true
      },
      '/triposr/config': {
        target: 'https://stabilityai-triposr.hf.space',
        changeOrigin: true,
        secure: true,
        selfHandleResponse: true,
        rewrite: () => '/config',
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq) => {
            proxyReq.setHeader('accept-encoding', 'identity')
          })
          proxy.on('proxyRes', (proxyRes, req, res) => {
            const chunks = []
            proxyRes.on('data', (chunk) => chunks.push(chunk))
            proxyRes.on('end', () => {
              let body = Buffer.concat(chunks)
              const headers = { ...proxyRes.headers }
              delete headers['content-encoding']

              if (req.url?.startsWith('/config')) {
                try {
                  const config = JSON.parse(body.toString('utf8'))
                  config.root = `http://${req.headers.host}/triposr`
                  body = Buffer.from(JSON.stringify(config))
                  headers['content-type'] = 'application/json'
                } catch {
                  /* keep original response body */
                }
              }

              headers['content-length'] = String(body.length)
              res.writeHead(proxyRes.statusCode || 200, headers)
              res.end(body)
            })
          })
        }
      },
      '/triposr': {
        target: 'https://stabilityai-triposr.hf.space',
        changeOrigin: true,
        secure: true,
        rewrite: (p) => p.replace(/^\/triposr/, '')
      }
    }
  }
})
