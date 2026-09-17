import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { calculate } from '../src/calculations.js';
const fixture = JSON.parse(readFileSync(new URL('./fixtures/demo.json', import.meta.url)));
const demo = () => structuredClone(fixture);

test('spec example allocates 990 and settles Luis to Ana for 40', () => {
  const result = calculate(demo());
  assert.equal(result.total, 99000);
  assert.deepEqual(result.groups.map(g => [g.paid, g.share, g.balance]), [[70000, 66000, 4000], [29000, 33000, -4000]]);
  assert.deepEqual(result.transfers, [{ from: 'luis', to: 'ana', amount: 4000 }]);
});

test('leftover cents follow registration order', () => {
  const event = demo();
  event.expenses = [{ amount: 101, category: 'general', groupId: 'luis' }];
  const result = calculate(event);
  assert.deepEqual(result.allocation[3].members.map(m => [m.charge, m.extra]), [[34, true], [34, true], [33, false]]);
  assert.deepEqual(result.transfers, [{ from: 'ana', to: 'luis', amount: 68 }]);
});

test('unpopulated category blocks settlement until participants are present', () => {
  const event = demo();
  event.groups.forEach(g => g.attendees.forEach(a => { a.categories = a.categories.filter(c => c !== 'games'); }));
  assert.equal(calculate(event).blocked, true);
  assert.deepEqual(calculate(event).transfers, []);
  event.groups[0].attendees[0].categories.push('games');
  assert.equal(calculate(event).blocked, false);
});

test('allocation and settlement conserve cents across varying totals', () => {
  for (let amount = 1; amount < 150; amount++) {
    const event = demo();
    event.expenses = event.expenses.map((e, i) => ({ ...e, amount: amount * (i + 1) }));
    const result = calculate(event);
    assert.equal(result.groups.reduce((s, g) => s + g.share, 0), result.total);
    const balances = Object.fromEntries(result.groups.map(g => [g.id, g.balance]));
    for (const t of result.transfers) { balances[t.from] += t.amount; balances[t.to] -= t.amount; }
    assert.ok(Object.values(balances).every(b => b === 0));
  }
});
