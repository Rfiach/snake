# Snake

Klassisches Snake mit Regenbogen-Schlange – als Python-Spiel (pygame) und als Browser-Version.

## Python-Version starten
```powershell
py -m pip install --user -r requirements.txt
py snake.py
```
Hinweis: Verwendet wird `pygame-ce` (kompatibler pygame-Fork), da das klassische `pygame` für Python 3.14 noch keine fertigen Pakete hat.
Tests der Spiellogik: `py -m unittest -v`

## Mit Gradio hosten
Die Gradio-Anwendung verwendet die Browser-Version. Für einen öffentlichen,
temporären Gradio-Link lokal starten:
```powershell
py -m pip install -r requirements.txt
py app.py
```
Gradio zeigt im Terminal eine öffentliche URL der Form
`https://….gradio.live` an und öffnet die Anwendung lokal im Browser. Den
öffentlichen Link kannst du mit anderen teilen. Das Terminal und der Rechner
müssen laufen, solange der Link verwendet werden soll; der Share-Link ist
temporär und nicht für dauerhaftes Hosting gedacht. Für dauerhaftes Hosting
benötigst du einen dauerhaft laufenden Gradio-Server oder einen Hosting-Dienst.

## Browser-Version
`index.html` im Browser öffnen (oder per GitHub Pages).

## Steuerung
- **Pfeiltasten / WASD:** Richtung
- **Leertaste / P:** Pause
- **Enter:** Start / Neustart
- **H:** Bestenliste
- **4:** Design umschalten (Auto / Weihnachten / Silvester / Normal)
- **1 / 2 / 3** (Python, vor dem Start): Wrap-around / Hindernisse / Spezialfutter umschalten

## Spielfeld
28 × 18 Zellen im Querformat (beide Versionen). Das pygame-Fenster ist 932 × 804 px groß; die Darstellungsgröße lässt sich über `SCALE` und `CELL` in `snake.py` anpassen.

## Optionen
- **Wrap-around:** durch die Wand auf der Gegenseite wieder heraus
- **Hindernisse:** feste Blöcke auf dem Feld
- **Spezialfutter:** goldener Stern, +50 Punkte, mit Zeitlimit

Normales Futter bringt 10 Punkte; mit jedem Futter wird die Schlange schneller.

## Bestenliste
- Top 10 je Optionskombination mit Name, Punkten, Länge und Datum.
- Nach dem Spiel wird nach dem Namen gefragt, wenn die Punkte für die Liste reichen (Enter speichert, Esc überspringt). Der Name bleibt für die laufende Sitzung vorbelegt.
- **H** zeigt die Bestenliste, **←/→** wechselt dort zwischen den Modi.
- Gespeichert wird lokal: Python in `highscore.json`, Browser im `localStorage`.
- In der Online-Version (Cloudflare, siehe unten) teilen sich alle Spieler eine gemeinsame Bestenliste. Ist der Server nicht erreichbar, speichert der Browser lokal.

## Online-Version (Cloudflare Workers + D1)
Ein Worker liefert das Spiel aus und stellt die Bestenlisten-API bereit (`cloud/`):
- `GET /api/scores?mode=28x18-001` – Top 10 eines Modus
- `POST /api/scores` mit `{ mode, name, score, length }` – Eintrag speichern; der Server prüft die Plausibilität (Punkte passen zur Länge), bereinigt den Namen und begrenzt auf 5 Einträge pro Minute und Absender.

`cloud/build.mjs` kopiert `index.html` nach `cloud/public/`, schaltet dabei die Online-Bestenliste ein (`SCORE_API`) und blendet die Design-Auswahl aus (`THEME_PICKER`). Die lokale `index.html` bleibt rein lokal.

Einmalig einrichten:
```powershell
cd cloud
npm install
npx wrangler login
npx wrangler d1 create snake-scores        # ausgegebene database_id in wrangler.toml eintragen
npm run db:init:remote
npm run deploy
```
Lokal testen: `npm run db:init:local`, dann `npm run dev` (http://127.0.0.1:8787). Tests der Prüfregeln: `npm test`.

Bestenliste zurücksetzen: `npx wrangler d1 execute snake-scores --remote --command "DELETE FROM scores"`

## Weihnachten & Silvester
Vom 1. Advent bis 30.12. erscheint das Spiel automatisch weihnachtlich, am 31.12. mit Silvester-Feuerwerk, ab 1.1. wieder normal (jedes Jahr neu berechnet). Spielregeln, Punkte und Bestenlisten bleiben gleich – es ändert sich nur die Optik:
- 8 weihnachtliche Weltraum-Hintergründe (Polarlicht, Tannenbaum-Sternbild, Stern von Bethlehem, Rentierschlitten …)
- Schneefall (beim Gewinnen ein Gestöber), am 31.12. Feuerwerk
- Futter: Zuckerstange, Lebkuchenmann, Christbaumkugel, Zimtstern, Plätzchen; Spezialfutter als Geschenk
- Schlange als Lichterkette mit Weihnachtsmütze, Hindernisse als Eisblöcke, Wrap-Rahmen als Lichterkette
- Funkeln beim Fressen, weihnachtliche Texte, rot-grün-goldene Akzente

Umschalten mit **Taste 4** (Auto → Weihnachten → Silvester → Normal), im Browser auch über das Auswahlfeld „Design“ (wird gespeichert) oder zum Testen per `index.html?theme=xmas`. Die Online-Version zeigt keine Auswahl und folgt immer dem Datum.

## Weltraum-Hintergründe
Bei jedem gefressenen Futter wechselt der Hintergrund mit sanfter Überblendung zum nächsten von 8 Weltraum-Motiven (Nebel, Ringplanet, Spiralgalaxie, Schwarzes Loch, Komet …). Die Bilder liegen in `assets/` (in `index.html` eingebettet via `tools/embed_backgrounds.py`) und sind selbst generiert (`tools/make_backgrounds.py` bzw. `tools/make_xmas_backgrounds.py`, benötigt numpy + pillow – nur zum Neu-Erzeugen).

## Dateien
- `snake_core.py` – Spiellogik ohne Grafik
- `snake.py` – pygame-Oberfläche
- `snake_xmas.py` – Weihnachts-/Silvester-Grafik für pygame
- `app.py` – Gradio-Host für die Browser-Version
- `test_snake_core.py` – Tests
- `index.html` – Browser-Version
- `assets/` – Hintergrundbilder
- `tools/` – Skripte zum Erzeugen und Einbetten der Hintergründe
- `cloud/` – Cloudflare Worker (API + Auslieferung), D1-Schema, Tests
