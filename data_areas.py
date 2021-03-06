import json

class Areas(object):
    """
    A class used to represent the sub-districts Uber has split the city into.
    
    Attributes
    ----------
    data : pd.DataFrame
        Containing all area information
    positions : dict
        Coordinates for each point of the areas polygons
    polygons : dict
        List of coordinates for each polygon stored in a dict 
    
    
    Methods
    -------
    load_data(filename):
        Loads informatio from json into a DataFrame
    load_graph(graph):
        Loads a networkgraph depicting area borders as edges
    """
    
    def load_data(self, filename):
        """
        Loads informatio from json into a DataFrame.
        
        Parameters
        ----------
        filename: str
        """
        
        with open("./input/"+filename) as f:
            self.data = json.load(f)

        return self.data


    def load_graph(self, graph):
        """
        Loads a networkgraph depicting area borders as edges
        
        Paramters
        ---------
        graph : nx.Graph 
        """
        
        self.positions =dict()
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
                self.positions[area_id+"-"+str(j)]=(k[0], k[1])

            for j in range(len(nodes)-1):
                graph.add_edge(
                    u_of_edge=area_id+"-"+str(j), 
                    v_of_edge=area_id+"-"+str(j+1))

            graph.add_edge(
                u_of_edge=area_id+"-"+str(len(nodes)-1), 
                v_of_edge=area_id+"-"+str(0))