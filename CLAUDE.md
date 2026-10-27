# Projekt: Snake – Kontext

Dieses Dokument beschreibt Spielgedanke, Regeln und Umsetzungsanforderungen. Es gilt als verbindlicher Kontext für alle Arbeiten in diesem Projekt.

## Hintergrund
- Ursprung: Arcade-Spiel *Blockade* (Gremlin, 1976, 2 Spieler).
- Populär durch Nokia-Handys ab 1998.
- Genre: Geschicklichkeitsspiel (Reaktion, räumliches Denken).

## Spielgedanke
Der Spieler steuert eine Schlange, die sich ständig weiterbewegt. Ziel: möglichst viel Futter fressen. Jedes Futter verlängert die Schlange und bringt Punkte. Dadurch wird es auf dem Feld immer enger, und das Spiel wird von selbst schwerer. Game Over bei Kollision mit Wand oder eigenem Körper.

## Kernregeln
- **Spielfeld:** Raster aus festen Zellen; Bewegung Zelle für Zelle.
- **Bewegung:** automatisch in festen Zeitschritten; der Spieler ändert nur die Richtung (Pfeiltasten / WASD).
- **Futter:** immer auf einer freien Zelle. Fressen bedeutet: +1 Segment, Punkte, neues Futter an zufälliger freier Stelle.
- **Game Over:** Kopf trifft Wand oder eigenen Körper.
- **Schwierigkeit:** Länge wächst, optional steigt das Tempo.

## Umsetzungsanforderungen (Pflicht)
1. **Keine 180°-Umkehr:** Eine Eingabe in die Gegenrichtung der aktuellen Bewegung wird ignoriert.
2. **Eingabepuffer:** Eingaben kommen in eine Warteschlange, maximal eine Richtungsänderung pro Spielschritt. Schnelle Doppeleingaben dürfen keine Selbstkollision auslösen.
3. **Feste Spielschritte:** Spiellogik unabhängig von der Bildrate.
4. **Ablauf pro Schritt:** neuen Kopf berechnen → Kollision prüfen → Futter? dann wachsen : Schwanz entfernen.
5. **Schwanz-Sonderfall:** Der Kopf darf in die Zelle ziehen, die der Schwanz im selben Schritt verlässt, aber nur wenn die Schlange nicht wächst.
6. **Futter-Spawn:** nur auf freien Zellen, nie auf der Schlange.
7. **Gewinnbedingung:** Feld komplett gefüllt bedeutet „gewonnen“ (kein Absturz und kein Endlos-Suchen nach freier Zelle).
8. **Zustände:** Start, Läuft, Pause, Game Over, (Gewonnen), Neustart. Der Neustart setzt Schlange, Punkte und Tempo zurück.
9. **Rückmeldung:** Punkte und Highscore sichtbar, Kopf klar erkennbar, deutliches Game-Over-Signal.

## Optionale Varianten
- Wrap-around: durch die Wand auf der Gegenseite wieder herauskommen
- Hindernisse / Labyrinthe (vgl. *Nibbler*, 1982)
- Spezialfutter (Bonus, Zeitlimit)
- 2-Spieler-Modus (vgl. *Blockade*)
- Tempostufen / Level

## Entscheidungen
- Hauptversion: Python mit pygame.
  - `snake_core.py`: reine Spiellogik (`Game`), ohne pygame, getestet in `test_snake_core.py` (unittest).
  - `snake.py`: pygame-Oberfläche, Loop mit festen Schritten, Eingabe, Overlays. Optionen per Taste 1/2/3 vor dem Start. Bestenliste in `highscore.json`.
- Browser-Version `index.html` (HTML/JS, Canvas) mit gleichem Funktionsumfang; Logik im `<script id="core">`.
- Bestenliste: Top 10 je Feldgröße und Optionskombination (Name, Punkte, Länge, Datum). Logik (`clean_name`, `qualifies`, `insert_score`) im Kern beider Versionen. Namensabfrage nur, wenn die Punkte für die Liste reichen; Name wird nur für die Session gemerkt (pygame: Laufzeit, Browser: `sessionStorage`). Anzeige per Taste H. Browser speichert über `ScoreStore` (async): online über `SCORE_API`, sonst bzw. bei Serverausfall `localStorage`. pygame bleibt rein lokal.
- Online: Cloudflare Worker + D1 in `cloud/` (Worker liefert auch das Spiel aus). `cloud/build.mjs` kopiert `index.html` nach `cloud/public/` und setzt `SCORE_API`. Server prüft Plausibilität (`cloud/src/validate.js`) – bei Regeländerungen (Punkte, Startlänge, Feldgröße, Hindernisse) dort mitziehen.
- Spielfeld: 28 × 18 Zellen (Querformat), in beiden Versionen gleich. pygame-Fenster 932 × 804 px (passt auf 1536 × 912 nutzbare Fläche bei 150 % Skalierung). Highscore getrennt je Feldgröße.
- Varianten im Umfang: Basisspiel + Wrap-around, Spezialfutter, Hindernisse (je als Option umschaltbar).
- Darstellung: Schlange in Regenbogenfarben (durchlaufend), Kopf weiß mit Regenbogen-Rand, rot bei Game Over.
- Hintergrund: 8 Weltraum-Bilder (`assets/bg_01..08.png`, generiert mit `tools/make_backgrounds.py`). Wechsel zum nächsten Bild bei jedem gefressenen Futter (normal + Spezial), 400 ms Überblendung, Abdunklung + feines Raster für Lesbarkeit. Fallback ohne Bilder: Schachbrett.
  - In `index.html` sind die Bilder als JPEG-Data-URLs eingebettet (Block `BG-DATA-START/END`, erzeugt mit `tools/embed_backgrounds.py`). Nach Änderung der Bilder das Skript erneut ausführen.
  - Browser: Für die Überblendung immer die rAF-Zeit (`now`) verwenden, nicht `performance.now()` mischen.
- Änderungen an Regeln immer in beiden Versionen konsistent halten.
