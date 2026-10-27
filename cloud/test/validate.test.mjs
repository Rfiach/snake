// Ausführen: node --test cloud/test
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { cleanName, obstacleCount, validateEntry } from '../src/validate.js';

const ok = body => assert.ok(validateEntry(body).entry, JSON.stringify(body));
const bad = body => assert.ok(validateEntry(body).error, JSON.stringify(body));

test('plausible Einträge', () => {
  ok({ mode: '28x18-000', name: 'Max', score: 10, length: 4 });           // 1 Futter
  ok({ mode: '28x18-001', name: 'Max', score: 50, length: 4 });           // 1 Spezialfutter
  ok({ mode: '28x18-001', name: 'Max', score: 90, length: 8 });           // 4 normal + 1 Spezial
});

test('unplausible Einträge', () => {
  bad({ mode: '28x18-000', score: 50, length: 4 });                       // Spezialfutter ohne Option
  bad({ mode: '28x18-001', score: 999999, length: 10 });
  bad({ mode: '28x18-001', score: 15, length: 4 });
  bad({ mode: '28x18-001', score: 0, length: 3 });
  bad({ mode: '28x18-001', score: 10, length: 1000 });
  bad({ mode: '28x18-001', score: 10.5, length: 4 });
  bad({ mode: '20x20-001', score: 10, length: 4 });
  bad({ mode: "28x18-001' OR 1=1", score: 10, length: 4 });
  bad(null);
});

test('maximale Länge mit Hindernissen', () => {
  const max = 28 * 18 - obstacleCount();
  assert.equal(obstacleCount(), 24);
  ok({ mode: '28x18-010', score: (max - 3) * 10, length: max });
  bad({ mode: '28x18-010', score: (max - 2) * 10, length: max + 1 });
});

test('Namen werden bereinigt', () => {
  assert.equal(cleanName('  Max   Muster \n'), 'Max Muster');
  assert.equal(cleanName('\t\x00 '), 'Anonym');
  assert.equal(cleanName('x'.repeat(50)).length, 16);
  assert.equal(validateEntry({ mode: '28x18-000', name: 42, score: 10, length: 4 }).entry.name, '42');
});
