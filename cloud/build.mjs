// Kopiert index.html nach public/ und passt sie für den Online-Betrieb an:
//  - Online-Bestenliste einschalten (SCORE_API)
//  - Design-Auswahl und ?theme=-Testparameter ausblenden (online folgt das Design immer dem Datum)
// Wird von wrangler automatisch vor `dev` und `deploy` ausgeführt (siehe wrangler.toml).
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const REPLACEMENTS = [
  ['const SCORE_API = null;', "const SCORE_API = '/api/scores';"],
  ['const THEME_PICKER = true;', 'const THEME_PICKER = false;'],
];

let html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
for (const [marker, value] of REPLACEMENTS) {
  if (!html.includes(marker)) throw new Error(`Marker "${marker}" nicht in index.html gefunden`);
  html = html.replace(marker, value);
}

mkdirSync(new URL('./public/', import.meta.url), { recursive: true });
writeFileSync(new URL('./public/index.html', import.meta.url), html);
console.log('public/index.html erstellt (Online-Bestenliste aktiv, Design-Auswahl ausgeblendet)');
