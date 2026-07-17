# Unfallanalyse Oberbaumbrücke

Dieses Repository enthält ein mit Streamlit umgesetztes Dashboard zur Analyse
der polizeilich erfassten Verkehrsunfälle im Untersuchungsraum Oberbaumbrücke
für die Jahre 2018 bis 2024.

## Inhalt

Das Dashboard zeigt:

- die Gesamtzahl der Unfälle,
- die Zahl und den Anteil der Unfälle mit Radverkehrsbeteiligung,
- die Entwicklung der Radunfälle nach Jahren,
- einen Vergleich zwischen allen Unfällen und Radunfällen,
- die räumliche Verteilung der Unfallpunkte auf einer interaktiven Karte.

## Datengrundlage

Die Unfallpunkte wurden im Rahmen der Labor-Hausaufgabe zunächst in QGIS
räumlich auf den Bereich der Oberbaumbrücke und die angrenzenden Knotenpunkte
begrenzt. Der gefilterte Datensatz wurde anschließend als CSV-Datei exportiert
und mit pandas, Plotly und Folium ausgewertet.

## Dateien

- `dashboard.py`
- `requirements.txt`
- `Unfaelle_Oberbaumbruecke_2017_2024.csv`

## Start der Anwendung

```bash
streamlit run dashboard.py
```
