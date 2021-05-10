# Libraries for data processing
import numpy as np
import pandas as pd
import datetime as dt

class Uber(object):
    """
    A class used to represent all information from uber rides in Vienna published
    by https://movement.uber.com/.
    
    Attributes
    ----------
    data : pd.DataFrame
    unknown : list

    Methods
    -------
    load_rides(filename, nrows):
        A function that loads and transforms the raw input data
    unknown_areas(nodes):
        A function that identifies areas that are not present in the official street network
        of the City of Vienna.
    drop_areas():
        A function that removes rows where area of start of end are not within the street network
    """

    # Load dataframe
    def load_rides(self, filename, **kwargs):
        """
        A function that loads and transforms the raw input data.
        
        Parameters
        ----------
        filename : str
        nrows : int (optional)
        """
        
        # Load data
        if "nrows" in kwargs:
            self.data = pd.read_csv("input/"+filename, sep=",", usecols=np.arange(8), nrows=kwargs["nrows"])
        else:
            self.data = pd.read_csv("input/"+filename, sep=",", usecols=np.arange(8), nrows=5)

        # Dict for data types
        dtypes = {
            "start_hour":str,
            "end_hour":str,
            "sourceid":str,
            "dstid":str}

        self.data = self.data.astype(dtypes)

        # Combine start_hour & end_hour to 1 feature
        self.data["time_of_day"] = self.data["start_hour"]+"-"+self.data["end_hour"]

        # Get date
        self.data["year"] = 2020
        self.data["date"] = pd.to_datetime(self.data[["year", "month", "day"]])

        # Get week features
        self.data["weekday"] = self.data["date"].dt.weekday
        self.data["weeknum"] = self.data["date"].dt.isocalendar().week
        self.data["weekend"] = np.where(self.data["weekday"]>=5,1,0)

        # Drop redundant features
        self.data.drop(["start_hour","end_hour","year","day","date"], axis=1, inplace=True)

        # Align data type of area_id
        self.data["sourceid"] = self.data["sourceid"].apply(lambda x: x.zfill(4))
        self.data["dstid"] = self.data["dstid"].apply(lambda x: x.zfill(4))

        # Export data as csv
        if "export" in kwargs:
            if kwargs["export"] == True:
                self.data.to_csv("uber.csv", sep=",", index=False)
            else:
                pass
            
            
    def unknown_areas(self, nodes):
        """
        A function that identifies areas that are not present in the official street network
        of the City of Vienna.
        
        Parameters
        ----------
        nodes : pd.DataFrame
        """
        
        areas_streets = nodes["AREA"].unique()
        areas_uber    = self.data["sourceid"].append(self.data["dstid"])
        areas_uber    = np.unique(areas_uber)

        self.unknown = [i for i in areas_uber if i not in areas_streets]
        return self.unknown
    
    
    def drop_areas(self):
        """A function that removes rows where area of start of end are not within the street network"""
        
        self.data = self.data[-self.data["sourceid"].isin(self.unknown)]
        self.data = self.data[-self.data["dstid"].isin(self.unknown)]
        self.data.reset_index(drop=True, inplace=True)