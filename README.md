# Snake

Klassisches Snake mit Regenbogen-Schlange – als Python-Spiel (pygame) und als Browser-Version.

## Python-Version starten
```bash
pip install -r requirements.txt
python snake.py
```
Tests der Spiellogik: `python -m unittest -v`

## Browser-Version
`index.html` im Browser öffnen (oder per GitHub Pages).

## Steuerung
- **Pfeiltasten / WASD:** Richtung
- **Leertaste / P:** Pause
- **Enter:** Start / Neustart
- **1 / 2 / 3** (Python, vor dem Start): Wrap-around / Hindernisse / Spezialfutter umschalten

## Optionen
- **Wrap-around:** durch die Wand auf der Gegenseite wieder heraus
- **Hindernisse:** feste Blöcke auf dem Feld
- **Spezialfutter:** goldener Stern, +50 Punkte, mit Zeitlimit

Normales Futter bringt 10 Punkte; mit jedem Futter wird die Schlange schneller. Der Highscore wird pro Optionskombination gespeichert (Python: `highscore.json`).

## Dateien
- `snake_core.py` – Spiellogik ohne Grafik
- `snake.py` – pygame-Oberfläche
- `test_snake_core.py` – Tests
- `index.html` – Browser-Version
