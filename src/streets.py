from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from matplotlib import path


class Streets:
    """
    A class used to represent all information from the official street network published
    by https://www.data.gv.at/.
    
    Attributes
        nodes (pd.DataFrame): Contains all information of crossings
        edges (pd.DataFrame): Contains all information of streets that connect crossings
        pos (dict): Contains LNG/LAT information of each node   
    """
    def __init__(self, filepaths: Dict[str, str], polygons) -> None:
        self.edges = self.load_edges(filepaths["edges"])
        self.nodes = self.load_nodes(filepaths["nodes"])
        self.pos = self.get_pos()
        
        self.drop_nodes()
        self.add_areas(polygons)

    def load_edges(self, filepath: str) -> pd.DataFrame:
        """
        Imports and cleans the raw input file. This includes dropping irrelevant columns, 
        generating an id, and mapping street-types to speed limits.
        """
        df = pd.read_csv(filepath, sep=",")
        df.drop([
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
            "SCD"
        ], axis=1, inplace=True)

        df.rename(columns={
            "NODEFROM_OBJECTID":"NODE_FROM",
            "NODETO_OBJECTID":"NODE_TO",
            "FEATURENAME":"STREET_NAME",
            "SHAPELENGTH":"DISTANCE",
            "BEZIRK":"DISTRICT"
        }, inplace=True)

        # Create custom edge-id
        df.index = list(zip(df["NODE_FROM"], df["NODE_TO"]))
        df.index.name = "id"

        df["DISTRICT"] = df["DISTRICT"].str[3:5]
        df["DISTRICT"] = df["DISTRICT"].apply(lambda x: "00" if x=="90" else x)

        # Street type & speed limit
        speed = {"G": 30, "L": 50, "B": 70}
        categories = {
            "G":"local-street",
            "L":"main-street",
            "B":"federal-street"
        }
        df["SPEED"] = df["EDGECATEGORY"].replace(speed)
        df["TRAVEL_TIME"] = df["DISTANCE"]/df["SPEED"]/1000*60*60
        df["STREET_TYPE"] = df["EDGECATEGORY"].replace(categories)

        # Filter out sidewalks and stairs
        df = df[-df["FRC"].isin([10, 45, 12])]
        df = df[-df["FOW"].isin([14, 15, 12,6])]
        df.drop([
            "FRC",
            "FRC_NAME",
            "FOW",
            "FOW_NAME", 
            "EDGECATEGORY"
        ], axis=1, inplace=True)

        return df

    def load_nodes(self, filepath: str) -> pd.DataFrame:
        """
        Imports and cleans the raw input file. This includes dropping irrelevant columns and 
        transforming geospacial information.
        """
        df = pd.read_csv(filepath, sep=",")
        df["SHAPE"].replace("MULTIPOINT ","", regex=True, inplace=True)
        df["SHAPE"] = df["SHAPE"].str.strip('()')
        df[["LNG", "LAT"]] = df["SHAPE"].str.split(pat=" ", n=2, expand=True).astype("float")
        df["POS"] = list(zip(df["LNG"], df["LAT"]))

        df.drop([
            "OBJECTID",
            "FID",
            "SHAPE",
            "SE_ANNO_CAD_DATA",
            "NEIGHBORNODE_OBJECTID"
        ], axis=1, inplace=True)

        df.rename(columns={"FEATURENAME": "STREET_NAME"}, inplace=True)
        df.set_index(keys="GIP_OBJECTID", drop=True, inplace=True)
        df.index.name = "id"

        return df

    def get_pos(self) -> Dict[int, Tuple[float, float]]:
        """Return a dictionary of positions for plotting."""

        pos = dict()
        for oid, lat, lng in zip(
            self.nodes.index, 
            self.nodes["LAT"], 
            self.nodes["LNG"]
        ):
            pos[oid] = (lng, lat)

        return pos
            
    def drop_nodes(self):
        """A function that drops nodes, which are not connected to any edge."""
        
        all_nodes = pd.concat(objs=[
            self.edges["NODE_FROM"], 
            self.edges["NODE_TO"]
        ], axis=0).unique()

        self.nodes = self.nodes[self.nodes.index.isin(all_nodes)]

    def add_areas(self, polygons: Dict[str, list]) -> None:
        """Iterates through all nodes, to check within which area they are lying.

        Args:
            polygons (Dict[str, list]): A dictionary of polygons describing an area's boundaries.
        """
        sub_districts = list()

        for i in self.nodes["POS"]:
            for key,val in polygons.items():
                p = path.Path(val)
                check = p.contains_points([i])

                if check == True:
                    sub_districts.append(key)
                    break

            if check == False:
                sub_districts.append(None)
                
        self.nodes["AREA"] = sub_districts
        self.nodes["AREA"] = self.nodes.apply(lambda x: self.fill_areas(x.name) if x["AREA"]==None else x["AREA"], axis=1)
        
        # Merge area information to start-node and end-node to each edge
        self.edges = self.edges.merge(self.nodes["AREA"], left_on="NODE_FROM", right_index=True, how="left")
        self.edges = self.edges.merge(self.nodes["AREA"], left_on="NODE_TO", right_index=True, how="left")

        # Rename area columns
        self.edges.rename(columns={"AREA_x":"AREA_FROM", "AREA_y":"AREA_TO"}, inplace=True)
        
        # Fill edges areas where None
        self.edges["AREA_TO"]   = np.where(self.edges["AREA_TO"].isnull(), self.edges["AREA_FROM"], self.edges["AREA_TO"])
        self.edges["AREA_FROM"] = np.where(self.edges["AREA_FROM"].isnull(), self.edges["AREA_TO"], self.edges["AREA_FROM"])
        
    def get_all_areas(self) -> np.array:
        """Get unique set of areas the street network is covering."""

        return np.unique(self.nodes["AREA"].dropna())

    def fill_areas(self, node: int) -> int:
        """
        Assigns an area to a node that has not been assigned yet. Thereby the connected 
        neighbor-nodes' areas are list, and the max count area is being assigned to the initially 
        unassigned area.

        Args:
            node (int): Key of the node to be assigned to an area.

        Returns:
            int: The assigned area, or None if an error occurs.
        """
        try:
            n_from = list(self.edges[self.edges["NODE_FROM"]==node]["NODE_TO"])
            n_to   = list(self.edges[self.edges["NODE_TO"]==node]["NODE_FROM"])
            n_connect = n_from + n_to

            n_areas = self.nodes[self.nodes.index.isin(n_connect)]["AREA"]
            n_areas = n_areas.dropna()

            return max(list(n_areas))

        except: return None
        
    def node_from_area(self, area: int) -> Optional[int]:
        """
        Randomly selectes a node within a specified area.
        
        Args:
            node (int): Key of the area to draw a node from.

        Returns:
            Optional[int]: The index of the randomly selected node, or None if there are no nodes
                in the specified area.
        """
        tmp = self.nodes[self.nodes["AREA"]==area]
        idx = np.random.randint(len(tmp))

        return tmp.index[idx]
