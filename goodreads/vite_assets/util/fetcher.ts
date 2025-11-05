export async function fetcher(
  input: string | URL | globalThis.Request,
  init?: RequestInit,
) {
  const res = await fetch(input, init);
  if (!res.ok) {
    throw new Error(`Fetch error: ${res.status} ${res.statusText}`);
  }
  return await res.json();
}
