import os
import sys

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from matplotlib.patches import Polygon
from shapely.geometry import Polygon as Centroid

import params.config as conf
from src.network import Network
from src.paths import NetworkPath
from src.streets import Streets
from src.uber_areas import UberAreas
from src.uber_rides import UberRides
from src.utils import plot_graph


vienna = nx.Graph()
filepath = os.path.join(conf.root_input, "vienna_statistical_areas.json")

areas = UberAreas(
    filepath=filepath, 
    graph=vienna
)

filepaths = {
    "edges": conf.root_input+"/STRASSENGRAPHOGD.csv",
    "nodes": conf.root_input+"/STRASSENKNOTENOGD.csv"
}

streets = Streets(
    filepaths=filepaths, 
    polygons=areas.polygons
)

network = Network(
    edges=streets.edges, 
    nodes=streets.nodes
)

# Remove pruned nodes & edges also from streets data
streets.nodes = streets.nodes[~streets.nodes.index.isin(network.disconnect_nodes)]
streets.edges = streets.edges[~streets.edges.index.isin(network.disconnect_edges)]

path = NetworkPath()


areas_streets = streets.get_all_areas()

filename = "/vienna-statistical_areas-2020-1-All-DatesByHourBucketsAggregate.csv"
filepath = conf.root_input + filename

uber = UberRides(
    filepath=filepath,
    areas_streets=areas_streets,
    nrows=100
)


# Creat empty lists to store path statistics in
path_summary, path_details = list(), list()

iterations = 100

for _, row in uber.data.head(iterations).iterrows():

    start_area = row["sourceid"]
    end_area = row["dstid"]

    # Get median path
    path.get_median_path(
        Streets=streets, 
        G=network.G, 
        metric="TRAVEL_TIME", 
        area_from=start_area, 
        area_to=end_area, 
        sample_size=3
    )
    
    metric = path.get_areas_by_metric(network.G, "TRAVEL_TIME")
    metric = metric.reindex(areas_streets).fillna(0)
    summary = path.get_summary(network.G)

    path_summary.append(summary)
    path_details.append(metric)
    
# Transform lists/dicts into dataframes to later merge with uber data
path_summary = pd.DataFrame(path_summary)
path_details = pd.DataFrame(path_details)