import test from 'node:test';
import assert from 'node:assert/strict';
import { createApi } from '../src/api.js';

test('all methods use backend paths, exact bodies, and public access', async () => {
  const calls = [];
  const event = { id: 'event', groups: [], expenses: [] };
  const api = createApi('/api', async (url, options) => {
    calls.push({ url, ...options });
    return Response.json(event, { status: options.method === 'POST' ? 201 : 200 });
  });
  const group = { name: 'A', representative: 'A', attendees: [{ name: 'A', categories: [] }] };
  const expense = { description: 'X', amount: 101, category: 'general', groupId: 'a' };
  assert.deepEqual(await api.getEvent('a/b ?'), event);
  assert.deepEqual(await api.createEvent('Picnic', 'MXN'), event);
  assert.deepEqual(await api.addGroup('event', group), event);
  assert.deepEqual(await api.addExpense('event', expense), event);
  assert.deepEqual(await api.createDemo(), event);
  assert.deepEqual(calls.map(c => [c.method, c.url, c.body]), [
    ['GET', '/api/events/a%2Fb%20%3F', undefined],
    ['POST', '/api/events', JSON.stringify({ name: 'Picnic', currency: 'MXN' })],
    ['POST', '/api/events/event/groups', JSON.stringify(group)],
    ['POST', '/api/events/event/expenses', JSON.stringify(expense)],
    ['POST', '/api/events/demo', undefined],
  ]);
  assert.ok(calls.every(c => !c.headers.Authorization && c.cache === 'no-store'));
});

test('backend errors preserve the message displayed by the UI', async () => {
  for (const status of [404, 422, 502]) {
    const api = createApi('/api', async () => Response.json({ message: 'Mensaje del servidor' }, { status }));
    await assert.rejects(api.getEvent('missing'), /Mensaje del servidor/);
  }
});

test('network failures and invalid responses produce understandable errors', async () => {
  const offline = createApi('/api', async () => { throw new TypeError('fetch failed'); });
  await assert.rejects(offline.createDemo(), /No se pudo conectar/);
  const invalid = createApi('/api', async () => new Response('<html>Error</html>', { status: 502 }));
  await assert.rejects(invalid.getEvent('demo'), /respuesta inesperada/);
  const error = createApi('/api', async () => Response.json({}, { status: 500 }));
  await assert.rejects(error.createDemo(), /500/);
});
