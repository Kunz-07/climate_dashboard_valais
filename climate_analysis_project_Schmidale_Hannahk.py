# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import os
import pandas as pd
import numpy as np
import geopandas as gdp
import matplotlib.pyplot as plt
import folium
from geopandas.tools import sjoin

#Die drei csv-Dateien laden und bereinigen

df_Temperature = pd.read_csv('MeteoSwiss_Temperature.csv')
df_Rain = pd.read_csv('MeteoSwiss_Rain.csv')
df_Sunshine = pd.read_csv('MeteoSwiss_Sunshine.csv')
df_Temperature.dropna(inplace=True)
df_Rain.dropna(inplace=True)
df_Sunshine.dropna(inplace=True)

#Die drei csv-Dateien zusammenführen

df_merged = pd.merge(df_Temperature, df_Rain, on=['time', 'lon', 'lat'], how='inner')
df_merged = pd.merge(df_merged, df_Sunshine, on=['time', 'lon', 'lat'], how='inner')

print(df_merged.head())

def create_geodataframe(df_merged):
    gdf = gdp.GeoDataFrame(
        df_merged.copy(),
        geometry=gdp.points_from_xy(df_merged['lon'],df_merged['lat']),
        crs="EPSG:4326"
    )
    return gdf

gdf = create_geodataframe(df_merged)
gdf.to_file('climate_data.shp')

#Fokus auf Kanton Graubünden

kantone = gdp.read_file('TLM_KANTONSGEBIET.shp')
wallis = kantone[kantone['NAME'] == 'Valais']

gdf = gdp.GeoDataFrame(
    df_merged.copy(),
    geometry=gdp.points_from_xy(df_merged['lon'], df_merged['lat']),
    crs="EPSG:4326"
)

#CRS kontrollieren

gdf = gdf.to_crs(wallis.crs)

#Punkte im Kanton Graubünden wählen

wallis = wallis[['geometry']]
gdf_wallis = sjoin(gdf, wallis, predicate='within', how='inner')


print(gdf_wallis.head())
gdf_wallis.to_file("climate_data_wallis.shp")

#Gemeindegrenzen laden


# Gemeindegrenzen als Linien laden
gemeinden_vs = gdp.read_file("Communes.shp")

# CRS anpassen
gemeinden_vs = gemeinden_vs.to_crs(wallis.crs)


# CRS angleichen (falls nötig)
gemeinden_vs = gemeinden_vs.to_crs(gdf_wallis.crs)



gemeinden_vs = gemeinden_vs.to_crs(gdf_wallis.crs)



gdf_wallis = gdf_wallis.to_crs(gemeinden_vs.crs)


gemeinden_vs = gemeinden_vs[['geometry']]

# Entferne 'index_right', falls sie noch vom vorherigen Join existiert
if 'index_right' in gdf_wallis.columns:
    gdf_wallis = gdf_wallis.drop(columns='index_right')

# Räumlicher Join: welche Messstation liegt in welcher Gemeinde
gdf_with_gemeinde = sjoin(gdf_wallis, gemeinden_vs, predicate='within', how='inner')


print("Anzahl Treffer im Join:", len(gdf_with_gemeinde))
print(gdf_with_gemeinde.head())

gdf_with_gemeinde.to_file("gdf_with_gemeinde.shp")

if 'level_0' in gemeinden_vs.columns:
    gemeinden_vs = gemeinden_vs.drop(columns='level_0')
if 'index' in gemeinden_vs.columns:
    gemeinden_vs = gemeinden_vs.drop(columns='index')

from matplotlib_scalebar.scalebar import ScaleBar


# EINMAL resetten und merken
gemeinden_reset = gemeinden_vs.reset_index(drop=False)

# Temperatur
mean_temp_per_gemeinde = gdf_with_gemeinde.groupby('index_right')['TabsD'].mean().reset_index()
mean_temp_per_gemeinde.rename(columns={'TabsD': 'mean_temperature'}, inplace=True)
gemeinden_temp = gemeinden_reset.merge(mean_temp_per_gemeinde, left_on='index', right_on='index_right')

fig, ax = plt.subplots(figsize=(10, 10))
gemeinden_temp.plot(column='mean_temperature', cmap='coolwarm', legend=True, ax=ax)
ax.set_title('Average Temperature (°C) January per Municipality')
plt.axis('off')

ax.annotate('N', xy=(0.95, 0.15), xytext=(0.95, 0.05),
            arrowprops=dict(facecolor='black', width=5, headwidth=15),
            ha='center', va='center', fontsize=12, xycoords='axes fraction')

scalebar_length = 10000  # in Meter (10 km)
xmin, xmax = ax.get_xlim()
ymin, ymax = ax.get_ylim()
bar_x = xmin + (xmax - xmin) * 0.05
bar_y = ymin + (ymax - ymin) * 0.05

# Linie + Text
ax.plot([bar_x, bar_x + scalebar_length], [bar_y, bar_y], color='black', linewidth=3)
ax.text(bar_x + scalebar_length / 2, bar_y + scalebar_length * 0.002, '10 km',
        ha='center', va='bottom', fontsize=10)

plt.show()
gemeinden_temp.to_file("mean_temperature_per_gemeinde.shp")
fig.savefig("mean_temperature_per_gemeinde.pdf", bbox_inches='tight', dpi=300)

# Sonnenscheindauer
mean_sun_per_gemeinde = gdf_with_gemeinde.groupby('index_right')['SrelD'].mean().reset_index()
mean_sun_per_gemeinde.rename(columns={'SrelD': 'mean_sunshine'}, inplace=True)
gemeinden_sun = gemeinden_reset.merge(mean_sun_per_gemeinde, left_on='index', right_on='index_right')

fig, ax = plt.subplots(figsize=(10, 10))
gemeinden_sun.plot(column='mean_sunshine', cmap='YlOrBr', legend=True, ax=ax)
ax.set_title('Average Daily Relative Sunshine Duration (%) in January per Municipality')
plt.axis('off')

ax.annotate('N', xy=(0.95, 0.15), xytext=(0.95, 0.05),
            arrowprops=dict(facecolor='black', width=5, headwidth=15),
            ha='center', va='center', fontsize=12, xycoords='axes fraction')

scalebar_length = 10000  # in Meter (10 km)
xmin, xmax = ax.get_xlim()
ymin, ymax = ax.get_ylim()
bar_x = xmin + (xmax - xmin) * 0.05
bar_y = ymin + (ymax - ymin) * 0.05

# Linie + Text
ax.plot([bar_x, bar_x + scalebar_length], [bar_y, bar_y], color='black', linewidth=3)
ax.text(bar_x + scalebar_length / 2, bar_y + scalebar_length * 0.002, '10 km',
        ha='center', va='bottom', fontsize=10)

plt.show()
gemeinden_sun.to_file("mean_sunshine_per_gemeinde.shp")
fig.savefig("mean_sunshine_per_gemeinde.pdf", bbox_inches='tight', dpi=300)

# Rain
mean_rain_per_gemeinde = gdf_with_gemeinde.groupby('index_right')['RhiresD'].mean().reset_index()
mean_rain_per_gemeinde.rename(columns={'RhiresD': 'mean_rain'}, inplace=True)
gemeinden_rain = gemeinden_reset.merge(mean_rain_per_gemeinde, left_on='index', right_on='index_right')

gemeinden_rain_plot = gemeinden_rain.to_crs(epsg=2056)

fig, ax = plt.subplots(figsize=(10, 10))
gemeinden_rain.plot(column='mean_rain', cmap='Blues', legend=True, ax=ax)
ax.set_title('Average Percipitation (mm) in January per Municipality')
plt.axis('off')

ax.annotate('N', xy=(0.95, 0.15), xytext=(0.95, 0.05),
            arrowprops=dict(facecolor='black', width=5, headwidth=15),
            ha='center', va='center', fontsize=12, xycoords='axes fraction')

scalebar_length = 10000  # in Meter (10 km)
xmin, xmax = ax.get_xlim()
ymin, ymax = ax.get_ylim()
bar_x = xmin + (xmax - xmin) * 0.05
bar_y = ymin + (ymax - ymin) * 0.05

# Linie + Text
ax.plot([bar_x, bar_x + scalebar_length], [bar_y, bar_y], color='black', linewidth=3)
ax.text(bar_x + scalebar_length / 2, bar_y + scalebar_length * 0.002, '10 km',
        ha='center', va='bottom', fontsize=10)

plt.show()
gemeinden_rain.to_file("mean_rain_per_gemeinde.shp")
fig.savefig("mean_rain_per_gemeinde.pdf", bbox_inches='tight', dpi=300)

os.makedirs("data", exist_ok=True)

# Export als GeoJSON für Streamlit
gemeinden_temp.to_file("gemeinden_temp.geojson", driver="GeoJSON")
gemeinden_sun.to_file("gemeinden_sun.geojson", driver="GeoJSON")
gemeinden_rain.to_file("gemeinden_rain.geojson", driver="GeoJSON")







