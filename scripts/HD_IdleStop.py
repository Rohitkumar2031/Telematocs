#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="NorthCorp")
import datetime
import matplotlib.pyplot as plt
import os

base_dir = r"/home/parth/Machine Learning/Datasets/North Corp/Ajanta"
files = os.listdir(base_dir)
files_corrected = []
data = []
first_one = True
for file in files :
    if file.endswith(".csv") :
        files_corrected.append(file)
        dat = pd.read_csv(os.path.join( "/home/parth/Machine Learning/Datasets/North Corp/Ajanta" , file))
        if first_one :
            columns = dat.columns
        else :
            assert  np.all(columns == dat.columns)
        first_one = False
        data.append(dat)
        
files = files_corrected
del files_corrected

for i in range(len(data)) :
    data[i] = data[i].sort_values("updateddate" , ascending=True)

for i in range(len(data)) :
    data[i]["dateSeconds"] = data[i]["updateddate"].apply(
        lambda x: datetime.datetime.strptime(x , "%Y-%m-%d %H:%M:%S")).apply(
        lambda x: (x - datetime.datetime(1970,1,1)).total_seconds() )

for i in range(len(data)) :
    previdletime = data[i].iloc[0]["time_idle"]
    data[i]["idleWastedFuel"] = None
    data[i]["idleTimeDelta"] = None
    for row in range(1 , len(data[i])):
        currentidletime = data[i].iloc[row]["time_idle"]
        currentFuel = data[i].iloc[row]["total_fuel_consumption"]
        if (currentidletime != previdletime):
            if row != 0 :
                data[i].at[row , "idleWastedFuel"] = abs ((currentFuel - prevFuel))
                data[i].at[row  , "idleTimeDelta"] = abs(currentidletime - previdletime)
            else :
                data[i].at[row , "idleWastedFuel"] = 0
        else:
            data[i].at[row , "idleWastedFuel"] = 0
        previdletime = currentidletime
        prevFuel = currentFuel
    data[i].at[0 , "idleWastedFuel"] = 0
    data[i].at[0 , "idleTimeDelta"] = 0

IdleCases = []

for i in range(len(data)) :
    IdleCases.append(data[i][data[i].speed == 0])
    IdleCases[i] = IdleCases[i][IdleCases[i]["idleWastedFuel"] != 0]

StopCases = []

for i in range(len(data)) :
    StopCases.append(data[i][data[i].speed == 0])
    StopCases[i] = StopCases[i][StopCases[i]["idleWastedFuel"] == 0 ]
    StopCases[i]["stopTimeDelta"] = 0
    StopCases[i].drop(columns=["idleWastedFuel" , "idleTimeDelta"] , inplace=True)
    StopCases[i].stopTimeDelta = StopCases[i].dateSeconds.diff()
    StopCases[i].at[0 , "stopTimeDelta"] = 0
    StopCases[i]["stopTimeDelta"] = StopCases[i]["stopTimeDelta"] / 3600.0

for i in range(len(data)) :
    print("Total Fuel Wasted CASE:{} : {} ".format(i , sum(IdleCases[i]["idleWastedFuel"] )))

for i in range(len(data)) :
    IdleCases[i].to_csv("IdleCases-{}.csv".format(files[i]))
    StopCases[i].to_csv("StopCases-{}.csv".format(files[i]))
    data[i].to_csv("Full-Data-{}.csv".format(files[i]))

