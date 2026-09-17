import http from 'node:http';
import https from 'node:https';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('.', import.meta.url));
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };

// Keep browser requests same-origin, including when opened from another device.
export function createFrontendServer(backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000') {
  const backend = new URL(backendUrl);
  if (!['http:', 'https:'].includes(backend.protocol)) throw new Error('BACKEND_URL must use HTTP or HTTPS');
  return http.createServer(async (req, res) => {
    const url = new URL(req.url, 'http://localhost');
    if (url.pathname === '/api' || url.pathname.startsWith('/api/')) {
      const transport = backend.protocol === 'https:' ? https : http;
      const upstream = transport.request({
        protocol: backend.protocol, hostname: backend.hostname, port: backend.port,
        path: url.pathname + url.search, method: req.method,
        headers: { ...req.headers, host: backend.host },
      }, response => {
        res.writeHead(response.statusCode, response.headers);
        response.pipe(res);
        response.on('error', () => res.destroy());
      });
      upstream.setTimeout(12000, () => upstream.destroy(new Error('Backend timeout')));
      upstream.on('error', () => {
        if (res.headersSent) { res.destroy(); return; }
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ code: 'backend_unavailable', message: 'El servidor no está disponible. Inténtalo de nuevo en unos momentos.' }));
      });
      req.on('aborted', () => upstream.destroy());
      req.pipe(upstream);
      return;
    }
    try {
      const pathname = decodeURIComponent(url.pathname);
      const file = path.resolve(root, `.${pathname === '/' ? '/index.html' : pathname}`);
      if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
      const body = await readFile(file);
      res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
      res.end(body);
    } catch { res.writeHead(404).end('Not found'); }
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT || 5173);
  createFrontendServer().listen(port, '0.0.0.0', () => console.log(`Chip In: http://localhost:${port}`));
}
