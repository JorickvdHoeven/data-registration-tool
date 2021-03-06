# AUTOGENERATED! DO NOT EDIT! File to edit: 04_environment.ipynb (unless otherwise specified).

__all__ = ['DataIntakeEnv']

# Cell
#export

import configparser
from pathlib import Path
import pandas as pd
import sqlalchemy as db
import sys
from sqlalchemy.orm import sessionmaker
import drt.data_model as dm
from .utils import Data_Groups_Type

# Cell
class DataIntakeEnv():
    """
    TODO
    [summary]
    """
    def __init__(self, config_file:str):
        config = self.load_config(config_file)

        self.database_file = config['data_intake_db']

        if not Path(self.database_file).is_file():
            raise ValueError('Database file in config needs to be a file.')

        self.engine = db.create_engine(f'sqlite:///{self.database_file}', echo=False, pool_pre_ping=True)

        self.Sessions = sessionmaker(self.engine)
        self.session = self.Sessions()

        self.delivery_folder = Path(config['delivery_folder'])

        self.raw_data_folder = Path(config['raw_data_folder'])

        self.dataset_folder = Path(config['datasets_folder'])

        self.force_recalculate = config.get('force_recalculate',False)

        self.force_rebuild = False

        # Data
        self.data_extension_list = config['data_extensions']

        # Reports
        self.report_extension_list = config['report_extensions']

        # Scripts
        self.script_extension_list = config['script_extensions']

    @classmethod
    def load_config(cls, config_file: str) -> dict:
        """
        Load the configuration file provided and return a dict with it's
        elements converted. This method relies on the config file to have
        two sections:
        - PATHS: contains all the file system paths which are converted
                    to pathlib.Path object for later use
        - FLAGS: contains all the boolean variables which are converted
                    to boolean True if they have "True" in them, false
                    otherwise
        If this function is unable to load the config file it will raise
        a FileExistsError

        ##### Parameters
        config_file : str
            The path to the configuration file


        ##### Returns
        Dict
            A dictionary containing the PATHS and FLAGS sections of the config
            file.
        """
        cfg = configparser.ConfigParser()
        d = dict()

        try:
            cfg.read(config_file)
            # Convert paths to dict
            for k,v in cfg.items(section='PATHS'):
                d[k]=Path(v)

            # Convert flags to bool
            # ! This converts flags to false if it's not exactly "True"
            for k,v in cfg.items(section='FLAGS'):
                d[k]= v=="True"

            # Convert extensions to lists
            # ! This converts flags to false if it's not exactly "True"
            for k,v in cfg.items(section='EXTENSIONS'):
                d[k]= v.split('\n')

        except Exception as e:
            print(e)
            print("Unable to load configuration, please recreate config file.")
            raise FileExistsError



        return d

    def get_data_group_list(self, data_group: Data_Groups_Type ) -> list:
        """
        Returns a DataFrame containing the data for a whole data group list.
        !!! Potential to remove this, it seems like a useless abstraction.

        ##### Parameters
        list_name : str
            This is the name of the list to retrieve this can be either:
            - delivery
            - raw_data
            - dataset

        ##### Returns
        list
            A list of dm.Data_Group descendant objects

        """

        return self.session.query(data_group).all()

    def upsert_data_group(self, folder, data, type) -> dict:
        # Insert or update data into the database if non-mandatory
        # columns are missing don't overwrite existing data with null.

        # check dictionary keys and split into two dicts, one for base
        # one for spcific.

        # lookup specific ID in table to get ID related to folder name

        # if ID exists, run update for base and specific data dicts

        # if ID doesn't exist insert base and specific dicts

        # return result of get_data_group

        # Return with full data.
        raise NotImplementedError

    def get_group_type_from_path(self, path: Path):
        folder_name = path.name
        data_group_folder = path.parent

        if self.delivery_folder == data_group_folder:
            return dm.Delivery
        elif self.raw_data_folder == data_group_folder:
            return dm.Raw_Data
        elif self.dataset_folder == data_group_folder:
            return dm.Dataset
        else:
            raise ValueError("Unable to determine type from path", path, data_group_folder)
