import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox
from descartes import PolygonPatch
from shapely.geometry import Point, LineString, Polygon
import streamlit as st

ox.settings.log_console = True
ox.settings.use_cache = True
ox.__version__

def main():
    # streamlit settings
    place = st.text_input('Select the location. Use OpenStreetMap.org to find a good search query.', 'Toronto, Ontario, Canada')

    network_type = st.selectbox(
        'Which network would you like to use?',
        ('walk', 'bike', 'drive'))

    time_values = st.slider(
        'Select a range of travel times (in minutes).',
        0, 60, (0, 30))

    travel_speed = st.slider(
        'Select a travel speed (in km/hour).',
        0.1, 120.0)

    trip_times = list(range(time_values[0], time_values[1], 5))

    if st.button('Create isochrome'):
        with st.spinner("Processing data"):
            fig = create_isochrome(network_type=network_type, travel_speed=travel_speed, place=place, trip_times=trip_times)
            st.balloons()
            st.pyplot(fig)


def create_isochrome(network_type, travel_speed, place, trip_times):

    # download the street network
    G = ox.graph_from_place(place, network_type=network_type)


    # find the centermost node and then project the graph to UTM
    gdf_nodes = ox.graph_to_gdfs(G, edges=False)
    x, y = gdf_nodes['geometry'].unary_union.centroid.xy
    center_node = ox.nearest_nodes(G, x[0], y[0])
    G = ox.project_graph(G)


    # add an edge attribute for time in minutes required to traverse each edge
    meters_per_minute = travel_speed * 1000 / 60 #km per hour to m per minute
    for u, v, k, data in G.edges(data=True, keys=True):
        data['time'] = data['length'] / meters_per_minute


    # get one color for each isochrone
    iso_colors = ox.plot.get_colors(n=len(trip_times), cmap='plasma', start=0, return_hex=True)


    # color the nodes according to isochrone then plot the street network
    node_colors = {}
    for trip_time, color in zip(sorted(trip_times, reverse=True), iso_colors):
        subgraph = nx.ego_graph(G, center_node, radius=trip_time, distance='time')
        for node in subgraph.nodes():
            node_colors[node] = color
    nc = [node_colors[node] if node in node_colors else 'none' for node in G.nodes()]
    ns = [15 if node in node_colors else 0 for node in G.nodes()]
    fig, ax = ox.plot_graph(G, node_color=nc, node_size=ns, node_alpha=0.8, node_zorder=2,
                            bgcolor='k', edge_linewidth=0.2, edge_color='#999999')
    return fig


if __name__ == "__main__":
    main()