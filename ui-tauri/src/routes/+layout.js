// Tauri doesn't have a Node.js server to do proper SSR
// so we use adapter-static with a fallback to index.html to put the site in SPA mode
// See SvelteKit docs for single-page apps
// See Tauri docs for SvelteKit frontend info
export const ssr = false;
