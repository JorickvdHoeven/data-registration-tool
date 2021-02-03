# AUTOGENERATED! DO NOT EDIT! File to edit: 06_registration.ipynb (unless otherwise specified).

__all__ = ['extract_delivery_from_script', 'register_data_group', 'register_data_folder', 'register_all']

# Cell
"""
Module to contain all data registration code. If other methods need to be used
this module will call out to them such as utility functions to gather folder
metadata or document generation functions.
"""
from re import L
from drt.environment import DataIntakeEnv
import drt.utils as utils
import drt.receipt as rct
import itertools
import drt.data_model as dm
from pathlib import Path
from typing import Union
from drt.utils import Data_Groups_Type

def extract_delivery_from_script(env:DataIntakeEnv, folder:Path) -> str:
    """
    TODO:
    [summary]

    Parameters
    ----------
    env : DataIntakeEnv
        [description]

    folder : Path
        [description]


    Returns
    -------
    str
        [description]

    Example
    -------
    [>>> example_usage_of_module in pydoctest]
    """
    # load script data
    # get all registered delivery names
    # search for delivery names in script
    # return the delivery name which is the source
    # error if there is more than one source

    files = [fil for fil in folder.rglob("*")
             if fil.suffix[1:] in env.script_extension_list
                and fil.is_file()
    ]

    text = ''

    for fil in files:
        with open(fil, mode='rt') as f:
            text = text + f.read()

    sources = []
    for delivery in env.session.query(dm.Delivery).all():
        if delivery.name in text:
            sources.append(delivery)

    if len(sources) > 1:
        print(f"[!!] Error loading source for {folder}, too many sources" )
        return None
    elif len(sources) == 0:
        print(f"[!!] Error no registered source found for {folder}")
        return None
    else:
        return sources[0]

def register_data_group(env:DataIntakeEnv, folder:Path, group_type: Data_Groups_Type, record: Data_Groups_Type = None):
    """
    Register a single data group to the database.

    Parameters
    ----------
    env : DataIntakeEnv
        The application environment settings.

    folder : Path
        The full path to the folder of the data group to register. Relative paths won't work.

    group_type : str
        The group type to put it in the proper table.

    record : dm.Data_Group, optional
        If this is a pre-existing record and you have it provide it here, by default None

    Raises
    ------
    TypeError
        group_type must be one of ['delivery', 'raw_data', 'dataset']

    Example
    -------
    >>> register_data_group(env, Path(/users/data/01_delivery/2020_11_01_test_Data),'delivery')
    """
    dg = group_type
    if not record:
        record = env.session.query(dg).filter_by(name = folder.name).first()

    try:
        data = utils.process_data_group(folder, dg)
    except FileNotFoundError:
        print(f"[!] {folder} not processed, empty or non-existent")
        return False

    if group_type == dm.Raw_Data or type(record) == dm.Raw_Data:
        raw_data_source = extract_delivery_from_script(env, folder)

    # Set the system fields based on the metadata collected
    if record:
        # we have an existing record create it
        dg = record
        dg.type = data['type']
        dg.name = data['name']
        dg.last_update = data['last_update']
        dg.size = data['size']
        dg.num_files = data['num_files']
        dg.group_hash= data['group_hash']
        dg.group_last_modified= data['group_last_modified']
        if type(record) == dm.Raw_Data:
            dg.source = raw_data_source
    # we need to create a new record
    elif group_type == dm.Delivery:
        dg = dm.Delivery(**data)
        env.session.add(dg)
    elif group_type == dm.Raw_Data:
        dg =dm.Raw_Data(**data, source=raw_data_source)
        env.session.add(dg)
    elif group_type == dm.Dataset:
        dg = dm.Dataset(**data)
        env.session.add(dg)
    else:
        raise TypeError

    env.session.commit()

    return True

def register_data_folder(env:DataIntakeEnv, group_type: Data_Groups_Type, force:bool = False):
    """
    Scans a folder containing data groups and registers them if they
    don't already exist in the database.

    Parameters
    ----------
    env : DataIntakeEnv
        The environment with data intake process pathnames.

    group_type : str
        The type of folder to scan, delivery, raw_data, or dataset.

    force : bool, optional
        If we force we ignore the current data and regenerate all stats. This will
        overwrite previous stats.

    Raises
    ------
    ValueError
        The right type must be passed.

    Example
    -------
    >>> register_data_folder(env, 'delivery')
    """
    # get folder list, if not delivery folder then skip "In_Progress_*"
    if group_type == dm.Delivery:
        root_folder = env.delivery_folder
        folder_list = [fil
                       for fil in root_folder.iterdir()
                       if fil.is_dir() and not fil.name.startswith(".")]


    elif group_type == dm.Raw_Data:
        root_folder = env.raw_data_folder
        folder_list = [fil
                       for fil in root_folder.iterdir()
                       if not (fil.name.startswith(".") or fil.name.startswith("In_Progress"))
                       and fil.is_dir()]

    elif group_type == dm.Dataset: # group_type == 3
        root_folder = env.dataset_folder
        folder_list = [fil
                       for fil in root_folder.iterdir()
                       if not (fil.name.startswith(".") or fil.name.startswith("In_Progress"))
                       and fil.is_dir()]
    else:
        raise ValueError

    # Process new folders and add them to the database.
    data_group_list = env.get_data_group_list(group_type)
    known_folders = [ item.name for item in data_group_list ]
    new_folders = list(set([f.name for f in folder_list]) - set(known_folders))

    process_folders = list(zip(new_folders, itertools.repeat(None)))
    if force:
        process_folders.extend([(item.name, item) for item in data_group_list if (root_folder / item.name).is_dir()])

    for folder, record in process_folders:
        folder = root_folder / folder
        registered = register_data_group(env, folder, group_type, record)
        if force:
            rct.write_receipt(env, folder)
        elif registered:
            rct.sync_data_group(env, folder)
            rct.write_receipt(env, folder)

def register_all(env:DataIntakeEnv):
    """
    Register all new data groups in the data intake process environment.
    This on purpose, ignores In_Progress and . files.

    Parameters
    ----------
    env : DataIntakeEnv
        The data intake process environment to scan and register new data groups.

    Example
    -------
    >>> register_all(env)
    """
    [ register_data_folder(env, i, env.force_recalculate) for i in [dm.Delivery, dm.Raw_Data, dm.Dataset] ]
