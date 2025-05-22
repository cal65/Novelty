export async function fetcher(
  input: string | URL | globalThis.Request,
  init?: RequestInit,
) {
  const res = await fetch(input, init);
  return await res.json();
}
