from typing import List

import networkx as nx
import numpy as np
import pandas as pd

from src.utils import get_colors


class Network:
    """
    A class that stores and updates the network based on the official street network of the City of 
    Vienna, mapped with the defined areas by Uber Movements.

    Attributes:
        G (nx.Graph): The network graph.
        disconnect_nodes (list): A list of nodes that are not connected to the main network.
        disconnect_edges (list): A list of edges that are not connected to the main network.
        colors (list): A list of colors to be used to color the network edges.
    """
    
    def __init__(self, edges: pd.DataFrame, nodes: pd.DataFrame) -> None:
        """Create network graph with data from Streets module.

        Args:
            edges (pd.DataFrame): DataFrame containing edges.
            nodes (pd.DataFrame): DataFrame with column 'AREA' containing nodes information.
        """
        # Set edges
        self.G = nx.from_pandas_edgelist(
            df=edges, 
            source='NODE_FROM', 
            target='NODE_TO', 
            edge_attr=True
        )
        # Set node attributes
        nx.set_node_attributes(
            G=self.G, 
            values=nodes["AREA"].to_dict(), 
            name="AREA"
        )
        # Prune network if not fully connected
        if not nx.is_connected(self.G):
            self.get_disconnected_nodes()
            self.get_disconnected_edges()
            self.drop_disconnected()        

        # Standard color for all edges
        self.color_init()

    def get_disconnected_nodes(self) -> None:
        """Identifies nodes that are not part of the main connected network."""
        
        main_nodes = list(max(nx.connected_components(self.G)))
        all_nodes  = list(self.G.nodes())

        self.disconnected_nodes = list(set(all_nodes) - set(main_nodes))

    def get_disconnected_edges(self) -> None:
        """Identifies edges that are linked to disconnected nodes."""

        self.disconnected_edges = list(self.G.edges(self.disconnected_nodes))

    def drop_disconnected(self) -> None:
        """Drop all disconnected edges and nodes to retain a fully connected network."""

        for i in self.disconnected_edges:
            self.G.remove_edge(i[0], i[1])
    
        for i in self.disconnected_nodes:
            self.G.remove_node(i)

    def random_node(self) -> int:
        """Return a random node from the network."""
        
        nodes = list(self.G.nodes)
        idx = np.random.randint(len(self.G.nodes))
        return nodes[idx]

    def random_edge(self) -> tuple:
        """Return a random edge from the network."""
        
        edges = list(self.G.edges())
        idx  = np.random.randint(len(self.G.edges))
        return edges[idx]

    def color_by_attr(self, edges: pd.DataFrame, attr: str) -> None:
        """Set the color of all network edges according to an edge-attribute.

        Args:
            edges (pd.DataFrame): DataFrame containing streets edge data.
            attr (str): The edge attribute to use for coloring the network.
        """
        attrs = np.unique(edges[attr])
        palette = get_colors(len(attrs))
        hex_dict = {j: palette[i] for i,j in enumerate(attrs)}

        # Iterate through edges and map color dict to it
        edges = nx.get_edge_attributes(self.G, attr)

        for key in edges.keys():
            edges[key] = hex_dict[edges[key]]

        self.colors = list(edges.values())

    def color_by_path(self, path: List[int], color: str) -> None:    
        """Sets the color of network edges of a specified path.
        
        Args:
            path (List[int]): List of integers that indicate the path of a trip.
            color (str): The HEX/RGB-code for coloring the path
        """
        # Clear existing coloring
        self.color_init()
        
        # Retrieve dict of edge keys from network
        path_rev = [i[::-1] for i in path]
        hex_list = list()

        for i,j in enumerate(list(self.G.edges())):
            if (j in path) or (j in path_rev):
                hex_list.append(color)
            else:
                hex_list.append(self.colors[i])

        self.colors = hex_list

    def color_init(self) -> None:
        """Sets the color all network edges equal to gray."""
        
        self.colors = ["darkgray"]*len(self.G.edges)
