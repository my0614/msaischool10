import AsyncStorage from '@react-native-async-storage/async-storage';

const AUTH_TOKEN_KEY = 'auth:token';

export function getAuthToken() {
  return AsyncStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAuthToken(token: string) {
  return AsyncStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearAuthToken() {
  return AsyncStorage.removeItem(AUTH_TOKEN_KEY);
}

export async function authHeaders(): Promise<Record<string, string>> {
  const token = await getAuthToken();
  return token ? { Authorization: `Token ${token}` } : {};
}
