#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import json
from pandas.io.json import json_normalize
from functools import partial


# In[2]:


def loader(mainDataDir , pcodeDataFile , deviceMappingDataFile):
    # Read Main Data
    import os
    file_list = os.listdir(mainDataDir)
    data_list = []
    for file in file_list:
        if not file.endswith(".csv"):
            continue
        data_list.append(pd.read_csv( os.path.join(mainDataDir , file) ) )
    
    ## Read and Load the pcode data
    pcode_data = pd.read_csv(pcodeDataFile)
    
    # Read and Load device Mapping Data
    deviceMapping = pd.read_csv(deviceMappingDataFile )
    
    return data_list , pcode_data , deviceMapping


# In[3]:


def functionWrapper(loaderFunc=loader):
    data_list , pcode_data  , deviceMapping = loaderFunc()
    first = True
    for i , df in enumerate(data_list):
        if first:
            first = False
            real_columns = df.columns
        try :
            assert (df.columns == real_columns).all()
        except Exception:
            print("Problem")
        else:
            print("No Problem Found")

    device_data = []
    for df in data_list:
        if not (df["type"] == 'DTCA').any():
            continue
        df = df[df["type"] == 'DTCA'].reset_index().drop(columns='index' , inplace=False)
        temp_list = df.data.astype(str).to_list()
        jsonDict = [json.loads(tem) for tem in temp_list ]
        device_data.append(json_normalize(jsonDict, 'dtcasub' , ['id', 'date', 'type', 'deviceID', 'sequenceNo', 'latitude', 'longitude',
                   'utc', 'numberOfFaultCodes']) )

    pcode_data = pcode_data[["SPN \n( Bosch Proposal )"  , "FMI\n( Bosch Proposal )"]]
    pcode_data = pcode_data.rename(
        columns = {
            "SPN \n( Bosch Proposal )":'spn' ,
            "FMI\n( Bosch Proposal )":'fmi'
        }
    )

    for i , dat in enumerate(device_data):
        device_data[i] = dat.merge(pcode_data , on=['spn' , 'fmi'])

    complete_data = pd.concat(device_data)

    x1 = deviceMapping[["Device IMEI" , "Vehicle VIN No"]].to_dict()
    x2 = deviceMapping[["Device IMEI" , "Customer"]].to_dict()
    x3 = deviceMapping[["Device IMEI" , "Fleet"]].to_dict()
    x4 = deviceMapping[["Device IMEI" , "Vehicle No Plate"]].to_dict()
    device2chassis = {a:b for a,b in zip(x1["Device IMEI"].values() , x1["Vehicle VIN No"].values())}
    device2customer = {a:b for a,b in zip(x2["Device IMEI"].values() , x2["Customer"].values())}
    device2fleet = {a:b for a,b in zip(x3["Device IMEI"].values() , x3["Fleet"].values())}
    device2plate = {a:b for a,b in zip(x4["Device IMEI"].values() , x4["Vehicle No Plate"].values())}
    def appFunc(deviceDict , x):
        try:
            fin = deviceDict[x]
        except IndexError:
            fin = None
        return fin

    complete_data["Vehicle VIN No"] = None
    complete_data["Vehicle VIN No"] = complete_data.deviceID.apply(
        lambda x : appFunc(device2chassis , int(x) )
    )
    complete_data["Customer"] = None
    complete_data["Customer"] = complete_data.deviceID.apply(
        lambda x : appFunc(device2customer , int(x))
    )
    complete_data["Fleet"] = None
    complete_data["Fleet"] = complete_data.deviceID.apply(
        lambda x : appFunc(device2fleet , int(x))
    )
    complete_data["Vehicle No Plate"] = None
    complete_data["Vehicle No Plate"] = complete_data.deviceID.apply(
        lambda x : appFunc(device2plate , int(x))
    )
    return complete_data


# In[ ]:



loadingFunc = partial(
    loader,
    mainDataDir = "/home/parth/Machine Learning/Datasets/North Corp/DTC/May/Raw",
    pcodeDataFile = "/home/parth/Machine Learning/Datasets/North Corp/DTC/SPN_PCODE_Master.csv",
    deviceMappingDataFile = "/home/parth/Machine Learning/Datasets/North Corp/DTC/Eicherlive -Device-Vehicle Mapping.csv"
)

completeDataProcessed = functionWrapper(loadingFunc)

dataDevice = { id_:completeDataProcessed[completeDataProcessed.deviceID == id_]                for id_ in completeDataProcessed.deviceID.unique()}

for id_ , data in dataDevice.items():
    saves = data.to_csv("Device{}.csv".format(id_))

#complete_data.to_csv("complete_aug.csv")


# In[ ]:




