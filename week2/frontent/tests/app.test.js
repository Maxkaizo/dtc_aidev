import test from 'node:test';
import assert from 'node:assert/strict';
import { calculate } from '../src/calculations.js';
import { api } from '../src/api.js';
const storage = new Map();
globalThis.localStorage = { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value) };

test('spec example allocates 990 and settles Luis to Ana for 40', async () => {
  const event = await api.createDemo();
  const result = calculate(event);
  assert.equal(result.total, 99000);
  assert.deepEqual(result.groups.map(g => [g.paid, g.share, g.balance]), [[70000, 66000, 4000], [29000, 33000, -4000]]);
  assert.deepEqual(result.transfers, [{ from: 'luis', to: 'ana', amount: 4000 }]);
  assert.deepEqual(result.allocation.map(c => c.members.reduce((s, m) => s + m.charge, 0)), [60000, 20000, 10000, 9000]);
});

test('mock API persists groups, includes general automatically, and saves expenses', async () => {
  let event = await api.createEvent('Test event', 'EUR');
  event = await api.addGroup(event.id, { name: 'Solo', representative: 'Alex', attendees: [{ name: 'Alex', categories: ['food'] }] });
  const groupId = event.groups[0].id;
  assert.deepEqual(event.groups[0].attendees[0].categories, ['food', 'general']);
  event = await api.addExpense(event.id, { description: 'Lunch', amount: 1234, category: 'food', groupId });
  assert.deepEqual(await api.getEvent(event.id), event);
  assert.equal(calculate(event).groups[0].share, 1234);
  assert.equal(calculate(event).transfers.length, 0);
  event.name = 'Unsaved mutation';
  assert.equal((await api.getEvent(event.id)).name, 'Test event');
});

test('leftover cents go to included attendees in registration order', async () => {
  const event = await api.createDemo();
  event.expenses = [{ description: 'Test', amount: 101, category: 'general', groupId: 'luis' }];
  const result = calculate(event);
  assert.deepEqual(result.allocation[3].members.map(m => [m.charge, m.extra]), [[34, true], [34, true], [33, false]]);
  assert.deepEqual(result.groups.map(g => g.share), [68, 33]);
  assert.deepEqual(result.transfers, [{ from: 'ana', to: 'luis', amount: 68 }]);
});

test('unpopulated expense category blocks settlement until a participant is registered', async () => {
  let event = await api.createEvent('Games', 'MXN');
  event = await api.addGroup(event.id, { name: 'A', representative: 'A', attendees: [{ name: 'A', categories: [] }] });
  event = await api.addExpense(event.id, { description: 'Game', amount: 100, category: 'games', groupId: event.groups[0].id });
  assert.equal(calculate(event).blocked, true);
  assert.deepEqual(calculate(event).transfers, []);
  event = await api.addGroup(event.id, { name: 'B', representative: 'B', attendees: [{ name: 'B', categories: ['games'] }] });
  assert.equal(calculate(event).blocked, false);
  assert.equal(calculate(event).transfers[0].amount, 100);
});

test('allocations conserve cents and transfers settle every group across varying totals', async () => {
  for (let amount = 1; amount < 150; amount++) {
    const event = await api.createDemo();
    event.expenses = event.expenses.map((e, i) => ({ ...e, amount: amount * (i + 1) }));
    const result = calculate(event);
    assert.equal(result.groups.reduce((s, g) => s + g.share, 0), result.total);
    assert.equal(result.groups.reduce((s, g) => s + g.paid, 0), result.total);
    const balances = Object.fromEntries(result.groups.map(g => [g.id, g.balance]));
    for (const t of result.transfers) { balances[t.from] += t.amount; balances[t.to] -= t.amount; }
    assert.ok(Object.values(balances).every(b => b === 0));
  }
});

test('invalid amounts and unknown events are rejected', async () => {
  const event = await api.createDemo();
  for (const amount of [0, -1, 1.5, NaN, Infinity]) {
    await assert.rejects(api.addExpense(event.id, { description: 'Invalid', amount, category: 'food', groupId: 'ana' }));
  }
  await assert.rejects(api.getEvent('missing'));
  assert.equal(calculate({ groups: [], expenses: [] }).total, 0);
});
