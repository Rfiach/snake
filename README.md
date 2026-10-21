# Snake

Klassisches Snake mit Regenbogen-Schlange – als Python-Spiel (pygame) und als Browser-Version.

## Python-Version starten
```powershell
py -m pip install --user -r requirements.txt
py snake.py
```
Hinweis: Verwendet wird `pygame-ce` (kompatibler pygame-Fork), da das klassische `pygame` für Python 3.14 noch keine fertigen Pakete hat.
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

## Weltraum-Hintergründe
Bei jedem gefressenen Futter wechselt der Hintergrund mit sanfter Überblendung zum nächsten von 8 Weltraum-Motiven (Nebel, Ringplanet, Spiralgalaxie, Schwarzes Loch, Komet …). Die Bilder liegen in `assets/` (in `index.html` eingebettet via `tools/embed_backgrounds.py`) und sind selbst generiert (`tools/make_backgrounds.py`, benötigt numpy + pillow – nur zum Neu-Erzeugen).

## Dateien
- `snake_core.py` – Spiellogik ohne Grafik
- `snake.py` – pygame-Oberfläche
- `test_snake_core.py` – Tests
- `index.html` – Browser-Version
