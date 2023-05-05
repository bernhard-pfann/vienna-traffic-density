from typing import Tuple

import pandas as pd
import networkx as nx
from tqdm import tqdm

import params.config as conf
from src.network import Network
from src.network_paths import NetworkPath
from src.streets import Streets
from src.uber_areas import UberAreas
from src.uber_rides import UberRides


def pathfinder(n_iter: int) -> Tuple[pd.DataFrame, pd.Series]:
    """Calculate shortest paths between Uber areas based on travel time.

    Args:
        n_iter (int): The number of iterations to perform.

    Returns:
        Tuple[pd.DataFrame, pd.Series]: A tuple containing two objects:
            1. A pandas DataFrame containing the travel times between each pair of Uber areas,
            indexed by the area IDs.
            2. A pandas Series containing the target variable for the first n_iter Uber rides.
    """
    # Areas defined by Uber
    areas = UberAreas(
        filepath=conf.input_paths["areas"], 
        graph=nx.Graph()
    )
    # Streets and crossings from city of Vienna
    streets = Streets(
        filepaths=conf.input_paths, 
        polygons=areas.polygons
    )
    # Build graph on streets and crossings
    network = Network(
        edges=streets.edges, 
        nodes=streets.nodes
    )
    # Drop all disconnected edges and nodes that are not part of the main network
    streets.drop_disconnected(
        disconnected_edges=network.disconnected_edges,
        disconnected_nodes=network.disconnected_nodes
    )
    # All uber areas that are present in the netowrk of streets and crossings
    areas_in_network = streets.get_all_areas()

    # Collection of uber rides with start, destionatio and travel times
    uber = UberRides(
        filepath=conf.input_paths["rides"],
        areas_in_network=areas_in_network
    )
    # Instance for shortest path calcuations
    path = NetworkPath()

    X    = list()
    y    = uber.data.head(n_iter)[conf.target]
    meta = uber.data.head(n_iter).drop(columns=conf.target)

    # Path calculation
    for _, row in tqdm(meta.iterrows(), total=n_iter):

        start_area = row["sourceid"]
        end_area = row["dstid"]

        path.get_median_path(
            Streets=streets, 
            G=network.G, 
            metric="TRAVEL_TIME", 
            area_from=start_area, 
            area_to=end_area, 
            sample_size=3
        )
        
        x_i = path.get_areas_by_metric(network.G, "TRAVEL_TIME")
        x_i = x_i.reindex(areas_in_network).fillna(0)
        X.append(x_i)

    X = pd.DataFrame(X)
    return X, y
