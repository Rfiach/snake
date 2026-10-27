// Snake auf Cloudflare: liefert das Spiel aus (statische Assets) und die Bestenlisten-API.
//   GET  /api/scores?mode=28x18-001   → { list }
//   POST /api/scores  { mode, name, score, length }   → { list, rank }
import { MAX_SCORES, isValidMode, validateEntry } from './validate.js';

const RATE_LIMIT = 5;          // Einträge pro Minute und Absender
const MAX_BODY = 1024;         // Bytes

const json = (data, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
});

async function top(env, mode) {
  const { results } = await env.DB.prepare(
    'SELECT id, name, score, length, date FROM scores WHERE mode = ?1 ORDER BY score DESC, id ASC LIMIT ?2',
  ).bind(mode, MAX_SCORES).all();
  return results;
}

const strip = rows => rows.map(({ id, ...e }) => e);   // interne ID nicht ausliefern

// IP nur gehasht speichern (für das Rate-Limit)
async function clientHash(req) {
  const ip = req.headers.get('CF-Connecting-IP') || 'local';
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('snake:' + ip));
  return [...new Uint8Array(digest)].slice(0, 16).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function getScores(url, env) {
  const mode = url.searchParams.get('mode') || '';
  if (!isValidMode(mode)) return json({ error: 'Unbekannter Spielmodus' }, 400);
  return json({ list: strip(await top(env, mode)) });
}

async function postScore(req, env) {
  const text = await req.text();
  if (text.length > MAX_BODY) return json({ error: 'Anfrage zu groß' }, 413);
  let body;
  try { body = JSON.parse(text); } catch { return json({ error: 'Ungültige Anfrage' }, 400); }
  const { entry, error } = validateEntry(body);
  if (error) return json({ error }, 400);

  const now = Math.floor(Date.now() / 1000), who = await clientHash(req);
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM submissions WHERE ip_hash = ?1 AND created_at > ?2')
    .bind(who, now - 60).first();
  if (n >= RATE_LIMIT) return json({ error: 'Zu viele Einträge – bitte kurz warten.' }, 429);

  const date = new Date().toISOString().slice(0, 10);
  const [, , inserted] = await env.DB.batch([
    env.DB.prepare('INSERT INTO submissions (ip_hash, created_at) VALUES (?1, ?2)').bind(who, now),
    env.DB.prepare('DELETE FROM submissions WHERE created_at < ?1').bind(now - 86400),
    env.DB.prepare('INSERT INTO scores (mode, name, score, length, date) VALUES (?1, ?2, ?3, ?4, ?5) RETURNING id')
      .bind(entry.mode, entry.name, entry.score, entry.length, date),
    // Nur die Top 10 je Modus aufbewahren
    env.DB.prepare(`DELETE FROM scores WHERE mode = ?1 AND id NOT IN
      (SELECT id FROM scores WHERE mode = ?1 ORDER BY score DESC, id ASC LIMIT ?2)`).bind(entry.mode, MAX_SCORES),
  ]);
  const id = inserted.results[0].id;
  const list = await top(env, entry.mode);
  const rank = list.findIndex(e => e.id === id);
  return json({ list: strip(list), rank: rank < 0 ? null : rank });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === '/api/scores') {
      try {
        if (req.method === 'GET') return await getScores(url, env);
        if (req.method === 'POST') return await postScore(req, env);
        return json({ error: 'Methode nicht erlaubt' }, 405);
      } catch (err) {
        console.error(err);
        return json({ error: 'Serverfehler' }, 500);
      }
    }
    return env.ASSETS.fetch(req);
  },
};
