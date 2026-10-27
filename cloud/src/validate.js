// Prüfregeln für Bestenlisten-Einträge (ohne Abhängigkeiten, mit node:test getestet).
// Muss zu den Spielregeln in index.html / snake_core.py passen.

export const GRID_W = 28, GRID_H = 18;
export const MAX_SCORES = 10, NAME_MAX = 16, DEFAULT_NAME = 'Anonym';
export const POINTS_FOOD = 10, POINTS_SPECIAL = 50;
export const START_LENGTH = 3;

const MODE_RE = new RegExp(`^${GRID_W}x${GRID_H}-[01]{3}$`);
export const isValidMode = mode => typeof mode === 'string' && MODE_RE.test(mode);

// Anzahl Hindernis-Zellen wie obstacleLayout() im Spiel
export function obstacleCount(w = GRID_W, h = GRID_H) {
  const xa = Math.floor(w / 5), xb = Math.floor(w * 2 / 5) - 1;
  return 2 * 2 * (xb - xa + 1);
}

// Gleiche Bereinigung wie cleanName() im Spiel
export function cleanName(name) {
  const n = String(name ?? '').replace(/\p{C}/gu, '').split(/\s+/).filter(Boolean).join(' ');
  return [...n].slice(0, NAME_MAX).join('').trim() || DEFAULT_NAME;
}

// Prüft einen Eintrag. Plausibilität: Jedes Futter verlängert um 1 Segment,
// normales Futter bringt 10, Spezialfutter 50 Punkte. Aus Länge und Punkten
// muss sich also eine ganzzahlige Anzahl Spezialfutter ergeben.
export function validateEntry(body) {
  if (!body || typeof body !== 'object') return { error: 'Ungültige Anfrage' };
  const { mode, score, length } = body;
  if (!isValidMode(mode)) return { error: 'Unbekannter Spielmodus' };
  if (!Number.isInteger(score) || !Number.isInteger(length)) return { error: 'Punkte und Länge müssen ganze Zahlen sein' };

  const [, obstacles, special] = mode.slice(-3).split('').map(b => b === '1');   // Bits: Wrap, Hindernisse, Spezial
  const maxLength = GRID_W * GRID_H - (obstacles ? obstacleCount() : 0);
  const eaten = length - START_LENGTH;
  if (score <= 0 || eaten < 1 || length > maxLength) return { error: 'Eintrag nicht plausibel' };

  const extra = score - eaten * POINTS_FOOD;                 // Zusatzpunkte durch Spezialfutter
  const specials = extra / (POINTS_SPECIAL - POINTS_FOOD);
  if (!Number.isInteger(specials) || specials < 0 || specials > eaten || (!special && specials > 0)) {
    return { error: 'Eintrag nicht plausibel' };
  }
  return { entry: { mode, name: cleanName(body.name), score, length } };
}
