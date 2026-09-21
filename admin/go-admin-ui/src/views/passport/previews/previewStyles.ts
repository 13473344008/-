// Vite rewrites width media queries into range syntax in production builds.
// Match both forms so the preview follows its own width, not the browser window.
export function previewStyles(css: string) {
  return css
    .replace(/@media\s*\(\s*(?:max-width\s*:\s*699px|width\s*<=\s*699px)\s*\)/g, '@container passportviewport (max-width:699px)')
    .replace(/@media\s*\(\s*(?:min-width\s*:\s*700px|width\s*>=\s*700px)\s*\)/g, '@container passportviewport (min-width:700px)')
}
