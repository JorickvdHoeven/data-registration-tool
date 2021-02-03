# AUTOGENERATED! DO NOT EDIT! File to edit: 99_utils.ipynb (unless otherwise specified).

__all__ = ['hash_files', 'process_data_group', 'count_data_group_components', 'Data_Groups_Type']

# Cell
"""
Utility functions used across the application. These methods should not
rely on the overall environment. This means that they should in principle
focus on implementing functionality with non-application specific code.

If when creating methods here you are tapping into the data model or the
environment modules ask yourself if the functionality can be refactored to
be more general.
"""
from pathlib import Path
from typing import List
import hashlib
from tqdm import tqdm
from datetime import datetime
import pandas as pd
import numpy as np

import drt.data_model as dm
import typing

Data_Groups_Type = typing.Union[dm.Delivery, dm.Raw_Data, dm.Dataset]


def hash_files(file_list: List[str],
               block_size: int = 10_485_760,
               progressbar_min_size: int = 10_737_400_000) -> str:
    """
    Takes a list of path objects and returns the SHA256 hash of
    the files in the list. If any of the objects are not file objects,
    this will crash. Ignores any files called 'receipt.rst' as those are
    considered data intake files and not part of the work.

    Parameters
    ----------
    file_list : List[str]
        List of strings denoting files to be hashed, the strings
        must all be valid files or this method will throw a
        ValueError exception.

    block_size : int, optional
        Block size in bytes to read from disk a good generic
        value is 10MB as most files are smaller than 10MB and
        it means we can load whole files in at a time when
        hashing, defaults to 10_485_760 (10MB).

    progressbar_min_size : int, optional
        Minimum size a file needs to be to get its
        own progress bar during processing. Default was chosen
        to work well on an SSD reading 400 MB/s, defaults
        to 10_737_400_000 (10GB).

    Returns
    -------
    str
        A string representation of the SHA256 hash of the files
        provided in the file list.

    Raises
    ------
    ValueError
        The strings passed in the file_list need to be valid file objects
        in the file system. Currently only windows and Posix filesystems
        are supported. This may change in future.

    Example
    -------
    >>> files = sorted([f for f in Path.cwd().iterdir() if not f.is_dir()])
    >>> hash_files(files)
    'ceafa67639bab8e30b0b73955668edec73c1ff2b190db60d74da419144e6c0b0'

    """

    # sort the file list to always give a consistent result. Order matters.
    file_list = sorted(file_list)

    file_list_hash = hashlib.sha256()  # Create the hash object for the list

    # loop through all the files in the list updating the hash object
    for fil in tqdm(file_list, leave=False, unit="files"):
        file_progress_bar = False

        if not Path(fil).exists():
            raise FileNotFoundError("Strings in the file_list must be a valid path in the filesystem")
        elif Path(fil).is_dir():
            raise ValueError("Strings in the file_list must be a valid files not folders")

        size = fil.stat().st_size
        if size > progressbar_min_size:
            file_progress_bar = True
            pbar = tqdm(total=fil.stat().st_size, unit="bytes", unit_scale=True, leave=False)
        else:
            pbar = [] # else only here to get rid of unbound warning

        # Read data from file in block_size chunks and update the folder hash function
        with open(fil, "rb") as f:
            fb = f.read(block_size)
            while len(fb) > 0:
                file_list_hash.update(fb)  # Update the file list hash
                fb = f.read(block_size)  # Read the next block from the file
                if file_progress_bar:
                    pbar.update(block_size)
        if file_progress_bar:
            pbar.close()
    return file_list_hash.hexdigest()

def process_data_group(folder:Path, type:str, light:bool = False) -> dict:
    """
    Return the system fields for a data group folder.

    If the data group is a delivery type, then this only looks at the
    data folder in it, if it is any other type it looks at the whole folder.

    Parameters
    ----------
    folder : Path
        The location to get metadata for.

    type : DataIntakeEnv
        The type of data group. ['delivery', 'raw_data', 'dataset']

    light : bool, optional
        If set skip the hashing

    Returns
    -------
    dict
        A dict of the following five metadata elements calculated:
        - name : Name of the folder of the data group
        - type : The type of the data group processed
        - last_update : The current date and time
        - size : The size of the data on disk
        - num_files : The number of data files.
        - group_hash : A SHA256 hash of all the data in the folder
        - group_last_modified : The maximum date of created, and modified for all files

    Example
    -------
    >>> process_data_group(delivery, dm.Delivery)
    {
        "name" : '2020_11_01_test_delivery',
        "type" : 'delivery',
        "last_update" : datetime.datetime(2020, 11, 15, 3, 51, 33, 851325),
        "size" : 5465684,
        "num_files" : 4,
        "group_hash" : 'ceafa67639bab8e30b0b73955668edec73c1ff2b190db60d74da419144e6c0b0',
        "group_last_modified" : datetime.datetime(2020, 11, 15, 3, 31, 36),
    }
    """

    if type == dm.Delivery:
        data_folder = folder / 'data'
    else:
        data_folder = folder

    # check for non-existent or empty folder
    if not data_folder.exists():
        raise FileNotFoundError
    try:
        next((data_folder).glob("**/*"))
    except StopIteration:
        # folder is empty can't process it
        raise FileNotFoundError

    # Get file sizes, last modified dates, and names to count,
    # sum size, and hash the file data provided
    file_sizes, file_modified_dates, file_metamodified_dates, file_names = zip(
        *[
            (f.stat().st_size, f.stat().st_mtime, f.stat().st_ctime, f)
            for f in (data_folder).glob("**/*")
            if f.is_file() and f.name != 'receipt.rst'
        ]
    )

    last_modified = datetime.fromtimestamp(
                    max(max(file_modified_dates),
                        max(file_metamodified_dates)))

    # Hash the files in the delivery
    if light:
        folder_hash = 'skipped'
    else:
        folder_hash = hash_files(file_names)

    dg = {
     'name' : folder.name,
     'type' : type.__name__,
     'last_update' : datetime.now(),
     'size' : sum(file_sizes),
     'num_files' : len(file_sizes),
     'group_hash' : folder_hash,
     'group_last_modified' : last_modified,
    }

    return dg

def count_data_group_components( data_group: Path,
                    data_extensions: list,
                    report_extensions: list,
                    script_extensions: list,
                    ):
    """
    A utility method to analyze a folder to determine which data
    it contains and whether those have the three requisite elements,
    generation script, data, and report. It relies on certain
    conventions about the folder which must be followed:

    1. Each data respresentation is stored in a folder, files in
        the root of the passed folder will be ignored.
    2. Folders starting with "In_Progress" or "." will be ignored.
    3. In each data representation folder there are three entries
        more won't cause an error but should be avoided
    4. Report types have extensions:
            ['report','md','html','pptx','docx', ...]
        with the initial report extension added to a folder containing
        report files if there is more than 1 report file needed.
    5. Data types have extensions:
            ['data','parquet','hdf5', ...]
        with the initial data extension being used for folders in the
        declaration which allows the data to be spread over multiple
        files.
    6. Script types have extensions:
            ['script','ipynb','py','r','jl','sh', ...]
        Where the first extension can be applied to a folder if more
        than one file was needed to process the data.

    This analyzer will look only for the extensions listed and report
    how many of each of the types of files/folders exist in the root
    of the provided folder.

    Parameters
    ----------
    folder : Path
        A folder containing folders of data representations

    TODO add extension list parameters

    Returns
    -------
    pd.DataFrame
        A table listing all the data representations which appear
        in the root of the folder.

    Example
    -------
    >>> analyze_folder(folder)
    {
        'data'   : 1,
        'report' : 0,
        'script' : 1
    }
    """

    element_count ={
        'data':0,
        'report':0,
        'script':0
    }

    # For each Raw data file extract count the number of each data elements it has
    for fil in data_group.iterdir():
        if not fil.name.startswith('.'):
            if fil.suffix in data_extensions:
                element_count['data'] += 1
            if fil.suffix in report_extensions:
                element_count['report'] += 1
            if fil.suffix in script_extensions:
                element_count['script'] += 1

    return element_count