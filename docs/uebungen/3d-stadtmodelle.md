# Neue Gebäude und Grünflächen im 3D-Stadtmodell

**Ziel:** Mit Basemap3D eigene Szenen programmieren, Objekte platzieren, Schatten untersuchen und die Eignung verschiedener Stadtmodelle beurteilen. **Aufgaben 1–3 sind Pflicht; Aufgabe 4 ist freiwillig.**

## 1 · Grundlagen kennenlernen (Pflicht)

Bearbeiten Sie die ersten beiden Beispiele im [Colab-Notebook „Modules“](https://colab.research.google.com/github/yfeng-hsm/Basemap3D/blob/main/notebooks/Mainz_Modules.ipynb). Führen Sie zuerst die Installation aus.

- Ändern Sie Standort, Kameradistanz und Blickwinkel.
- Erklären Sie kurz die Rollen von `Map` und `.add_to(m)`.

## 2 · Eine eigene Szene für Trier (Pflicht)

Erstellen Sie ein **eigenes Colab-Notebook**. Übernehmen Sie bei Bedarf die Installationszelle aus Aufgabe 1; schreiben Sie den Szenencode selbst.

- Laden Sie das **Stadtmesh von Trier** mit `Tiles3D`. Deaktivieren Sie die standardmäßigen LoD2-Gebäude, damit sich die Modelle nicht überlagern.

- Ergänzen Sie `HousePlacement` und `SunShadows`. Platzieren Sie mindestens ein neues Haus und eine Grünfläche auf einer freien Fläche. Passen Sie Größe und Ausrichtung an.

- Vergleichen Sie die Schatten zu zwei Tageszeiten am selben Datum.

Orientieren Sie sich an den [Examples · Mesh models](https://yfeng-hsm.github.io/Basemap3D/examples/#mesh). Wählen Sie dort Trier aus und verwenden Sie die Beispiele als Grundlage für Ihren eigenen Szenencode.

## 3 · Auf Koblenz übertragen und vergleichen (Pflicht)

Passen Sie Ihren eigenen Code für das **Stadtmesh von Koblenz** an. Wiederholen Sie die Platzierung von Haus und Grünfläche sowie den Schattenvergleich. Verwenden Sie dieselben Objektgrößen, dasselbe Datum und dieselben Uhrzeiten wie in Trier.

- Welche Unterschiede beobachten Sie? Achten Sie auf schwebende oder versunkene Objekte, durchdringende Oberflächen und die Sichtbarkeit der Schatten.

- Erklären Sie mögliche Ursachen für die Unterschiede zwischen beiden Städten. Berücksichtigen Sie dabei das Zusammenspiel von Gelände und Mesh.

- Unterscheiden Sie zwischen Ihren Beobachtungen und möglichen Erklärungen. Falls Sie keinen Unterschied erkennen, berichten Sie auch dieses Ergebnis.

## 4 · Das Python-Paket mit KI erweitern (Optional)

Entwickeln Sie Basemap3D mithilfe eines KI-Assistenten weiter. Wählen Sie einen Anwendungsfall und ergänzen Sie passende **geometrische Objekte**, etwa Bäume, Bänke, Überdachungen oder Zylinder und Quader.

Die Erweiterung soll über die Python-Schnittstelle nutzbar sein und die interaktive Platzierung unterstützen. Ermöglichen Sie passende Einstellungen für Größe, Höhe, Farbe oder Ausrichtung. Prüfen Sie den KI-generierten Code und testen Sie die Erweiterung. Erläutern Sie bei der Demonstration Ihren eigenen Beitrag, die KI-Unterstützung und bekannte Grenzen.

**Abschluss:** Wenn Sie die Pflichtaufgaben abgeschlossen haben, melden Sie sich per Handzeichen. Zeigen Sie dem Dozenten Ihre Szenen in Trier und Koblenz und erläutern Sie kurz die beobachteten Unterschiede. Falls Sie Aufgabe 4 bearbeitet haben, führen Sie auch Ihre Erweiterung vor. Eine Datei-Abgabe ist nicht erforderlich.

**Hinweise:** Platzierte Objekte bleiben derzeit nur in der laufenden Kartensitzung erhalten; sie werden nicht im Notebook oder HTML-Export gespeichert. Schatten in Mesh-Texturen bleiben unverändert. Die Darstellung dient der qualitativen Untersuchung, nicht einer verbindlichen Planungsprüfung. Datenquellen im Viewer beibehalten.
