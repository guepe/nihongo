// Client of the PHP API (api/ at the root of the repository), served on the same domain.

export interface User {
  id: number
  name: string
  email: string
  is_admin: boolean
}

export interface Session {
  token: string
  user: User
}

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message)
  }
}

/** Calls the API. Throws ApiError, with status 0 when the server can't be reached. */
export async function api<T>(method: string, path: string, body?: unknown, token?: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api/${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        // Custom header: OVH doesn't pass "Authorization" to PHP.
        ...(token ? { 'X-Hachi-Token': token } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'Pas de connexion au serveur')
  }
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new ApiError(response.status, data.error ?? `Erreur ${response.status}`)
  return data as T
}
