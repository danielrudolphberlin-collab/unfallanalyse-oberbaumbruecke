import pandas as pd
import plotly.express as px
import streamlit as st
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

st.set_page_config(
    page_title="Unfallanalyse Oberbaumbrücke",
    page_icon="🚲",
    layout="wide"
)

st.title("🚲 Unfallanalyse Oberbaumbrücke")
st.caption(
    "Polizeilich erfasste Verkehrsunfälle im Untersuchungsraum Oberbaumbrücke "
    "(2018–2024)"
)

st.markdown(
    '''
    Das Dashboard visualisiert die im Rahmen der Labor-Hausaufgabe räumlich
    gefilterten Verkehrsunfälle im Bereich der Oberbaumbrücke. Im Mittelpunkt
    stehen die zeitliche Entwicklung der Unfälle mit Radverkehrsbeteiligung,
    deren Anteil am gesamten Unfallgeschehen sowie ihre räumliche Verteilung.
    '''
)

DATA_FILE = "Unfaelle_Oberbaumbruecke_2017_2024.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)

    def as_bool(series):
        return (
            series.astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "wahr", "1", "1.0", "ja"])
        )

    df["IstRad_bool"] = as_bool(df["IstRad"]) if "IstRad" in df.columns else False

    for col in ["UJAHR", "UMONAT", "USTUNDE", "UKATEGORIE"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

df = load_data()
rad = df[df["IstRad_bool"]].copy()

c1, c2, c3 = st.columns(3)
c1.metric("Unfälle insgesamt", f"{len(df):,}".replace(",", "."))
c2.metric("Unfälle mit Radbeteiligung", f"{len(rad):,}".replace(",", "."))
anteil = (len(rad) / len(df) * 100) if len(df) else 0
c3.metric(
    "Anteil der Unfälle mit Radbeteiligung",
    f"{anteil:.1f} %".replace(".", ",")
)

st.divider()

jahre = (
    sorted([int(x) for x in df["UJAHR"].dropna().unique()])
    if "UJAHR" in df.columns
    else []
)
auswahl = st.multiselect("Jahre auswählen", jahre, default=jahre)

gefiltert = df[df["UJAHR"].isin(auswahl)] if jahre else df
rad_gefiltert = gefiltert[gefiltert["IstRad_bool"]]

st.subheader("Entwicklung der Unfälle mit Radbeteiligung")
st.write(
    "Die Darstellung zeigt die Anzahl der im Untersuchungsraum erfassten "
    "Unfälle mit Radverkehrsbeteiligung je Jahr."
)

pro_jahr = (
    rad_gefiltert.groupby("UJAHR")
    .size()
    .reset_index(name="Anzahl")
    .sort_values("UJAHR")
)

fig = px.bar(
    pro_jahr,
    x="UJAHR",
    y="Anzahl",
    labels={"UJAHR": "Jahr", "Anzahl": "Anzahl der Radunfälle"},
    text="Anzahl",
    color_discrete_sequence=["#d95f02"]
)
fig.update_traces(textposition="outside")
fig.update_layout(
    showlegend=False,
    xaxis=dict(dtick=1),
    margin=dict(t=20, l=20, r=20, b=20)
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Radbeteiligung im Jahresvergleich")
st.write(
    "Das zweite Diagramm stellt die Gesamtzahl der Unfälle der Zahl der "
    "Unfälle mit Radverkehrsbeteiligung gegenüber."
)

gesamt = gefiltert.groupby("UJAHR").size().rename("Alle Unfälle")
rad_jahr = rad_gefiltert.groupby("UJAHR").size().rename("Mit Radbeteiligung")
vergleich = pd.concat([gesamt, rad_jahr], axis=1).fillna(0).reset_index()

vergleich_lang = vergleich.melt(
    id_vars="UJAHR",
    var_name="Kategorie",
    value_name="Anzahl"
)

fig2 = px.bar(
    vergleich_lang,
    x="UJAHR",
    y="Anzahl",
    color="Kategorie",
    barmode="group",
    labels={"UJAHR": "Jahr"},
    color_discrete_map={
        "Alle Unfälle": "#4c78a8",
        "Mit Radbeteiligung": "#d95f02"
    }
)
fig2.update_layout(
    xaxis=dict(dtick=1),
    margin=dict(t=20, l=20, r=20, b=20)
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Räumliche Verteilung")
st.write(
    "Die Karte zeigt die im ausgewählten Zeitraum erfassten Unfallpunkte. "
    "Unfälle mit Radverkehrsbeteiligung sind hervorgehoben."
)

map_df = gefiltert.copy()
lat = lon = None

if {"XGCSWGS84", "YGCSWGS84"}.issubset(map_df.columns):
    lon = pd.to_numeric(map_df["XGCSWGS84"], errors="coerce")
    lat = pd.to_numeric(map_df["YGCSWGS84"], errors="coerce")

if (
    lat is None
    or lon is None
    or lat.dropna().empty
    or lon.dropna().empty
    or lat.abs().max() > 90
):
    if {"X", "Y"}.issubset(map_df.columns):
        x = pd.to_numeric(map_df["X"], errors="coerce")
        y = pd.to_numeric(map_df["Y"], errors="coerce")
        transformer = Transformer.from_crs(
            "EPSG:3857",
            "EPSG:4326",
            always_xy=True
        )
        coords = [
            transformer.transform(xi, yi)
            if pd.notna(xi) and pd.notna(yi)
            else (None, None)
            for xi, yi in zip(x, y)
        ]
        lon = pd.Series([c[0] for c in coords], index=map_df.index)
        lat = pd.Series([c[1] for c in coords], index=map_df.index)

map_df["lon"] = lon
map_df["lat"] = lat
map_df = map_df.dropna(subset=["lat", "lon"])
map_df = map_df[
    map_df["lat"].between(52.3, 52.8)
    & map_df["lon"].between(13.0, 13.8)
]

m = folium.Map(
    location=[52.5015, 13.4450],
    zoom_start=15,
    tiles="CartoDB positron"
)

for _, row in map_df.iterrows():
    rad_unfall = bool(row["IstRad_bool"])

    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=5 if rad_unfall else 3,
        color="#d95f02" if rad_unfall else "#666666",
        fill=True,
        fill_opacity=0.75,
        tooltip=(
            f"Jahr: "
            f"{int(row['UJAHR']) if pd.notna(row.get('UJAHR')) else '-'}"
            f" | Radbeteiligung: {'Ja' if rad_unfall else 'Nein'}"
        )
    ).add_to(m)

st_folium(m, use_container_width=True, height=520)

with st.expander("Methodisches Vorgehen"):
    st.markdown(
        '''
        1. Räumliche Eingrenzung des Untersuchungsraums in QGIS  
        2. Auswahl der innerhalb des Polygons liegenden Unfallpunkte  
        3. Export der Attributdaten als CSV-Datei  
        4. Auswertung mit pandas und Visualisierung mit Plotly und Folium  
        5. Veröffentlichung über GitHub und Streamlit Cloud
        '''
    )

with st.expander("Datengrundlage anzeigen"):
    st.dataframe(gefiltert, use_container_width=True)

st.caption(
    "Hinweis: Die Auswertung ist deskriptiv. Veränderungen können nicht ohne "
    "Weiteres kausal auf die 2022 umgesetzte Maßnahme zurückgeführt werden."
)
