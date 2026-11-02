// Shareable calculator state in the URL fragment (#...). Browsers never send the
// fragment to the server, so inputs stay on the device unless the user shares the link.

export function readHash(): URLSearchParams {
  return new URLSearchParams(location.hash.replace(/^#/, ""));
}

export function writeHash(params: Record<string, string>): void {
  const q = new URLSearchParams(params).toString();
  history.replaceState(null, "", q ? `#${q}` : location.pathname + location.search);
}

/** Copy the current URL; shows feedback on the button. */
export async function copyLink(button: HTMLButtonElement): Promise<void> {
  const original = button.textContent;
  try {
    await navigator.clipboard.writeText(location.href);
    button.textContent = "Bağlantı kopyalandı ✓";
  } catch {
    window.prompt("Bağlantıyı kopyalayın:", location.href);
  }
  setTimeout(() => (button.textContent = original), 2000);
}
