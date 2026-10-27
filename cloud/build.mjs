// Kopiert index.html nach public/ und schaltet dabei die Online-Bestenliste ein.
// Wird von wrangler automatisch vor `dev` und `deploy` ausgeführt (siehe wrangler.toml).
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const MARKER = 'const SCORE_API = null;';
const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
if (!html.includes(MARKER)) throw new Error(`Marker "${MARKER}" nicht in index.html gefunden`);

mkdirSync(new URL('./public/', import.meta.url), { recursive: true });
writeFileSync(new URL('./public/index.html', import.meta.url), html.replace(MARKER, "const SCORE_API = '/api/scores';"));
console.log('public/index.html erstellt (Online-Bestenliste aktiv)');
