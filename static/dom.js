// static-src/dom.ts
export function qs(selector, root = document) {
    return root.querySelector(selector);
}
export function qsa(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
}
export function byId(id) {
    return document.getElementById(id);
}
// Sonar-safe typed wrappers (use unknown bridge to avoid S4325)
export function qsT(selector, root = document) {
    return root.querySelector(selector);
}
export function qsaT(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
}
export function byIdT(id) {
    return document.getElementById(id);
}
