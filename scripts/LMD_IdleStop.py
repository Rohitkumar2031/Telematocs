#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
#from geopy.geocoders import Nominatim
import datetime
import matplotlib.pyplot as plt
import os
import argparse
import warnings

warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser()

parser.add_argument(
    "--base-dir" , type=str , default="."
)
parser.add_argument(
    "--file"  , default="rawfeed_april_0_CAN.csv"
)
parser.add_argument(
    "--save" , type=bool , default=False
)
parser.add_argument(
    "--plot" , type=str , default=None
)

args = parser.parse_args()

def process(intervals):
        intervals = intervals.T
        intervals["Interval ID"] = intervals[0]
        intervals["Date"] = intervals[1]
        intervals["Interval Length"] = intervals[2]
        intervals["Latitude"] = intervals[3]
        intervals["Longitude"] = intervals[4]
        intervals.drop(columns=[0 , 1 , 2 , 3 , 4] , inplace=True)
        return intervals

def plotter(mi  , ma , intervals , str_):
    plt.rcParams.update({'font.size': 22})
    plt.style.use('ggplot')
    x = intervals["Date"].values[mi:ma]
    y = intervals["Interval Length"].values[mi:ma]
    y = y.reshape(-1 , 1)
    x = x.reshape(-1 , 1)
    plt.figure(figsize=(25 , 20))
    plt.xlabel("Date")
    plt.ylabel("{} Time".format(str_))
    plt.title("{} Time vs Date".format(str_))
    plt.hist( x=x  , weights=y , bins=ma-mi)
    plt.show()

def saveFiles(base , data_sort , dataRunning , dataRunningId , IdleCases , IdleIntervals , StopCases , StoppageIntervals):
    data_sort.to_csv(os.path.join(base , "DataSorted.csv") )
    dataRunning.to_csv(os.path.join(base , "dataRunning.csv"))
    IdleCases.to_csv(os.path.join(base , "IdleCases.csv"))
    StopCases.to_csv(os.path.join(base , "StopCases.csv"))
    dataRunningId.to_csv(os.path.join(base , "dataRunningId{}.csv"
                        .format(dataRunningId["deviceID"].unique()[0]) ) )
    IdleIntervals.to_csv(os.path.join(base , "IdleIntervals.csv") )
    StoppageIntervals.to_csv(os.path.join(base , "StoppageIntervals.csv") )

if __name__ == '__main__':
    #geolocator = Nominatim(user_agent="NorthCorp")
    base_dir = args.base_dir
    filename = args.file
    save = args.save
    plot = args.plot
    filename = os.path.join(base_dir , filename)
    data = pd.read_csv(filename)
    data_sort = data.sort_values(["date"]  , ascending=True)
    data_sort.drop(columns="Unnamed: 0" , inplace=True)
    data_sort["deviceID"] = data_sort["deviceID"].apply(lambda x: "{:.2f}".format(x))
    IdleCases = data_sort[data_sort.vehicleSpeed == 0] 
    IdleCases = IdleCases[IdleCases.engineSpeed > 0]
    StopCases = data_sort[data_sort.vehicleSpeed == 0]
    StopCases = StopCases[StopCases.engineSpeed == 0 ]
    dataRunning = data_sort.copy()
    dataRunning["Running"] = np.where( (dataRunning["engineSpeed"] > 0)  , 1 , 0)
    dataRunningId = dataRunning[dataRunning.deviceID == dataRunning.deviceID.unique()[0]]
    dataRunningId["date_object"] = dataRunningId["date"].apply(
        lambda x: datetime.datetime.strptime(x , "%Y-%m-%d %H:%M:%S.0"))
    dataRunningId["dateSeconds"] = dataRunningId["date_object"].apply(
        lambda x: (x - datetime.datetime(1970,1,1)).total_seconds() )
    times = dataRunningId["dateSeconds"].values
    was_one = False
    result = []
    resutlt_latitude= []
    resutlt_longitude = []
    result_date = []
    for index  , time in enumerate(times) :
        if dataRunningId.iloc[index]["Running"] == 1 :
            if not was_one:
                startTime = time
                startDate = dataRunningId.iloc[index]["date"]
            was_one = True
        elif dataRunningId.iloc[index]["Running"] == 0 :
            if was_one :
                result.append(time - startTime)
                result_date.append(startDate)
                resutlt_latitude.append(dataRunningId.iloc[index - 1]["latitude"])
                resutlt_longitude.append(dataRunningId.iloc[index - 1]["longitude"])
            was_one = False
    times = dataRunningId["dateSeconds"].values
    was_zero = False
    result0 = []
    resutlt0_latitude= []
    resutlt0_longitude = []
    result0_date = []
    for index  , time in enumerate(times) :
        if dataRunningId.iloc[index]["Running"] == 0 :
            if not was_zero:
                startTime = time
                startDate = dataRunningId.iloc[index]["date"]
            was_zero = True
        elif dataRunningId.iloc[index]["Running"] == 1 :
            if was_zero :
                result0.append(time - startTime)
                result0_date.append(startDate)
                resutlt0_latitude.append(dataRunningId.iloc[index - 1]["latitude"])
                resutlt0_longitude.append(dataRunningId.iloc[index - 1]["longitude"])
            was_zero = False
    
    IdleIntervals = pd.DataFrame( data=[np.arange(len(result)) , result_date , result, resutlt_latitude , resutlt_longitude] )
    StoppageIntervals = pd.DataFrame( data=[np.arange(len(result0)) , result0_date , result0, resutlt0_latitude , resutlt0_longitude] )
    #result_location_str = [geolocator.reverse(*tup) for tup in resutlt_location]
    
    IdleIntervals = process(IdleIntervals)
    StoppageIntervals = process(StoppageIntervals)
    # Saving All relevant files
    if save:
        saveFiles(base_dir , data_sort , dataRunning , dataRunningId , IdleCases , IdleIntervals , StopCases , StoppageIntervals)
    mi = 0
    ma = 0
    if plot is not None:
        while True:
            mi = int(input("Min Limit : "))
            ma = int(input("Max Limit : "))
            if mi == 0 and ma == 0 :
                break
            if plot == "idle":
                plotter(mi,ma , IdleIntervals , "Idle")
            elif plot == "stop":
                plotter(mi,ma , StoppageIntervals , "Stop")
    
    #shp_file = os.path.join(base , "MMRDA_Manual.shp")
    # from shapely.geometry import Point ,Polygon
    # import descartes
    # import geopandas as gpd
    # street_map = gpd.read_file(shp_file)
    # geometry = [Point(xy) for xy in zip(intervals["Longitude"] , intervals["Latitude"]) ]
    # crs = { 'init' : 'epsg:4326' }
    # geo_df = gpd.GeoDataFrame(intervals , crs = crs , geometry=geometry)
    # fig , ax = plt.subplots(figsize=(15 , 15))
    # street_map.plot(ax = ax)
    # geo_df.plot(ax = ax , markersize = 20 , color = "red"  , marker = "o")