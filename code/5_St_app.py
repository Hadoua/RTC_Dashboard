import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import os

# ---------------------------------------------------------
# Configuration 
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="Project RTC")
#st.title("Arrêts  du RTC : exploration des services à proximité")

col_type_osm = 'amenity'
col_nom_osm = 'geopy_name'

# CSS pour le style
st.markdown("""
<style>
    /* réduire l'espace vide en haut de la page */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }

    /* Style tableaux onglet 3 */
    .category-header {
        background-color: #4b7bff; 
        color: white;
        padding: 8px 15px;
        border-radius: 4px 4px 0 0;
        font-weight: bold;
        font-family: sans-serif;
        margin-bottom: 0px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Dictionnaires pour mapper les données
# ---------------------------------------------------------
all_groups = {
    'Nourriture & Boissons': ['restaurant', 'fast_food', 'cafe', 'bar', 'pub', 'ice_cream'],
    'Santé': ['pharmacy', 'hospital', 'clinic', 'doctors', 'dentist'],
    'Commerces': ['fuel'],
    'Services Publics': ['post_office', 'police', 'townhall', 'library', 'community_centre', 'fire_station'],
    'Éducation': ['school', 'university', 'college', 'kindergarten'],
    'Finance': ['bank', 'atm'],
    'Transport': ['taxi', 'bicycle_rental'], 
    'Culte': ['place_of_worship']
}

traductions_cate = {
    'bank': 'Banque', 'fast_food': 'Restauration rapide', 'fuel': 'Station-service',
    'bus_station': 'Gare routière', 'restaurant': 'Restaurant', 'cafe': 'Café',
    'parking': 'Stationnement', 'library': 'Bibliothèque', 'post_office': 'Bureau de poste',
    'school': 'École', 'pharmacy': 'Pharmacie', 'place_of_worship': 'Église',
    'community_centre': 'Centre communautaire', 'pub': 'Pub', 'ice_cream': 'Crèmerie',
    'bar': 'Bar', 'townhall': 'Hôtel de ville', 'dentist': 'Dentiste',
    'taxi': 'Taxi', 'atm': 'Guichet automatique', 'kindergarten': 'Garderie',
    'doctors': 'Médecin', 'clinic': 'Clinique', 'university': 'Université',
    'hospital': 'Hôpital', 'bicycle_rental': 'Location de vélo', 'college': 'Cégep'
}

couleurs_categories = {
    'fast_food': 'orange', 'restaurant': 'orange', 'cafe': 'orange', 
    'pub': 'orange', 'bar': 'orange', 'ice_cream': 'orange',
    'pharmacy': 'red', 'dentist': 'red', 'doctors': 'red', 'clinic': 'red', 'hospital': 'red',
    'school': 'green', 'library': 'green', 'university': 'green', 
    'college': 'green', 'kindergarten': 'green', 
    'taxi': 'darkblue', 'bicycle_rental': 'darkblue',
    'bank': 'purple', 'atm': 'purple',
    'post_office': 'gray', 'community_centre': 'gray',
    'townhall': 'gray',  'police': 'gray', 'fire_station': 'gray', 
    'place_of_worship': 'darkpurple',
    'supermarket': 'cadetblue', 'convenience': 'cadetblue', 'bakery': 'cadetblue', 
    'shop': 'cadetblue', 'mall': 'cadetblue', 'fuel': 'cadetblue'
}

# ---------------------------------------------------------
# Fonctions utiles 
# ---------------------------------------------------------
def get_amenity_category(amenity):
    """Retourne le groupe ou se trouve l'amenity"""
    for group, group_amenities in all_groups.items():
        if amenity in group_amenities:
            return group
    return 'Autres'

def get_marker_style(amenity):
    """Retourne la couleur et l'icône selon le type"""
    couleur = couleurs_categories.get(amenity, 'blue') 
    icone = "info-sign"

    if couleur == 'orange': icone = "cutlery" 
    elif couleur == 'red': icone = "plus"
    elif couleur == 'green': icone = "book"
    elif couleur == 'darkblue': icone = "road"
    elif couleur == 'purple': icone = "briefcase"
    elif couleur == 'cadetblue': icone = "shopping-cart"
    elif couleur == 'darkpurple': icone = "eye-open" 
    elif couleur == 'gray': icone = "envelope" 
    return couleur, icone

# ---------------------------------------------------------
# Données 
# ---------------------------------------------------------
@st.cache_data
def load_data():
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    rtc_path = os.path.join(current_dir, '..', 'output', 'rtc_data.geojson')
    osm_path = os.path.join(current_dir, '..', 'output', 'osm_places_v2.geojson')
    
    # 1. Chargement
    rtc_data = gpd.read_file(rtc_path)
    osm_places = gpd.read_file(osm_path)
    
    # Projection en mètres NAD83 CSRS MTM zone 7 
    osm_meters = osm_places.to_crs(epsg=2949)
    
    return rtc_data, osm_places, osm_meters

rtc_data, osm_places, osm_meters_all = load_data() 

# ---------------------------------------------------------
# Création des filtres  et boutton de recherche 
# ---------------------------------------------------------
#st.markdown("### Sélectionner les paramètres de recherche")
with st.container():
    #c1, c2, c3, c4, c5 = st.columns(5)
    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        types_bus_uniques = rtc_data['Type'].unique()
        selected_type = st.selectbox("1. Type de parcours", types_bus_uniques)

    with c2:
        parcours_uniques = rtc_data[rtc_data['Type'] == selected_type]['Parcours'].unique()
        selected_parcours = st.selectbox("2. Numéro de parcours", sorted(parcours_uniques, key=int))

    with c3:
        subset_parcours = rtc_data[(rtc_data['Type'] == selected_type) & (rtc_data['Parcours'] == selected_parcours)]
        dir_dispo_uniques = subset_parcours['trip_headsign'].unique()
        direction_choisie = st.selectbox("3. Direction", dir_dispo_uniques)

    c4, c5, c6 = st.columns([2, 2, 1], vertical_alignment="bottom") 
    with c4:
        subset_final = subset_parcours[subset_parcours['trip_headsign'] == direction_choisie]
        subset_final = subset_final.sort_values('stop_sequence')
        arrets_dict = dict(zip(subset_final['stop_name'], subset_final['stop_id']))
        selected_stop_name = st.selectbox("4. Arrêt", list(arrets_dict.keys()))

    with c5:
        #radius = st.number_input("5. Rayon de recherche (mètres)", min_value=50, max_value=2000, value=500, step=50)
        radius = st.slider(
            "5. Rayon de recherche (mètres)",
            min_value=0,  max_value=2000, step=100,
            value=500
        )
        
    with c6:
        lancer = st.button("Rechercher", type="primary", use_container_width=True)
    
# Bouton Recherche
if "map_data" not in st.session_state:
    st.session_state.map_data = None

if lancer:
    stop_info_choisi = subset_final[subset_final['stop_name'] == selected_stop_name].iloc[0].copy()
    
    st.session_state.map_data = {
        'stop_info': stop_info_choisi,
        'radius': radius
    }

# ---------------------------------------------------------
# Calculs principaux
# ---------------------------------------------------------
if st.session_state.map_data is not None:
    
    st.divider()
    
    # Récupération des inputs utilisateurs 
    data = st.session_state.map_data
    stop_info = data['stop_info']
    rayon_de_recherche = data['radius']
        
    # Projection geometrie arret vers le NAD83 CSRS MTM zone 7 
    stop_geom_meters = gpd.GeoSeries([stop_info.geometry], crs="EPSG:4326").to_crs(epsg=2949).iloc[0]

    # Calcul des distances entre l arrets et tous les points d interet OSM 
    distances = osm_meters_all.geometry.distance(stop_geom_meters)
    
    # Filtre selon le rayon de recherche
    dist_within_rayon = osm_meters_all[distances <= rayon_de_recherche].copy()
    dist_within_rayon['distance_m'] = distances[distances <= rayon_de_recherche]

    # ---------------------------------------------------------
    # Preparation des donnéées : Mapping, traduction 
    # ---------------------------------------------------------
    if not dist_within_rayon.empty:
        # Traduction fr
        dist_within_rayon['Type_FR'] = dist_within_rayon[col_type_osm].map(traductions_cate).fillna(dist_within_rayon[col_type_osm])
        
        # Creation colonne groupes defini dans all_groups
        dist_within_rayon['Groupe'] = dist_within_rayon[col_type_osm].apply(get_amenity_category)
        
        # Formatage texte distance
        dist_within_rayon['Dist_Text'] = dist_within_rayon['distance_m'].map('{:.0f} m'.format)
        
        # D. Gestion des noms vides
        #dist_within_rayon[col_nom_osm] = dist_within_rayon[col_nom_osm].fillna("Lieu sans nom")
        
        # Projection des points en WGS84 pour la carte 
        nearby_wgs84 = dist_within_rayon.to_crs(epsg=4326)
    else:
        nearby_wgs84 = gpd.GeoDataFrame() 

    # ---------------------------------------------------------
    # Affichages des trois onglets carte, analyse et tableau
    # ---------------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["Carte Interactive", "Analyses", "Tableaux détaillés"])
    
    # CARTE 
    with tab1: 
        m = folium.Map(location=[stop_info.stop_lat, stop_info.stop_lon], 
                       zoom_start=16, tiles="Cartodb Positron")

        # Marqueur de l'arrêt
        html_arret = f"""
        <div style="font-family:sans-serif; width:160px; line-height:1.4;">
            Arrêt RTC<br><b style="font-size:1.1em;">{stop_info.stop_name}</b>
        </div>
        """
        folium.Marker(
            [stop_info.stop_lat, stop_info.stop_lon],
            popup=folium.Popup(html_arret, max_width=300),
            icon=folium.Icon(color="black", icon="bus", prefix="fa"),
        ).add_to(m)

        # Zone de recherche
        folium.Circle(
            location=[stop_info.stop_lat, stop_info.stop_lon],
            radius=rayon_de_recherche, color="#3388ff", fill=True, fill_opacity=0.08
        ).add_to(m)

        # Points d'intérêts
        if not nearby_wgs84.empty:
            for _, row in nearby_wgs84.iterrows():
                couleur, icone = get_marker_style(row[col_type_osm])         

                html = f"""
                <div style="font-family:sans-serif; width:160px; line-height:1.4;">
                    <span style="font-size:0.8em; color:#555;">{row['Type_FR']}</span><br>
                    <b style="color:{couleur}; font-size:1em;">{row[col_nom_osm]}</b><br>
                    <b>{row['Dist_Text']}</b>
                </div>
                """
                
                folium.Marker(
                    [row.geometry.y, row.geometry.x],
                    popup=folium.Popup(html, max_width=300),
                    icon=folium.Icon(color=couleur, icon=icone)
                ).add_to(m)

        st_folium(m, width=None, height=500)

    # ANALYSES
    with tab2: 
        if not dist_within_rayon.empty:
            c1, c2 = st.columns(2)
            with c1:
               
                counts = dist_within_rayon['Type_FR'].value_counts().reset_index()
                counts.columns = ['Type', 'Nombre']
                fig_bar = px.bar(counts, x='Nombre', y='Type', orientation='h', 
                                 title="Nombre de lieux par catégorie", color='Type')
                fig_bar.update_layout(showlegend=False, yaxis_title=None)
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with c2:
                fig_hist = px.histogram(dist_within_rayon, x="distance_m", nbins=15, 
                                        title="Distribution des distances",
                                        labels={'distance_m': 'Distance (m)'})
                st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Aucun lieu trouvé dans ce rayon")

    # TABLEAUX 
    with tab3: 
        if not dist_within_rayon.empty:
            
            cols_ui = st.columns(2)

            groupes_presents = sorted(dist_within_rayon['Groupe'].unique())
            
            for i, groupe in enumerate(groupes_presents):
                col_index = i % 2
                
                # Filtrage simple sur le DataFrame principal
                subset = dist_within_rayon[dist_within_rayon['Groupe'] == groupe].sort_values('distance_m')
                count = len(subset)
                moyenne_dist = subset['distance_m'].mean()
                
                with cols_ui[col_index]:
                    st.markdown(f"""
                    <div class="category-header">
                        {groupe} ({count}) <span style="float:right; font-weight:normal; font-size:0.9em">Distance moy. {moyenne_dist:.0f}m</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Sélection des colonnes d'affichage
                    df_clean = subset[[col_nom_osm, 'Type_FR', 'Dist_Text']]
                    df_clean.columns = ['Nom', 'Type', 'Dist.']
                    
                    st.dataframe(
                        df_clean, 
                        use_container_width=True, 
                        hide_index=True,
                        height=(min(len(df_clean) * 35 + 38, 400))
                    )
                    st.write("") 
        else:
            st.write("Aucun résultat à afficher.")

else:
    st.info("Utilisez les filtres ci-dessus pour lancer une recherche.")
