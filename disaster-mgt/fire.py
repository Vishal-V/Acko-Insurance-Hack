import numpy as np
import os
import sys
import pandas as pd
import folium
import matplotlib.pyplot as plt
from folium import FeatureGroup, LayerControl, Map, Marker
# Importing the dataset
def firepred():
	dataset = pd.read_csv('MODIS.csv')
	X = dataset.iloc[:, 0:2].values
	print(X)
	from sklearn.cluster import KMeans
	kmeans = KMeans(n_clusters = 5, init = 'k-means++', random_state = 42)
	y_kmeans = kmeans.fit_predict(X)
	
	import folium
	from folium import plugins
	
	map = folium.Map(location=[21, 77], zoom_start=5, tiles='Stamen Terrain')
	# Draw markers on the map.
	for name, row in dataset.iterrows():
	    if row["brightness"]:
	        folium.CircleMarker(location=[row['latitude'],row['longitude']],radius=3,color="#7C0A02",opacity=0.5,popup='<i> Fire </	i>').add_to(map)
	# Create and show the map.
	map.save('templates/fire.html')
	map

