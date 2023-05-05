import json
import os
from typing import Dict, List, Tuple

import networkx as nx
import pandas as pd
import pickle

import params.config as conf

class UberAreas:
    """A class used to represent the sub-districts Uber has split the city into.
    
    Attributes:
        data (pd.DataFrame): Contains all area information.
        pos (Dict[str, Tuple[float, float]]): Coordinates for each point of the areas.
        polygons (Dict[str, List[Tuple[float, float]]]): List of coordinates for each polygon stored 
            in a dict.
    """

    def __init__(self, filepath: str, graph: nx.Graph) -> None:
        self.load_data(filepath)
        self.load_graph(graph)
        self.write_to_pickle()
        
    def load_data(self, filepath: str) -> pd.DataFrame:
        """Loads information from a JSON file into a DataFrame."""
        
        with open(filepath) as f:
            self.data = json.load(f)

        return self.data

    def load_graph(self, graph: nx.Graph) -> None:
        """Loads a network graph depicting area borders as edges."""

        self.pos = dict()
        self.polygons = dict()
        districts = len(self.data["features"])

        for i in range(districts):

            # Get shape information from file
            nodes   = self.data["features"][i]["geometry"]["coordinates"][0]
            area_id = self.data["features"][i]["properties"]["MOVEMENT_ID"].zfill(4) 

            # Convert list of lists to list of tuples (lng, lat)
            nodes = list(map(tuple, nodes))                           

            # Prune nodes and remove last node (duplicate of first node)
            nodes = list(map(lambda x: (x[:2]), nodes))         
            nodes = nodes[:-1]

            # Add polygon with node-coordinates to dict
            self.polygons[area_id] = nodes

            for j,k in enumerate(nodes):
                self.pos[area_id+"-"+str(j)]=(k[0], k[1])

            for j in range(len(nodes)-1):
                graph.add_edge(
                    u_of_edge=area_id+"-"+str(j), 
                    v_of_edge=area_id+"-"+str(j+1))

            graph.add_edge(
                u_of_edge=area_id+"-"+str(len(nodes)-1), 
                v_of_edge=area_id+"-"+str(0))

    def write_to_pickle(self):
        """Save object as pickle in output location."""
 
        with open(os.path.join(conf.root_output, "areas.pickle"), "wb") as f:
            pickle.dump(self, f)
