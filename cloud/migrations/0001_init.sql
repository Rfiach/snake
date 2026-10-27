-- Bestenliste: je Modus werden nur die Top 10 aufbewahrt (siehe worker.js)
CREATE TABLE scores (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  mode   TEXT    NOT NULL,          -- z. B. '28x18-001' (Feldgröße + Bits Wrap/Hindernisse/Spezial)
  name   TEXT    NOT NULL,
  score  INTEGER NOT NULL,
  length INTEGER NOT NULL,
  date   TEXT    NOT NULL           -- YYYY-MM-DD
);
CREATE INDEX scores_rank ON scores (mode, score DESC, id);

-- Für das Rate-Limit; IP nur als Hash, Einträge älter als 1 Tag werden gelöscht
CREATE TABLE submissions (
  ip_hash    TEXT    NOT NULL,
  created_at INTEGER NOT NULL       -- Unix-Zeit in Sekunden
);
CREATE INDEX submissions_by_ip ON submissions (ip_hash, created_at);
