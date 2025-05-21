import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st
import imageio
import tempfile
import os
import plotly.io as pio

# ========== Chargement optimisé ==========

@st.cache_data
def load_geojson(path):
    gdf = gpd.read_file(path)
    gdf.loc[195, "NAME_3"] = "Fada N'gourma"
    return gdf

@st.cache_resource
def load_excel(path):
    return pd.ExcelFile(path)

@st.cache_data
def parse_sheet(_excel_file, sheet_name):
    df = _excel_file.parse(sheet_name=sheet_name)
    df.columns = df.columns.astype(str).str.strip()
    return df

# ========== Configuration interface ==========
st.set_page_config(layout="wide")
st.title("🌍 Visualisation des Indices Climatiques - Burkina Faso")

# ========== Sélection utilisateur ==========
index_options = {
    "Indice WRSI" : "wrsi",
    "Indice NDVI" : "ndvi",
    "Indice CPS" : "cps",
    "Indice SPI" : "spi",
    "Eau résiduelle" : "resid"
}
index_display = st.sidebar.selectbox("Choisir un indice", list(index_options.keys()))
index_key = index_options[index_display]

# ========== Chargement des données avec spinner ==========
with st.spinner("📂 Chargement des données..."):
    carteBurkina = load_geojson("gadm41_BFA_3.json")
    index_file = load_excel("index_data.xlsx")
    df_index = parse_sheet(index_file, index_key)

# ========== Sélection de l'année et du département ==========
available_years = df_index.columns[1:]
selected_years = st.sidebar.selectbox("Choisir une année", available_years)

departements = df_index['NAME_3'].unique()
selected_dept = st.sidebar.selectbox("Choisir un département", ["Tous"] + list(departements))

# ========== Fonction de catégorisation ==========
def classify_value(index, value):
    if pd.isnull(value):
        return 'Valeur Manquante'
    
    if index in ['wrsi', 'cps', 'ndvi']:
        if value <= 0.7:
            return "Sécheresse sévère"
        elif value <= 0.8:
            return "Sécheresse modérée"
        elif value <= 0.9:
            return "Sécheresse légère"
        elif value <= 1:
            return "Condition normale"
        elif value <= 1.1:
            return "Inondation modérée"
        else:
            return "Inondation sévère"
        
    elif index == "spi":
        if value <= -2:
            return "Sécheresse sévère"
        elif value <= -1.5:
            return "Sécheresse modérée"
        elif value <= -1:
            return "Sécheresse légère"
        elif value <= 1:
            return "Condition normale"
        elif value <= 1.5:
            return "Inondation modérée"
        else:
            return "Inondation sévère"
        
    elif index == "resid":
        return "Inondation constaté" if value == 1 else "Pas d'inondation constaté"
    
    return "Inconnu"

# ========== Préparation des données ==========
if selected_years not in df_index.columns:
    st.error(f"La colonne '{selected_years}' n'existe pas dans les données.")
    st.stop()

df_year = df_index[['NAME_3', selected_years]].copy()
df_year["Category"] = df_year[selected_years].apply(lambda x: classify_value(index_key, x))
merged = carteBurkina.merge(df_year, on="NAME_3", how="left")

# ========== Couleurs ==========
color_mapping = {
    "Sécheresse sévère": "#8B0000",
    "Sécheresse modérée": "#CD5C5C",
    "Sécheresse légère": "#F08080",
    "Condition normale": "#A9A9A9",
    "Inondation modérée": "#87CEFA",
    "Inondation sévère": "#4682B4",
    "Inondation constaté": "#1E90FF",
    "Pas d'inondation constaté": "#B0C4DE",
    "Valeur Manquante": "#D3D3D3",
    "Inconnu": "#000000"
}

st.markdown(f"**Indice choisi** : {index_display}")

# ========== Filtrage si nécessaire ==========
filtered_map = merged if selected_dept == "Tous" else merged[merged["NAME_3"]==selected_dept]

# ========== Centre et zoom dynamique ==========
if selected_dept != "Tous":
    centroid = filtered_map.geometry.centroid.iloc[0]
    map_center = {"lat": centroid.y, "lon": centroid.x}
    zoom_level = 7
else:
    map_center = {"lat": 12.5, "lon": -1.5}
    zoom_level = 5.5

# ========== Carte ==========
fig = px.choropleth_mapbox(
    filtered_map,
    geojson=filtered_map.geometry,
    locations=filtered_map.index,
    color='Category',
    color_discrete_map=color_mapping,
    mapbox_style='carto-positron',
    zoom=zoom_level,
    center=map_center,
    opacity=0.6,
    hover_data={
        "NAME_3": True,
        selected_years: True,
        "Category": True
    }
)

fig.update_layout(margin={"t":0, "b":0, "l":0, "r":0})
st.plotly_chart(fig, use_container_width=True)

# ========== Informations complémentaires ==========
if selected_dept != "Tous":
    st.subheader(f"📌 Informations climatiques pour : {selected_dept}")
    val = df_year[df_year['NAME_3'] == selected_dept][selected_years].values[0]
    cat = df_year[df_year['NAME_3'] == selected_dept]['Category'].values[0]
    st.markdown(f"- **Valeur** : `{val}`")
    st.markdown(f"- **Catégorie** : `{cat}`")

# ========== GIF d'animation par indice ==========
st.markdown("---")
st.subheader("🎞️ Animation de l'évolution annuelle de l'indice sélectionné")

# Dictionnaire des chemins des fichiers GIF
gif_paths = {
    "wrsi": "gifs/wrsi.gif",
    "ndvi": "gifs/ndvi.gif",
    "cps": "gifs/cps.gif",
    "spi": "gifs/spi.gif",
    "resid": "gifs/resid.gif"
}

# On récupère le bon chemin selon l'indice sélectionné
gif_path = gif_paths.get(index_key)

# Vérification que le fichier existe, puis affichage
if gif_path and os.path.exists(gif_path):
    with open(gif_path, "rb") as f:
        gif_data = f.read()
        st.image(gif_data, use_container_width=True,  # ✅ Mise à jour ici
                 caption=f"Évolution annuelle de l’indice {index_key.upper()}")
else:
    st.warning("⚠️ Aucun GIF disponible pour cet indice.")
