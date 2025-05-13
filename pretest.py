import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st

# ========== Données ==========
carteBurkina = gpd.read_file("C:\\Users\\USER\\Desktop\\Monitoring\\gadm41_BFA_3.json")
index_file = pd.ExcelFile("C:\\Users\\USER\\Desktop\\Monitoring\\index_data.xlsx")
carteBurkina["NAME_3"].iloc[195] = "Fada N'gourma"

# Fonction de catégorisation
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

# ========== Interface ==========
st.set_page_config(layout="wide")
st.title("🌍 Visualisation des Indices Climatiques - Burkina Faso")

index_options = {
    "Indice WRSI" : "wrsi",
    "Indice NDVI" : "ndvi",
    "Indice CPS" : "cps",
    "Indice SPI" : "spi",
    "Eau résiduelle" : "resid"
}
index_display = st.sidebar.selectbox("Choisir un indice", list(index_options.keys()))
index_key = index_options[index_display]

# Lecture et nettoyage des données
df_index = index_file.parse(sheet_name=index_key)
df_index.columns = df_index.columns.astype(str).str.strip()  # nettoyage des noms de colonnes

# Années disponibles et sélection
available_years = df_index.columns[1:]
selected_years = st.sidebar.selectbox("Choisir une année", available_years)

# Départements
departements = df_index['NAME_3'].unique()
selected_dept = st.sidebar.selectbox("Choisir un département", ["Tous"] + list(departements))

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

# ========== Construction de la carte ==========
hover_cols = {}
if selected_years in merged.columns:
    hover_cols[selected_years] = True
if "Category" in merged.columns:
    hover_cols["Category"] = True

fig = px.choropleth_mapbox(
    merged,
    geojson=merged.geometry,
    locations=merged.index,
    color='Category',
    color_discrete_map=color_mapping,
    mapbox_style='carto-positron',
    zoom=5.5,
    center={"lat": 12.5, "lon": -1.5},
    opacity=0.6,
    hover_data=hover_cols
)
fig.update_layout(margin={"t":0, "b":0, "l":0, "r":0})
st.plotly_chart(fig, use_container_width=True)

# ========== Informations par département ==========
if selected_dept != "Tous":
    st.subheader(f"📌 Informations climatiques pour : {selected_dept}")
    val = df_year[df_year['NAME_3'] == selected_dept][selected_years].values[0]
    cat = df_year[df_year['NAME_3'] == selected_dept]['Category'].values[0]
    st.markdown(f"- **Valeur** : `{val}`")
    st.markdown(f"- **Catégorie** : `{cat}`")