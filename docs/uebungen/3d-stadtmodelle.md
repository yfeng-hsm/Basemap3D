# Neue Gebäude und Grünflächen im 3D-Stadtmodell

**Ziel:** Mit Basemap3D eigene Szenen programmieren, Objekte platzieren, Schatten untersuchen und die Eignung verschiedener Stadtmodelle beurteilen. **Aufgaben 1–3 sind Pflicht; Aufgabe 4 ist freiwillig.**

## 1 · Grundlagen kennenlernen (Pflicht)

Bearbeiten Sie die ersten beiden Beispiele im [Colab-Notebook „Modules“](https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/notebooks/Mainz_Modules.ipynb). Führen Sie zuerst die Installation aus.

- Ändern Sie Standort, Kameradistanz und Blickwinkel.
- Erklären Sie kurz die Rollen von `Map` und `.add_to(m)`.

## 2 · Eine eigene Szene für Trier (Pflicht)

Erstellen Sie ein **eigenes Colab-Notebook**. Übernehmen Sie bei Bedarf die Installationszelle aus Aufgabe 1; schreiben Sie den Szenencode selbst.

- Laden Sie das **Stadtmesh von Trier** mit `Tiles3D`. Deaktivieren Sie die standardmäßigen LoD2-Gebäude, damit sich die Modelle nicht überlagern.

- Ergänzen Sie `HousePlacement` und `SunShadows`. Platzieren Sie mindestens ein neues Haus und eine Grünfläche auf einer freien Fläche. Passen Sie Größe und Ausrichtung an.

- Vergleichen Sie die Schatten zu zwei Tageszeiten am selben Datum. Dokumentieren Sie die Szene mit Screenshots.

Nutzen Sie die [API-Dokumentation](https://github.com/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/docs/API.md) und den [Stadtkatalog mit Mesh-URLs und Standorten](https://github.com/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/docs/examples/city_sources.json). Ein fertiges Trier-Notebook ist für diese Aufgabe nicht vorgesehen.

## 3 · Auf Koblenz übertragen und vergleichen (Pflicht)

Passen Sie Ihren eigenen Code für das **Stadtmesh von Koblenz** an. Wiederholen Sie die Platzierung von Haus und Grünfläche sowie den Schattenvergleich. Verwenden Sie dieselben Objektgrößen, dasselbe Datum und dieselben Uhrzeiten wie in Trier.

- Welche Unterschiede beobachten Sie? Achten Sie auf schwebende oder versunkene Objekte, durchdringende Oberflächen und die Sichtbarkeit der Schatten.

- Untersuchen Sie anhand des [Renderer-Codes](https://github.com/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/basemap3d/assets/scene.js), welche Oberfläche für die Platzierung verwendet wird. Erklären Sie mögliche Ursachen für die Unterschiede zwischen beiden Städten.

- Trennen Sie **Beobachtungen, durch den Code belegte Aussagen und noch ungeprüfte Vermutungen**. Falls Sie keinen Unterschied erkennen, dokumentieren Sie auch dieses Ergebnis.

## 4 · Das Python-Paket mit KI erweitern (Optional)

Entwickeln Sie Basemap3D mithilfe eines KI-Assistenten weiter. Wählen Sie einen Anwendungsfall und ergänzen Sie passende **geometrische Objekte**, etwa Bäume, Bänke, Überdachungen oder Zylinder und Quader.

Die Erweiterung soll über die Python-Schnittstelle nutzbar sein und die interaktive Platzierung unterstützen. Ermöglichen Sie passende Einstellungen für Größe, Höhe, Farbe oder Ausrichtung. Prüfen Sie den KI-generierten Code und testen Sie die Erweiterung. Dokumentieren Sie Ihren eigenen Beitrag, die KI-Unterstützung und bekannte Grenzen.

**Abgabe:** Ihr ausführbares Notebook, je zwei Screenshots aus Trier und Koblenz sowie eine kurze Erklärung der Unterschiede. Optional: geänderte Paketdateien, ein Python-Anwendungsbeispiel und ein Screenshot der Erweiterung.

**Hinweise:** Platzierte Objekte bleiben derzeit nur in der laufenden Kartensitzung erhalten; sie werden nicht im Notebook oder HTML-Export gespeichert. Schatten in Mesh-Texturen bleiben unverändert. Die Darstellung dient der qualitativen Untersuchung, nicht einer verbindlichen Planungsprüfung. Datenquellen im Viewer beibehalten.
