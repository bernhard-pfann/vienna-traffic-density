import argparse
import os

import networkx as nx
import pandas as pd
from tqdm import tqdm

import params.config as conf
from src.network import Network
from src.paths import NetworkPath
from src.streets import Streets
from src.uber_areas import UberAreas
from src.uber_rides import UberRides
from src.optimize import optimizer

def main2():

    filepath = os.path.join(conf.root_output, "coefs.csv")

    coefs = optimizer()
    coefs.to_csv(filepath, sep=",", index=True)
    print("LOL")

def main():

    # Argument parser for number of iterations
    parser = argparse.ArgumentParser()
    parser.add_argument('--iter', type=int, default=20, help='Number of paths to calculate')
    args = parser.parse_args()
    n_iter = args.iter

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
    export(X=X, y=y, meta=meta)    
    print("DONE")


def export(X: pd.DataFrame, y: pd.DataFrame, meta: pd.DataFrame) -> None:
    """Write files to output location for further analysis."""

    X_path    = os.path.join(conf.root_output, "csv", "X.csv")
    y_path    = os.path.join(conf.root_output, "csv", "y.csv")

    X.to_csv(X_path, sep=",", index=False)
    y.to_csv(y_path, sep=",", index=False)
    print("Files written to {}".format(conf.root_output))


if __name__ == "__main__":
    main()
