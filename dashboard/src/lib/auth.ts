const KEY = 'viralai_api_key'

export function getApiKey(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(KEY)
}

export function setApiKey(key: string): void {
  localStorage.setItem(KEY, key)
}

export function removeApiKey(): void {
  localStorage.removeItem(KEY)
}

export function isAuthenticated(): boolean {
  return !!getApiKey()
}
