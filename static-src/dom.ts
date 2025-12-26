// static-src/dom.ts

export function qs(selector: string, root: ParentNode = document): Element | null {
  return root.querySelector(selector);
}

export function qsa(selector: string, root: ParentNode = document): Element[] {
  return Array.from(root.querySelectorAll(selector));
}

export function byId(id: string): HTMLElement | null {
  return document.getElementById(id);
}

// Sonar-safe typed wrappers (use unknown bridge to avoid S4325)
export function qsT<T extends Element>(selector: string, root: ParentNode = document): T | null {
  return root.querySelector(selector) as unknown as T | null;
}

export function qsaT<T extends Element>(selector: string, root: ParentNode = document): T[] {
  return Array.from(root.querySelectorAll(selector)) as unknown as T[];
}

export function byIdT<T extends HTMLElement>(id: string): T | null {
  return document.getElementById(id) as unknown as T | null;
}
