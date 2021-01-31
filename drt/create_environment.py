# AUTOGENERATED! DO NOT EDIT! File to edit: 02_create_environment.ipynb (unless otherwise specified).

__all__ = ['create_data_model', 'create_folders', 'create_config', 'create_environment']

# Cell
'''
    Code to create a new environment with an associated config file.
'''

import sqlalchemy as db
from pathlib import Path
import shutil
import configparser
import drt.data_model as dm


def create_data_model( file_name:str = None, location:Path = None):
    """
    Creates an SQLite database with the appropriate tables for use in
    managing the data intake process.

    This will not destroy a pre-existing database file.

    Parameters
    ----------
    file_name : str, optional
        Name of the database file defaults to 'intake_db'

    location : Path, optional
        Location where to save the db file, by default current working directory

    Example
    -------
    >>> from pathlib import Path
    >>> create_data_model('testing', Path('/var/tmp/'))
    """
    if location is None:
        location = Path.cwd()

    if file_name is None or file_name == '':
        file_name = 'intake_db'

    (location / '.config').mkdir(parents=True, exist_ok=True)
    db_path = location / '.config' / f'{file_name}.sqlite'
    engine = db.create_engine(f'sqlite:///{db_path}', pool_pre_ping=True)

    if Path.exists(db_path):
        # db already exists return connection
        # TODO test that the sqlite database has the right schema if not, raise error
        with engine.connect() as conn:
            session = db.orm.Session(bind=conn)
            session.query(dm.Data_Group).all()

        return db_path

    dm.Base.metadata.create_all(engine)

    return db_path

# %%

def create_folders(location:Path=None):
    """
    Create the folder structure to accept data. Also populate a
    helpful readme with instructions on how to use the data intake
    process.

    Parameters
    ----------
    location : Path, optional
        The location where to create the folder structure, by default current working directory

    Example
    -------
    >>> create_folders(Path('/var/tmp'))
    """
    if location is None:
        location = Path.cwd()
    elif not location.exists():
        location.mkdir(parents=True)

    delivery = '01_Delivery'
    raw = '02_RAW'
    dataset = '03_Datasets'

    (location / delivery).mkdir(exist_ok=True)
    (location / raw).mkdir(exist_ok=True)
    (location / dataset).mkdir(exist_ok=True)

    parent = Path(__file__).resolve().parent
    shutil.copy(str(parent / 'templates' / 'data_intake_readme.md'), str(location / 'readme.md'))

    return {
        'delivery': (location / delivery),
        'raw': (location / raw),
        'datasets': (location / dataset),
    }

# %%

def create_config(location:Path, db_path:Path, folders:dict) -> Path:
    """
    Create a new default configuration file with the paths set to the
    default paths.

    Parameters
    ----------
    location : Path
        Location of data intake project

    db_path : Path
        Location of the data intake database

    folders : dict
        Dictionary with the folder paths for 'delivery', 'raw', and 'datasets'

    Example
    -------
    >>> create_config(Path('/var/tmp/'))
    """
    if location is None:
        location = Path.cwd()

    cfg = configparser.ConfigParser()
    d = dict()
    d['root_data'] = location
    d['delivery_folder'] = folders['delivery']
    d['raw_data_folder'] = folders['raw']
    d['datasets_folder'] = folders['datasets']
    d['data_intake_db'] = db_path


    cfg['PATHS'] = d

    d = dict()
    d['force_recalculate'] = False
    cfg['FLAGS'] = d

    d = dict()
    d['data_extensions'] = '\n'.join(["data", "parquet", "hdf5"])
    d['report_extensions'] = '\n'.join(['report','md','html','pptx','docx'])
    d['script_extensions'] = '\n'.join(['script', 'ipynb', 'py', 'r', 'jl', 'sh'])
    cfg['EXTENSIONS'] = d

    if not (location / '.config' / 'config.ini').is_file():
        with open((location / '.config' / 'config.ini'), mode='w') as f:
            cfg.write(f)
    else:
        print('[!] config.ini already exists, using existing version')

    return (location / '.config' / 'config.ini')


# %%

def create_environment(location:Path = None) -> Path:
    """
    Stands up a data intake environment at the given location.

    Parameters
    ----------
    location : Path, optional
        Location to create the environment, defaults to current working directory.


    Example
    -------
    >>> create_environment(Path('/var/tmp'))
    """

    if location is None:
        location = Path.cwd()

    (location / '.config').mkdir(parents=True, exist_ok=True)

    db_path = create_data_model(location=location)
    folders = create_folders(location=location)

    return create_config(location, db_path, folders)

