# Libraries for data processing & network analysis
import numpy as np
import pandas as pd
import networkx as nx

# Libraries for colors
import seaborn as sns
from matplotlib.cm import register_cmap
from matplotlib.colors import LinearSegmentedColormap


class Network(object):
    """
    A class that stores and updates the network based on the official street network of the City of Vienna,
    mapped with the defined areas by Uber Movements.
    
    Attributes
    ----------
    G : nx.Graph
    disconnect_nodes : list
    disconnect_edges : list    
    colors : list
    
    Methods
    -------
    initialize(Streets):
        Create network graph with data from Streets module
    random_node():
        Return a random node from the network
    random_edge():
        Return a random edge from the network
    disconnected():
        Return a list of nodes, that are not connected to the main (largest network)
    prune():
        Prunes the network based on the provided list of nodes
    color_init():
        Sets the color all network edges equal to gray
    color_by_attr(Streets, attr):
        Set the color of all network edges according to an edge-attribute
    color_by_path(path, color, write_all):
        Set the color of network edges of a specified path 
    """
    
    def initialize(self, Streets):
        """
        Create network graph with data from Streets module.
        
        Parameters
        ----------
        Streets : pd.DataFrame
        """
        
        # Initialize graph with edge attributes from dataframe
        self.G = nx.from_pandas_edgelist(
            df=Streets.edges, 
            source='NODE_FROM', 
            target='NODE_TO', 
            edge_attr=True)
        
        # Add area as node attribute
        nx.set_node_attributes(
            G=self.G, 
            values=Streets.nodes["AREA"].to_dict(), 
            name="AREA")
        
        # Standard color for edges
        self.color_init()
        
         
    def random_node(self):
        """Return a random node from the network"""
        
        nodes = list(self.G.nodes)
        idx = np.random.randint(len(self.G.nodes))
        return nodes[idx]


    def random_edge(self):
        """Return a random edge from the network"""
        
        edges = list(self.G.edges())
        idx  = np.random.randint(len(self.G.edges))
        return edges[idx]
    
    
    def disconnected(self):
        """Return a list of nodes, that are not connected to the main (largest network)"""
        
        main_nodes = list(max(nx.connected_components(self.G)))
        all_nodes  = list(self.G.nodes())

        self.disconnect_nodes = list(set(all_nodes) - set(main_nodes))
        self.disconnect_edges = list(self.G.edges(self.disconnect_nodes))

    def prune(self):
        """Prunes the network based on the provided list of nodes"""
        
        self.disconnected()
        
        for i in self.disconnect_edges:
            self.G.remove_edge(i[0], i[1])
    
        for i in self.disconnect_nodes:
            self.G.remove_node(i)
            
        self.color_init()
        
    
    def color_init(self):
        """Sets the color all network edges equal to gray"""
        
        self.colors = ["darkgray"]*len(self.G.edges)


    def color_by_attr(self, Streets, attr):
        """
        Set the color of all network edges according to an edge-attribute.
        
        Parameters
        ----------
        Streets : pd.DataFrame
        attr : str
        """
        
        # Unique categories of attribute
        attr_unique = np.unique(Streets.edges[attr])

        # Dict mapping categories with color palette of same length
        Colors = NetworkColors()
        palette = Colors.get_cpal(len(attr_unique))
        hex_dict = {j: palette[i] for i,j in enumerate(attr_unique)}

        # Iterate through edges and map color dict to it
        edges = nx.get_edge_attributes(self.G, attr)

        for key, val in edges.items():
            edges[key] = hex_dict[edges[key]]

        self.colors = list(edges.values())


    def color_by_path(self, path, color, write_all):    
        """
        Set the color of network edges of a specified path.
        
        Parameters
        ----------
        path : list
        color : hex/rgb-code
        write_all : bool
        """
        if write_all==True:
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

        

###################################################################################################



class NetworkPath(object):
    """
    A class that calculates paths within the network, and holds its properties.
    
    Attributes
    ----------
    edges : list
    nodes : list
    edge_data : dict
    crossings : int
    distance : float
    travel_time : float
    summary : dict
    areas_unique: list
    areas_count: pd.Series
    areas_metric: pd.Series
    
    Methods
    -------
    shortest_path(G, start_node, end_node, metric):
        A function that calculates the shortest path by minimizing a metric 
        (distance, travel_time)
    path_stats(G):
        A function that calculates basic statistics on the calculated path 
        (crossings, total distance, total travel_time)
    path_areas(G, metric):
        A function that calculates statistics on the calculated path per area
        (unique, by count, by metric)
    median_path(G, Streets, metric, area_from, area_to, sample_size):
        A function that executes the shortest_path algorithm multiple times, 
        to return the path of medium length. At each iteration a random starting &
        ending node from the respective starting & ending areas are being selected
    get_limits(Streets):
        A function that returns the limits for x&y axis for plotting 
        the currently selected path
    """

    def shortest_path(self, G, start_node, end_node, metric):
        """
        A function that calculates the shortest path by minimizing a metric 
        (distance, travel_time).
        
        Parameters
        ----------
        G : nx.Graph
        start_node : int
        end_node : int
        metric : str
        """
        self.edges = list()
        self.nodes = nx.shortest_path(
            G=G, 
            source=start_node,
            target=end_node,
            weight=metric)

        # Transform list of nodes to list of edge keys (check both directions)    
        for i in range(len(self.nodes)-1):
            key     = (self.nodes[i], self.nodes[i+1])
            key_rev = (self.nodes[i+1], self.nodes[i])

            if key in list(G.edges()):
                self.edges.append(key)
            else:
                self.edges.append(key_rev)
                
        self.path_stats(G=G)
        self.path_areas(G=G, metric="DISTANCE")
        
        

    def path_stats(self, G):
        """
        A function that calculates basic statistics on the calculated path 
        (crossings, total distance, total travel_time)
        
        Parameters
        ----------
        G : nx.Graph
        """
        
        # Get all attributes of route edges
        self.edge_data = {i: G.get_edge_data(i[0], i[1]) for i in self.edges}

        # Number of crossings on route
        self.crossings = len(self.edges)

        # Distance in meters on route
        self.distance = [i["DISTANCE"] for i in self.edge_data.values()]
        self.distance = sum(self.distance)

        # Miniumum travel_time (empty streets)
        self.travel_time = [i["TRAVEL_TIME"] for i in self.edge_data.values()]
        self.travel_time = sum(self.travel_time)

        self.summary = {
            "EST_CROSSINGS":self.crossings,
            "EST_DISTANCE":self.distance,
            "EST_TRAVEL_TIME":self.travel_time}



    def path_areas(self, G, metric):
        """
        A function that calculates statistics on the calculated path per area
        (unique, by count, by metric)
        
        Parameters
        ----------
        G : nx.Graph
        metric : str ("DISTANCE","TRAVEL_TIME")
        """
        
        # Get list of area info for each node
        self.areas = [G.nodes[i]["AREA"] for i in self.nodes]
         
        # Get list of unique areas (sorted by first occurence)
        idx = np.unique(self.areas, return_index=True)[1]
        self.areas_unique = [self.areas[i] for i in sorted(idx)]
        
        # Get list of count per area (sorted by first occurence)
        self.areas_count = pd.Series(self.areas).value_counts(sort=False)
        self.areas_count = self.areas_count.reindex(self.areas_unique)
        
        
        # Get dict of metric per area (where metric can be distance, travel-time etc.)
        self.areas_metric = dict()

        for i in ["AREA_TO", "AREA_FROM"]:
            for j in self.edges:
                key = G.edges[j][i]
                val = G.edges[j][metric]

                if key in self.areas_metric:
                    self.areas_metric[key] += val/2
                else:
                    self.areas_metric[key] = val/2
                    
        # Sort by first occurence
        self.areas_metric = {i: self.areas_metric[i] for i in self.areas_unique}
        
       
    
    def median_path(self, Streets, G, metric, area_from, area_to, sample_size):
        """
        A function that executes the shortest_path algorithm multiple times, 
        to return the path of medium length. At each iteration a random starting &
        ending node from the respective starting & ending areas are being selected.
        
        Parameters
        ----------
        G : nx.Graph
        Streets : pd.DataFrame
        metric : str ("DISTANCE", "TRAVEL_TIME")
        area_from : int (1 - 1370)
        area_to : int (1 - 1370)
        sample_size : int (>3)
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
                metric=metric)

            # Append information of node and metric in lists
            key.append((start_node, end_node))
            val.append(self.summary["EST_"+metric])

        # Get the node from the median path
        start_node, end_node = [x for _, x in sorted(zip(val, key))][sample_size//2]
        
        # Run shortest path for the selected median path
        self.shortest_path(
            G=G, 
            start_node=start_node, 
            end_node=end_node, 
            metric=metric)
        
        
    def get_limits(self, Streets):
        """
        A function that returns the limits for x&y axis for plotting 
        the currently selected path.
        
        Parameters
        ----------
        Streets : pd.DataFrame
        """
        # Get all coordinates for x&y separately
        self.x_coords = [Streets.nodes[Streets.nodes.index==i]["LNG"].item() for i in self.nodes]
        self.y_coords = [Streets.nodes[Streets.nodes.index==i]["LAT"].item() for i in self.nodes]
                    

        xlim = (min(self.x_coords), max(self.x_coords))
        ylim = (min(self.y_coords), max(self.y_coords))

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

            
        
###################################################################################################        
        
    
    
class NetworkColors(object):
    """
    A class that holds and assigns a color map.
    
    Attributes
    ----------
    base_colors : dict
    color_list : list
    cmap : mpl.colormap
    cpal : sns.colorpalette
    
    Methods
    -------
    get_cmap(color_dict):
        A function to set a color map for charts in matplotlib
    get_cpal(n):
        A function to set a color palette for charts in seaborn
    """

    def __init__(self):
        
        self.base_colors = {"orange":"#ffd166", "green":"#06d6a0", "red":"#ef476f"}
        self.get_cmap(self.base_colors)
        
    def get_cmap(self, color_dict):
        """
        A function to set a color map for charts in matplotlib
        
        Parameters
        ----------
        color_dict : dict
        """
        
        self.color_list = list(color_dict.values())
        self.cmap = LinearSegmentedColormap.from_list(name="custom", colors=self.color_list)
        register_cmap("vienna-roads", self.cmap)

    # Color palette for seaborn
    def get_cpal(self, n):
        """
        A function to set a color palette for charts in seaborn.
        
        Parameters
        ----------
        n : int
        """
        
        self.cpal = sns.color_palette(palette="vienna-roads", n_colors=n, desat=1)
        return self.cpal