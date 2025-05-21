# import packages
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# erstellen der Seite
st.set_page_config(layout="wide")
st.title("Climate Dashboard Valais in January")

# Selection climate variable
option = st.sidebar.selectbox("Select Climate Variable", ["Temperature", "Sunshine", "Percipitation"])

# definition of different selection options
if option == "Temperature":
    filepath = "data/gemeinden_temp.geojson"
    column = "mean_temperature"
    color = "RdBu_r"
    legend = "Ø Temperature (°C)"
elif option == "Sunshine":
    filepath = "data/gemeinden_sun.geojson"
    column = "mean_sunshine"
    color = "YlOrBr"
    legend = "Ø Daily Relative Sunshine Duration (%)"
else:
    filepath = "data/gemeinden_rain.geojson"
    column = "mean_rain"
    color = "BuPu"
    legend = "Ø Percipitation (mm)"

#corresponding GeoJSON access
gdf = gpd.read_file(filepath)
#st.write(gdf.head()) 

gdf = gpd.read_file(filepath)
gdf = gdf.to_crs(epsg=4326)

gdf[column] = gdf[column].round(0)

#calculation center
center = [gdf.geometry.unary_union.centroid.y, gdf.geometry.unary_union.centroid.x]
m = folium.Map(location=center, zoom_start=9, tiles="CartoDB positron")

#map
folium.Choropleth(
    geo_data=gdf,
    data=gdf,
    columns=["index", column],
    key_on="feature.properties.index",
    fill_color=color,
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name=legend
).add_to(m)

#tooltip
folium.GeoJson(
    gdf,
    tooltip=folium.GeoJsonTooltip(
        fields=["NOM", column],
        aliases=["Gemeinde:", legend]
    )
).add_to(m)

#show map
st_data = st_folium(m, width=1000, height=650)