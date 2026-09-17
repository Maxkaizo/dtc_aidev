// Run with npm run test:integration; requires uv and the backend dependencies.
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import { createFrontendServer } from '../server.js';
import { createApi } from '../src/api.js';
import { calculate } from '../src/calculations.js';

const port = process.env.INTEGRATION_BACKEND_PORT || '18080';
const backendUrl = `http://127.0.0.1:${port}`;
const databaseDir = await mkdtemp(path.join(tmpdir(), 'chip-in-integration-'));
const databaseUrl = `sqlite:///${path.join(databaseDir, 'test.db')}`;
const backend = spawn('uv', ['run', '--locked', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', port], {
  env: { ...process.env, DATABASE_URL: databaseUrl },
  cwd: fileURLToPath(new URL('../../backend/', import.meta.url)), stdio: ['ignore', 'pipe', 'pipe'],
});
let output = '', spawnError;
backend.stdout.on('data', chunk => { output += chunk; });
backend.stderr.on('data', chunk => { output += chunk; });
backend.on('error', error => { spawnError = error; });
const exited = once(backend, 'close').catch(() => {});
const server = createFrontendServer(backendUrl);
try {
  let ready = false;
  for (let i = 0; i < 100; i++) {
    if (spawnError || backend.exitCode !== null) throw new Error(output || String(spawnError));
    if (output.includes('Uvicorn running')) {
      try { ready = (await fetch(`${backendUrl}/api/events/demo`)).ok; } catch {}
    }
    if (ready) break;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.ok(ready, `Backend did not start: ${output}`);
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const origin = `http://127.0.0.1:${server.address().port}`;
  assert.equal((await fetch(origin)).status, 200);
  const api = createApi(`${origin}/api`);
  assert.equal(calculate(await api.getEvent('demo')).total, 99000);
  const demo = await api.createDemo();
  assert.deepEqual(calculate(demo).transfers, [{ from: 'luis', to: 'ana', amount: 4000 }]);
  let event = await api.createEvent('Integration picnic', 'MXN');
  event = await api.addGroup(event.id, {
    name: 'A', representative: 'Ana', attendees: [{ name: 'Ana', categories: ['food'] }],
  });
  assert.deepEqual(event.groups[0].attendees[0].categories, ['food', 'general']);
  event = await api.addExpense(event.id, {
    description: 'Lunch', amount: 1234, category: 'food', groupId: event.groups[0].id,
  });
  // A fresh client has no local browser state and still gets the same saved event.
  assert.deepEqual(await createApi(`${origin}/api`).getEvent(event.id), event);
  await assert.rejects(api.addExpense(event.id, {
    description: 'Invalid', amount: -1, category: 'food', groupId: event.groups[0].id,
  }), /Revisa los datos/);
  await assert.rejects(api.getEvent('missing'), /No se encontró/);
  backend.kill('SIGTERM');
  await exited;
  await assert.rejects(api.getEvent(event.id), /servidor no está disponible/);
  console.log('Integration passed: all 5 API operations, proxy, fresh-client reload, settlement, validation, missing events, backend offline.');
} finally {
  server.closeAllConnections();
  if (server.listening) await new Promise(resolve => server.close(resolve));
  if (backend.exitCode === null && !spawnError) backend.kill('SIGTERM');
  await exited;
  await rm(databaseDir, { recursive: true, force: true });
}
