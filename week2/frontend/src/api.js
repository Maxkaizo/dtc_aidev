// Centralized backend access. Event endpoints are public; no bearer token is required.
export function createApi(baseUrl = '/api', fetcher = (...args) => fetch(...args)) {
  async function request(path, body, method = body === undefined ? 'GET' : 'POST') {
    let response;
    try {
      response = await fetcher(`${baseUrl}${path}`, {
        method,
        headers: body === undefined ? { Accept: 'application/json' } : {
          Accept: 'application/json', 'Content-Type': 'application/json',
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        cache: 'no-store',
        signal: AbortSignal.timeout(15000),
      });
    } catch {
      throw new Error('No se pudo conectar con el servidor. Comprueba la conexión e inténtalo de nuevo.');
    }
    let data;
    try { data = await response.json(); }
    catch { throw new Error('El servidor devolvió una respuesta inesperada. Inténtalo de nuevo.'); }
    if (!response.ok) throw new Error(data.message || `No se pudo completar la operación (${response.status}).`);
    return data;
  }
  const eventPath = id => `/events/${encodeURIComponent(id)}`;
  return {
    getEvent: id => request(eventPath(id)),
    createEvent: (name, currency) => request('/events', { name, currency }),
    addGroup: (id, group) => request(`${eventPath(id)}/groups`, group),
    addExpense: (id, expense) => request(`${eventPath(id)}/expenses`, expense),
    // This POST has no body in the contract.
    createDemo: () => request('/events/demo', undefined, 'POST'),
  };
}
export const api = createApi();
