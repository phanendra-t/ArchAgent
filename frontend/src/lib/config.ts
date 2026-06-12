export function getApiUrl(): string {
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_ARCHAGENT_API) {
    return process.env.NEXT_PUBLIC_ARCHAGENT_API;
  }
  return "http://localhost:8000";
}

export const API_URL = getApiUrl();
