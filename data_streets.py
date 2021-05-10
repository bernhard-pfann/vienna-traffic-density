# Public libraries
import numpy as np
import pandas as pd
from matplotlib import path
from tqdm.notebook import tqdm

# Custom libraries
import data_streets

class Streets(object):
    """
    A class used to represent all information from the official street network published
    by https://www.data.gv.at/.
    
    Attributes
    ----------
    nodes : pd.DataFrame
        Contains all information of crossings
    edges : pd.DataFrame
        Contains all information of streets that connect crossings
    positions : dict
        Contains LNG/LAT information of each node
   
   
    Methods
    -------
    load_edges(filename):
        A function that imports and cleans the raw input file. This includes dropping irrelevant 
        columns, generating an id, mapping street-types to speed limits.
    load_nodes(filename):
        A function that imports and cleans the raw input file. This includes dropping irrelevant 
        columns and transforming geospacial information.
    drop_nodes():
        A function that drops nodes, which are not connected to any edge
    add_areas(polygons):
        A function that iterates through all nodes, to check within which area they are lying
    file_areas(node):
        A function that assigns an area to a node that has not been assigned yet. Thereby the connected 
        neighbor-nodes' areas are list, and the max count area is being assigned to the initially 
        unassigned area.
    node_from_area(area):
        A function that randomly selectes a node within a specified area.
    """
    
    def load_edges(self, filename):
        """
        A function that imports and cleans the raw input file. This includes dropping irrelevant 
        columns, generating an id, mapping street-types to speed limits.
        
        Parameters
        ----------
        filename : str
        """
        
        # Load edges dataframe
        self.edges = pd.read_csv("input/"+filename, sep=",")

        # Drop irrelevant columns
        self.edges.drop([
            "FID",
            "OBJECTID",
            "GIP_OBJECTID",
            "SE_ANNO_CAD_DATA",
            "MAINNAME_OBJECTID",
            "SHAPE",
            "REG_STRNAME",
            "EDGECATEGORY_NAME",
            "DEDICATEDWIDTH",
            "LEVELINTERMEDIATE",
            "SCD"], axis=1, inplace=True)

        # Rename columns
        self.edges.rename(columns={
            "NODEFROM_OBJECTID":"NODE_FROM",
            "NODETO_OBJECTID":"NODE_TO",
            "FEATURENAME":"STREET_NAME",
            "SHAPELENGTH":"DISTANCE",
            "BEZIRK":"DISTRICT"}, inplace=True)

        # Create custom edge-id
        self.edges.index = list(zip(self.edges["NODE_FROM"], self.edges["NODE_TO"]))

        # Data cleaning
        self.edges["DISTRICT"] = self.edges["DISTRICT"].str[3:5]
        self.edges["DISTRICT"] = self.edges["DISTRICT"].apply(lambda x: "00" if x=="90" else x)

        # Street type & speed limit
        edge_speed = {"G":30, "L":50, "B":70}
        edge_categ = {
            "G":"local-street",
            "L":"main-street",
            "B":"federal-street"}

        self.edges["SPEED"] = self.edges["EDGECATEGORY"].replace(edge_speed)
        self.edges["TRAVEL_TIME"] = self.edges["DISTANCE"]/self.edges["SPEED"]/1000*60*60
        self.edges["STREET_TYPE"] = self.edges["EDGECATEGORY"].replace(edge_categ)


        # Filter out sidewalks and stairs
        self.edges = self.edges[-self.edges["FRC"].isin([10, 45, 12])]
        self.edges = self.edges[-self.edges["FOW"].isin([14, 15, 12,6])]

        # Drop irrelevant columns
        self.edges.drop(["FRC","FRC_NAME","FOW","FOW_NAME", "EDGECATEGORY"], axis=1, inplace=True)


    def load_nodes(self, filename):
        """
        A function that imports and cleans the raw input file. This includes dropping irrelevant 
        columns and transforming geospacial information.
        
        Paramters
        ---------
        filename : str
        """
        
        # Load nodes dataframe
        self.nodes = pd.read_csv("input/"+filename, sep=",")

        # Transform geolocation
        self.nodes["SHAPE"].replace("MULTIPOINT ","", regex=True, inplace=True)
        self.nodes["SHAPE"] = self.nodes["SHAPE"].str.strip('()')
        self.nodes[["LNG", "LAT"]] = self.nodes["SHAPE"].str.split(pat=" ", n=2, expand=True).astype("float")
        self.nodes["POS"] = list(zip(self.nodes["LNG"], self.nodes["LAT"]))

        # Drop irrelevant columns
        self.nodes.drop(["OBJECTID","FID","SHAPE","SE_ANNO_CAD_DATA","NEIGHBORNODE_OBJECTID"], axis=1, inplace=True)
        self.nodes.rename(columns={"FEATURENAME":"STREET_NAME"}, inplace=True)
        self.nodes.set_index(keys="GIP_OBJECTID", drop=True, inplace=True)
        self.nodes.index.name = None

        # Create dict with mapping of geolocation per object
        self.positions = dict()

        for oid, lat, lng in zip (self.nodes.index, self.nodes["LAT"], self.nodes["LNG"]):
            self.positions[oid]=(lng,lat)
            
        
        # Drop nodes that have no associated edges
        self.drop_nodes()
            
            
    def drop_nodes(self):
        """A function that drops nodes, which are not connected to any edge"""
        
        scope = pd.concat(objs=[self.edges["NODE_FROM"], self.edges["NODE_TO"]], axis=0).unique()
        self.nodes = self.nodes[self.nodes.index.isin(scope)]
            

    def add_areas(self, polygons):
        """
        A function that iterates through all nodes, to check within which area they are lying.
        
        Parameters
        ----------
        polygons : dict
            Represents a dictionary of polygon items describing each areas boundaries
        """
        sub_districts = list()

        for i in tqdm(self.nodes["POS"]):
            for key,val in polygons.items():
                p = path.Path(val)
                check = p.contains_points([i])

                if check == True:
                    sub_districts.append(key)
                    break

            if check == False:
                sub_districts.append(None)
                
        self.nodes["AREA"] = sub_districts

        # Fill node areas where None
        self.nodes["AREA"] = self.nodes.apply(lambda x: self.fill_areas(x.name) if x["AREA"]==None else x["AREA"], axis=1)
        
        # Merge area information to start-node and end-node to each edge
        self.edges = self.edges.merge(self.nodes["AREA"], left_on="NODE_FROM", right_index=True, how="left")
        self.edges = self.edges.merge(self.nodes["AREA"], left_on="NODE_TO", right_index=True, how="left")

        # Rename area columns
        self.edges.rename(columns={"AREA_x":"AREA_FROM", "AREA_y":"AREA_TO"}, inplace=True)
        
        # Fill edges areas where None
        self.edges["AREA_TO"]   = np.where(self.edges["AREA_TO"].isnull(), self.edges["AREA_FROM"], self.edges["AREA_TO"])
        self.edges["AREA_FROM"] = np.where(self.edges["AREA_FROM"].isnull(), self.edges["AREA_TO"], self.edges["AREA_FROM"])
        

        
    def fill_areas(self, node):
        """
        A function that assigns an area to a node that has not been assigned yet. Thereby the connected neighbor-nodes'
        areas are list, and the max count area is being assigned to the initially unassigned area.
        
        Parameters
        ----------
        node : int
        """
        
        try:
            n_from = list(self.edges[self.edges["NODE_FROM"]==node]["NODE_TO"])
            n_to   = list(self.edges[self.edges["NODE_TO"]==node]["NODE_FROM"])
            n_connect = n_from + n_to

            n_areas = self.nodes[self.nodes.index.isin(n_connect)]["AREA"]
            n_areas = n_areas.dropna()

            return max(list(n_areas))

        except: return None
        
        
        
    def node_from_area(self, area):
        """
        A function that randomly selectes a node within a specified area.
        
        Parameters
        ----------
        area : int
        """
        temp = self.nodes[self.nodes["AREA"]==area]
        idx = np.random.randint(len(temp))

        return temp.index[idx]