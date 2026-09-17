export const categories = [
  { id: 'food', name: 'Comida', icon: '◒', color: 'orange' },
  { id: 'drinks', name: 'Bebidas alcohólicas', icon: '♧', color: 'purple' },
  { id: 'games', name: 'Juegos', icon: '✳', color: 'blue' },
  { id: 'general', name: 'Gastos generales', icon: '⌂', color: 'green' },
];

export function calculate(event) {
  const groups = event.groups.map(g => ({ ...g, paid: 0, share: 0, balance: 0 }));
  const attendees = groups.flatMap(g => g.attendees.map(a => ({ ...a, groupId: g.id })));
  for (const expense of event.expenses) groups.find(g => g.id === expense.groupId).paid += expense.amount;
  const allocation = categories.map(category => {
    const total = event.expenses.filter(e => e.category === category.id).reduce((sum, e) => sum + e.amount, 0);
    const included = attendees.filter(a => category.id === 'general' || a.categories.includes(category.id));
    const base = included.length ? Math.floor(total / included.length) : 0;
    const remainder = included.length ? total % included.length : 0;
    const members = included.map((a, i) => ({ ...a, charge: base + (i < remainder ? 1 : 0), extra: i < remainder }));
    for (const member of members) groups.find(g => g.id === member.groupId).share += member.charge;
    return { ...category, total, base, remainder, members, blocked: total > 0 && !included.length };
  });
  const blocked = allocation.some(c => c.blocked);
  groups.forEach(g => { g.balance = g.paid - g.share; });
  const debtors = groups.filter(g => g.balance < 0).map(g => ({ ...g, remaining: -g.balance }));
  const creditors = groups.filter(g => g.balance > 0).map(g => ({ ...g, remaining: g.balance }));
  const transfers = [];
  if (!blocked) for (const debtor of debtors) for (const creditor of creditors) {
    const amount = Math.min(debtor.remaining, creditor.remaining);
    if (amount) transfers.push({ from: debtor.id, to: creditor.id, amount });
    debtor.remaining -= amount;
    creditor.remaining -= amount;
  }
  return { groups, allocation, transfers, blocked, attendees: attendees.length, total: event.expenses.reduce((s, e) => s + e.amount, 0) };
}
