-- Verdächtig hohe Einträge (siehe needsReview() in validate.js) werden gespeichert,
-- aber erst nach Freigabe angezeigt: review = 1 → wartet auf Prüfung
ALTER TABLE scores ADD COLUMN review INTEGER NOT NULL DEFAULT 0;
