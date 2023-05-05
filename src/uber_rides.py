import os
import sys
from typing import Optional
from urllib.parse import urlencode

import numpy as np
import pandas as pd

import params.config as conf


class UberRides:
    """
    A class used to represent all information from uber rides in Vienna published
    by https://movement.uber.com/.
    """

    def __init__(self, filepath: str, areas_in_network: pd.DataFrame, **kwargs: Optional[dict]):
        """Comment this."""

        self.data = self.read_data(filepath=filepath, **kwargs)
        self.data = self.preprocess_date_columns(self.data)
        self.data.drop([
            "start_hour", 
            "end_hour", 
            "year", 
            "day", 
            "date"
        ], axis=1, inplace=True)

        self.data["sourceid"] = self.data["sourceid"].apply(lambda x: x.zfill(4))
        self.data["dstid"] = self.data["dstid"].apply(lambda x: x.zfill(4))

        self.data = self.drop_areas(
            df=self.data, 
            areas_in_network=areas_in_network
        )

    def read_data(self, filepath: str, **kwargs: Optional[dict]) -> pd.DataFrame:
        """
        Loads and transforms the raw input data.

        Args:
            filepath (str): Path to the raw data file.
            **kwargs (Optional[dict]): Additional arguments to be passed to the function.
                nrows (int, optional): Number of rows to be read.

        Returns:
            None, but updates self.data
        """
        self.check_downloaded(filepath)

        nrows = kwargs.get("nrows", None)        
        dtypes = {
            "sourceid": str,
            "dstid": str,
            "month": int,
            "mean_travel_time": float,
            "start_hour": str,
            "end_hour": str,
        }
        df = pd.read_csv(filepath, sep=",", usecols=np.arange(8), nrows=nrows, dtype=dtypes)
        return df
    
    def preprocess_date_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Comment this."""

        df["start_hour"] = df["start_hour"].str.zfill(2)
        df["end_hour"] = df["end_hour"].str.zfill(2)
        df["time_of_day"] = df["start_hour"] + "-" + df["end_hour"]
        df["year"] = 2020
        df["date"] = pd.to_datetime(df[["year", "month", "day"]])
        df["weekday"] = df["date"].dt.weekday
        df["weeknum"] = df["date"].dt.isocalendar().week
        df["weekend"] = np.where(df["weekday"] >= 5,1,0)

        return df
            
    def drop_areas(self, df: pd.DataFrame, areas_in_network: np.array) -> pd.DataFrame:
        """Removes rows where area of start of end are not within the street network."""
        
        areas_uber = self.get_all_areas(df)
        areas_unknown = [i for i in areas_uber if i not in areas_in_network]
                
        df = df[
            (-df["sourceid"].isin(areas_unknown)) &
            (-df["dstid"].isin(areas_unknown))
        ].reset_index(drop=True)

        return df

    def get_all_areas(self, df: pd.DataFrame) -> np.array:
        """Get unique set of areas this data set is covering."""

        return pd.concat([df["sourceid"], df["dstid"]]).unique()


    def check_downloaded(self, path: str) -> None:
        """
        Verifies if uber data has been downloaded and saved in certain path. If not, notify user 
        where to download data from.
        
        Args:
            path (str): Path where the data should be downloaded to.
        """
        if not os.path.exists(path):
            query_string = urlencode(conf.uber_url_params)
            url = f"{conf.uber_url_base}?{query_string}"

            print("Uber data cannot be found at {}.".format(path))
            print("Please download .csv file at {}.".format(url))
            sys.exit()
        else:
            pass
