# Data Registration tool
> This is a small tool that can be used to register data received from business users who have requested analyses. The purpose behind this project is to create a light-weight system that allows analysts to quickly and flexibly document the origin of small (less than 50GB) data sets. 


## Install

`git clone https://github.com/JorickvdHoeven/data-registration-tool.git`  
`pip install data-registration-tool`

## How to use

The application is a CLI which can be used directly from the command line once installed.  

```
!drt --help
```

    Usage: drt [OPTIONS] COMMAND [ARGS]...
    
    Options:
      --install-completion [bash|zsh|fish|powershell|pwsh]
                                      Install completion for the specified shell.
      --show-completion [bash|zsh|fish|powershell|pwsh]
                                      Show completion for the specified shell, to
                                      copy it or customize the installation.
    
      --help                          Show this message and exit.
    
    Commands:
      create    create a new data registration area
      document  Build documentation based on information in db and provided by...
      register  register any new data elements, run with --force to regeister...
      verify    verify the data registration environment to determine if there...



The structure of the data registration process is based on the following three concepts:

1. Delivery
2. Extracted Data
3. Transformed Data

Essentially it's a take on the traditional __ETL__ process which adds in an extra step call `Receive`. The reason for the additional step is that while in pure IT environments receipt of data is generally a contract managed between two systems and is rolled into the `E: Extract` part of the __ETL__ process. In Data Analytics receipt of data is only sometimes between systems. Often it is between people. We therefore need to create a log of the data receipt somewhere and only after the data is logged can we proceed to extract information from the folder dump or excel extravaganzza we've been delivered. To account for this and to account for the fact that we're working in a team environment we set the process in the following way:

0. L: `Load`
1. R: `Receive`   == 01_Delivery
2. E: `Extract`   == 02_RAW
3. T: `Transform` == 03_Datasets

You'll notice in the process above that the folder structure only accounts for steps 1-3 and doesn't account for step 0. This is normal, step 0 is just putting data into the registration system. We're trying to make it super easy by just using a file system for that. 

In the sections below we'll go over what each of steps 1-3 are about and what the requirements are for the Data Analyst.

__tldr;__  
Everything you get goes in `Delivery`, if it's got valuable data extract it to `Raw`, if you want to use extracted data transform it to a `Dataset` from several raw data elements and/or Datasets. Filtering happens during the Dataset creation (`Raw` -> `Dataset`), data conversion happens during extraction (`Delivery` -> `Raw`).

<br /><br />

01_Delivery
-----------
The delivery folder is the repository of the data delivered for the project. This can be in various different forms. It may be excel sheets provided by business experts, extracts from systems, files requested for analysis, etc. 

A Delivery is data or a group of data delivered at a particular point in time. The data can be preprocessed by the source or can be in a format which needs a more manual extraction. A delivery can also contain 1 or more different types of data to extract. This is because when someone provides us with a data dump it's not always immediately obvious whether we have multiple data elements in the dump. 

The structure of a delivery is as follows:
```

01_Delivery
  |
  + 2020_01_19_Delivery_title
  |   |
  |   + data
  |   |  |
  |   |  + Delivered data file/folder
  |   |
  |   + source
  |   |   |
  |   |   + Description of where data comes from
  |   |   
  |   + receipt.rst
  _

```
The data provided is put into the data folder, the data can be a single file or it can be a folder containing files. 

The source folder contains records of how the data was provided/coillected. This could be an email, a report transcript, or any other way of demonstrating where this data comes from.

The `receipt.rst` file is generated by the `drt` tool and contains metadata about the delivered data as well as information about who provided the data as well as what this data is. The source information and the description of the data must be filled in by the analyst on data receipt.

<br /><br />

02_RAW
------
When data flows from Delivery to Raw that means that the Data Analyst has found value in extracting the information from the delivery. A key thing to note is that a Raw data element can only ever have 1 source but a Delivery can have many Raw data elements extracted from it. The Raw data should be converted to a type-specific data storage format but the data should not be filtered or joined with other data. Another part of the Raw data extraction that is important is that during the extraction process the Data Analyst needs to produce a report which future users of the data can use to quickly determine what type of data is contained in the Raw data element. A Raw data element has the following structure:

```
02_RAW
  |
  + 2020_01_19_Raw_Data_Title
  |   |
  |   + extracted_data {folder OR file with data extension}
  |   |  |
  |   |  + Extracted data file/folder
  |   |
  |   + report {folder OR file with report extension}
  |   |   |
  |   |   + Description of the data including statistics
  |   |
  |   + script {folder OR file with script extension}
  |   |   |
  |   |   + Code used to extract the data
  |   |   
  |   + receipt.rst
  _
```

__extracted_data:__  
This is either data file (parquet, csv, etc) or data stored in a folder with the ".data" extension. In principle this data should be typed so that its clear for future users what the data is. 

__report:__  
This is either a report file (html, docx, pptx, etc) or a series of report files stored in a folder with the ".report" extension. This report should provide statistics about the data in the extracted data. Allowing future users of the data to better understand the extracted data.

__script:__  
This is either a script file (py, ipynb, r, jl, etc) or a folder with the ".script" extension which extracts information from the delivery data.

__receipt.rst:__  
This is a receipt file generated by the drt tool and which a Data Analyst should populate with a description. The information in this file will form the basis of the data documentation.

<br /><br />

03_Datasets
-----------
The Dataset element is the final element in the data registration process. This can be formed from one or multiple raw data elements or other datasets. The Dataset is filtered and combined data which can be used for analysis. Thought needs to go into how a Dataset is created and the source of its data is very important. Datasets form the basis of analyses.


```
03_Datasets
  |
  + 2020_01_19_Raw_Data_Title
  |   |
  |   + dataset {folder OR file with data extension}
  |   |  |
  |   |  + Compiled data file/folder
  |   |
  |   + report {folder OR file with report extension}
  |   |   |
  |   |   + Dataset report
  |   |
  |   + script {folder OR file with script extension}
  |   |   |
  |   |   + Code used to create the Dataset
  |   |   
  |   + receipt.rst
  _
```

__dataset:__  
This is the Dataset in a typed file type (parquet, etc) or a folder with data in it with the extension ".data"

__report:__  
The Dataset Report in html, docx, pptx or a folder with the ".report" extension containing the report. This report differs from the Raw data in that in addition to showing statistics of the data it should also maintain Dataset FactSheet which contains important information about the source of the data and the purpose why the dataset was created.

__script:__  
The script to create the Dataset in a script file or in a folder with the ".script" extension.  

__receipt.rst:__  
A file create by the drt tool which will be used to population information about this dataset in the data documentation generated by drt.
