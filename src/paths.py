from collections import OrderedDict
from typing import List

import networkx as nx
import pandas as pd


class NetworkPath:
    """
    Calculates paths within the network, and collects its properties.

    Attributes:
        edges (List[Tuple[int, int]]): The edges in the shortest path.
        nodes (List[int]): The nodes in the shortest path.
        edge_data (Dict[Tuple[int, int], Dict[str, Union[int, float]]]): The attributes for each 
            edge in the shortest path.

        crossings (int): The number of times the path crosses an edge.
        distance (float): The total distance of the shortest path.
        travel_time (float): The total travel time of the shortest path.
        summary (Dict[str, Union[int, float]]): A summary of the shortest path, including the number 
            of crossings, distance and travel time.

        areas_unique (List[int]): A list of unique areas the path goes through.
        areas_count (pd.Series): A count of how many times the path goes through each area.
        areas_metric (Dict[int, float]): A dictionary of the total distance or travel time spent in 
            each area.
    """

    def shortest_path(self, G: nx.Graph, start_node: int, end_node: int, metric: str) -> None:
        """
        Calculates the shortest path between two nodes by minimizing a metric.

        Args:
            G (nx.Graph): The network graph.
            start_node (int): The starting node of the path.
            end_node (int): The ending node of the path.
            metric (str): The metric to minimize - "distance" or "travel_time".

        Returns:
            None.
        """
        self.edges = list()
        self.nodes = nx.shortest_path(
            G=G, 
            source=start_node,
            target=end_node,
            weight=metric
        )
        # Transform list of nodes to list of edge keys (check both directions)    
        for i in range(len(self.nodes)-1):
            key = (self.nodes[i], self.nodes[i+1])
            key_rev = (self.nodes[i+1], self.nodes[i])

            if key in list(G.edges()):
                self.edges.append(key)
            else:
                self.edges.append(key_rev)

    def get_median_path(
        self, 
        Streets, 
        G: nx.Graph, 
        metric: str, 
        area_from: int, 
        area_to: int, 
        sample_size: int
    ) -> None:
        """
        Executes the shortest_path algorithm multiple times, to return the path of medium length. 
        At each iteration a random starting & ending node from the respective starting & ending 
        areas are being selected.
        
        Args:
            G (nx.Graph): The network graph.
            Streets (pd.DataFrame): DataFrame of streets.
            metric (str): Options on how to calculate a paths length are ("DISTANCE","TRAVEL_TIME").
            area_from (int): Key of the starting area is between (1 - 1370)
            area_to (int): Key of ending area is between (1 - 1370)
            sample_size (int): Number of paths of sample for median calculation.
        """
        key, val = list(), list()

        # Try out different start & end-points within the start & end areas
        for i in range(sample_size):

            # Get sampled node from start & end area
            start_node = Streets.node_from_area(area=area_from)
            end_node   = Streets.node_from_area(area=area_to)

            # Get shortest path
            self.shortest_path(
                G=G,
                start_node=start_node, 
                end_node=end_node,
                metric=metric
            )
            # Append information of node and metric in lists
            path_len = self.get_summary(G)
            key.append((start_node, end_node))
            val.append(path_len["EST_"+metric])

        # Get the node from the median path
        median_sample = sample_size//2
        start_node, end_node = [x for _, x in sorted(zip(val, key))][median_sample]
        
        # Run shortest path for the selected median path
        self.shortest_path(
            G=G, 
            start_node=start_node, 
            end_node=end_node, 
            metric=metric
        )

    def get_summary(self, G: nx.Graph) -> None:
        """Calculates statistics on the calculated path (crossings, total distance, travel time).

        Args:
            G (nx.Graph): The network graph.
        """
        
        # Get all attributes of route edges
        edge_data = {i: G.get_edge_data(i[0], i[1]) for i in self.edges}

        # Number of crossings on route
        crossings = len(self.edges)

        # Distance in meters on route
        distance = [i["DISTANCE"] for i in edge_data.values()]
        distance = sum(distance)

        # Miniumum travel_time (empty streets)
        travel_time = [i["TRAVEL_TIME"] for i in edge_data.values()]
        travel_time = sum(travel_time)

        return {
            "EST_CROSSINGS": crossings,
            "EST_DISTANCE": distance,
            "EST_TRAVEL_TIME": travel_time
        }

    def get_areas_list(self, G: nx.Graph):
        """
        A list of areas per street during the path. Contains duplicate areas if multiple streets 
        in path are located in same area.
        """
        self.areas_list = [G.nodes[i]["AREA"] for i in self.nodes]
    
    def get_areas_set(self):
        """A set of areas passed during path. It is ordered by first occurence of area key."""

        self.areas_set = list(OrderedDict.fromkeys(self.areas_list))

    def get_areas_count(self, G: nx.Graph) -> pd.Series:
        """Returns a Series which states the number of streets per area on path."""

        self.get_areas_list(G)
        self.get_areas_set()

        areas_count = pd.Series(self.areas_list).value_counts(sort=False)
        areas_count = areas_count.reindex(self.areas_set)        
        
        return areas_count

    def get_areas_by_metric(self, G: nx.Graph, metric: str) -> pd.Series:
        """Returns are dictionary which states the metric per area on path."""

        self.get_areas_list(G)
        self.get_areas_set()

        areas_by_metric = dict()
        for i in ["AREA_TO", "AREA_FROM"]:
            for j in self.edges:
                key = G.edges[j][i]
                val = G.edges[j][metric]

                if key in areas_by_metric:
                    areas_by_metric[key] += val/2
                else:
                    areas_by_metric[key] = val/2
                    
        areas_by_metric = pd.Series({i: areas_by_metric[i] for i in self.areas_set})
        return areas_by_metric
        
    def get_limits(self, nodes: pd.DataFrame) -> None:
        """Returns the limits for x&y axis for plotting the currently selected path.
        
        Args:
            Streets (pd.DataFrame): DataFrame of streets.
        """
        self.x_coords = [nodes[nodes.index==i]["LNG"].item() for i in self.nodes]
        self.y_coords = [nodes[nodes.index==i]["LAT"].item() for i in self.nodes]    
        xspread = max(self.x_coords) - min(self.x_coords)
        yspread = max(self.y_coords) - min(self.y_coords)

        xy_ratio = yspread / xspread
        margin = (0.0007, 0.001) 

        if xy_ratio > 0.7:
            new  = xspread * (xy_ratio/0.7)
            add  = (new - xspread)/2
            self.xlim = (min(self.x_coords)-margin[0]-add, max(self.x_coords)+margin[0]+add)
            self.ylim = (min(self.y_coords)-margin[1],     max(self.y_coords)+margin[1])
        else:
            new  = yspread * (0.7/xy_ratio)
            add  = (new - yspread)/2
            self.ylim = (min(self.y_coords)-margin[1]-add, max(self.y_coords)+margin[1]+add)
            self.xlim = (min(self.x_coords)-margin[0],     max(self.x_coords)+margin[0])
