// All data access lives here. Replace these methods with HTTP calls when the backend is ready.
// Mock shared links reference localStorage, so data is available only in this browser.
const prefix = 'chip-in:event:';
const clone = value => structuredClone(value);
const id = () => crypto.randomUUID();
function read(eventId) {
  const raw = localStorage.getItem(prefix + eventId);
  if (!raw) throw new Error('Este evento no está guardado en este navegador. Crea uno nuevo o abre el enlace en el navegador original.');
  return JSON.parse(raw);
}
function save(event) {
  localStorage.setItem(prefix + event.id, JSON.stringify(event));
  return clone(event);
}
export const api = {
  async getEvent(eventId) { return clone(read(eventId)); },
  async createEvent(name, currency) {
    if (!name.trim() || !['MXN', 'USD', 'EUR'].includes(currency)) throw new Error('Revisa el nombre y la moneda.');
    return save({ id: id(), name: name.trim(), currency, groups: [], expenses: [] });
  },
  async addGroup(eventId, group) {
    const event = read(eventId);
    if (!group.name.trim() || !group.representative.trim() || !group.attendees.length || group.attendees.some(a => !a.name.trim())) throw new Error('Completa el grupo, representante y asistentes.');
    event.groups.push({ ...clone(group), id: id(), attendees: group.attendees.map(a => ({ ...a, id: id(), categories: [...new Set([...a.categories, 'general'])] })) });
    return save(event);
  },
  async addExpense(eventId, expense) {
    const event = read(eventId);
    if (!expense.description.trim() || !Number.isSafeInteger(expense.amount) || expense.amount <= 0 || expense.amount > 10000000000 || !event.groups.some(g => g.id === expense.groupId) || !['food', 'drinks', 'games', 'general'].includes(expense.category)) throw new Error('Revisa los datos del gasto.');
    if (!Number.isSafeInteger(event.expenses.reduce((s, e) => s + e.amount, expense.amount))) throw new Error('El total excede el límite permitido.');
    event.expenses.push({ ...expense, id: id() });
    return save(event);
  },
  async createDemo() {
    const event = { id: id(), name: 'Domingo entre amigos', currency: 'MXN', groups: [
      { id: 'ana', name: 'Familia de Ana', representative: 'Ana', attendees: [{ id: 'a', name: 'Ana', categories: ['food', 'drinks', 'general'] }, { id: 'b', name: 'Peque de Ana', categories: ['food', 'games', 'general'] }] },
      { id: 'luis', name: 'Luis', representative: 'Luis', attendees: [{ id: 'c', name: 'Luis', categories: ['food', 'drinks', 'general'] }] },
    ], expenses: [
      { id: '1', description: 'Comida para compartir', category: 'food', amount: 60000, groupId: 'ana' },
      { id: '2', description: 'Bebidas para brindar', category: 'drinks', amount: 20000, groupId: 'luis' },
      { id: '3', description: 'Actividad para peques', category: 'games', amount: 10000, groupId: 'ana' },
      { id: '4', description: 'Servilletas', category: 'general', amount: 9000, groupId: 'luis' },
    ] };
    return save(event);
  },
};
