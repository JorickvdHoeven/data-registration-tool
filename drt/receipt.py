# AUTOGENERATED! DO NOT EDIT! File to edit: 05_receipt.ipynb (unless otherwise specified).

__all__ = ['sync_data_folder', 'sync_data_group', 'sync_receipt', 'write_receipt', 'parse_receipt']

# Cell
#export
from pathlib import Path
import drt.data_model as dm
import re
from typing import Union
from .environment import DataIntakeEnv
from dateutil import parser
from sqlalchemy import inspect
from typing import Union
from .utils import Data_Groups_Type

# Cell
def sync_data_folder(env: DataIntakeEnv, data_group_type: Data_Groups_Type):
    """
    TODO
    [summary]

    ##### Parameters
    env : DataIntakeEnv
        [description]

    data_group_type : Data_Groups_Type
        [description]

    ##### Raises
    TypeError
        [description]

    """
    if data_group_type == dm.Delivery:
        data_folder = env.delivery_folder
    elif data_group_type == dm.Raw_Data:
        data_folder = env.raw_data_folder
    elif data_group_type == dm.Dataset:
        data_folder = env.dataset_folder
    else:
        raise TypeError(data_group_type)

    for data_group in data_folder.iterdir():
        sync_data_group(env, data_group)

# Cell
def sync_data_group(env: DataIntakeEnv, data_group: Path):
    """
    TODO
    [summary]

    ##### Parameters
    env : [type]
        [description]

    data_group : Path
        [description]

    data_group_type : str
        [description]


    ##### Raises
    TypeError
        [description]

    """

    data_group_type = env.get_group_type_from_path(data_group)

    if data_group.is_dir() and (data_group / 'receipt.rst').exists():
        record = env.session.query(data_group_type).filter_by(name=data_group.name).first()
        if record:
            sync_receipt(env, (data_group / 'receipt.rst'), record)
        else:
            print(f'[!] record not found for {data_group.name}, can''t sync')

# Cell
def sync_receipt(env: DataIntakeEnv, receipt_path: Path, data_group: Data_Groups_Type):
    """
    TODO
    [summary]

    ##### Parameters
    env : DataIntakeEnv
        [description]

    receipt_path : Path
        [description]

    data_group : Union[dm.Dataset, dm.Delivery, dm.Raw_Data]
        [description]


    ##### Raises
    TypeError
        [description]

    """

    receipt_data = parse_receipt(env, receipt_path)

    for k, v in receipt_data.items():
        if k == 'description':
            data_group.description = v
        elif k == 'date_received':
            data_group.date_received = v
        elif k == 'delivery_source':
            data_group.delivery_source = v
        elif k == 'statistics_report':
            data_group.statistics_report = v
        elif k == 'dataset_report':
            data_group.dataset_report = v

    env.session.commit()

    # for each column compare text repr with data
    # cols have different masters:
    #  [[done]] Description, Source, Received date, are file master
    #  Tags are file master
    #  [[done]] System fields are db master
    #  links are outer join of file and db

    # update DB
    print(f"Writing receipt to {receipt_path.parent}")
    write_receipt(env, receipt_path.parent)

# Cell
def write_receipt(env: DataIntakeEnv, folder: Path):
    """
    Create a receipt for a data group based on information from the sqlite database.

    ##### Parameters
    env : DataIntakeEnv
        The data registration environment

    folder : Path
        Folder path to the Data Group to create a receipt for.

    group_type : str
        What type of data group is this data element.


    ##### Raises
    TypeError
        Raised if the data group type is not correct

    """

    dg = env.get_group_type_from_path(folder)

    # Get folder info from database
    folder_info = env.session.query(dg).filter_by(name=folder.name).first()

    # Write data to folder using data model serialization
    with open((folder / 'receipt.rst'), mode='wt') as f:
        try:
            f.write(folder_info.document())
        except Exception as e:
            print("Registering Failed")
            print(folder.name, folder_info, dg)
            raise e

# Cell
def parse_receipt(env: DataIntakeEnv, receipt_path: Path) -> dict:
    """
    TODO
    [summary]

    ##### Parameters
    receipt_path : Path
        [description]

    group_type : str
        [description]


    ##### Returns
    dict
        [description]

    ##### Raises
    TypeError
        [description]

    """
    text = receipt_path.read_text()

    group_type = env.get_group_type_from_path(receipt_path.parent)

    patterns = dict()
    data = dict()

    if group_type == dm.Delivery:
        # extract data with these regexes
        patterns['description'] = re.compile(r'Description:\n-+\n(.*?)\n+[^\n]+\n-+\n', re.MULTILINE | re.DOTALL)
        patterns['date_received'] = re.compile(r'\n:Date Received: (.+)$', re.MULTILINE)
        patterns['delivery_source'] = re.compile(r'\n:Received from: (.+)$', re.MULTILINE)
    elif group_type == dm.Raw_Data:
        # extract data with these regexes
        patterns['description'] = re.compile(r'Description:\n-+\n(.*?)\n+[^\n]+\n-+\n', re.MULTILINE | re.DOTALL)
        patterns['statistics_report'] = re.compile(r'Report\n-+\n(.*?)\n.*', re.MULTILINE | re.DOTALL)
        pass
    elif group_type == dm.Dataset:
        # extract data with these regexes
        patterns['description'] = re.compile(r'Description:\n-+\n(.*?)\n+[^\n]+\n-+\n', re.MULTILINE | re.DOTALL)
        patterns['dataset_report'] = re.compile(r'Report\n-+\n(.*?)\n.*', re.MULTILINE | re.DOTALL)
        pass
    else:
        raise TypeError

    for k, v in patterns.items():
        res = re.search(v, text)
        if res:
            data[k] = res.group(1)
            if data[k] == 'None':
                data[k] = None
            if 'date' in k and not data[k] is None:
                data[k] = parser.parse(data[k])

    return data