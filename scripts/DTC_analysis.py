#!/usr/bin/env python
# coding: utf-8


import multiprocessing
import os
import time
from functools import partial

import pandas as pd


# Only This Function Should be changed for different computer
def loadData():
    base_dir = '/home/parth/Machine Learning/Datasets/North Corp/DTC/August'
    filePcode = "Top_LMD_DTC_SPN.csv"
    file_list = os.listdir(base_dir)
    file_list_corrected = []
    for file_ in file_list:
        if file_.endswith(".csv") and file_ != filePcode:
            file_list_corrected.append(file_)
    file_list = file_list_corrected
    filename = os.path.join(base_dir, file_list[0])  # Loading should be done using threads if multiple files
    data = pd.read_csv(filename)
    pcode_data = pd.read_csv(os.path.join(base_dir, filePcode))
    return data, pcode_data


def preProcessData(data, pcode_data):
    ids = data.deviceID.unique()
    device_data = []
    for id_ in ids:
        device_data.append(data[data.deviceID == id_])
    pcode_data["spn_fmi"] = [(a, b) for a, b in zip(pcode_data["SPN"], pcode_data["FMI"])]
    for i, device_data_ in enumerate(device_data):
        device_data_ = device_data_.reset_index()
        device_data_["spn_fmi"] = [(a, b) for a, b in zip(device_data_["spn"], device_data_["fmi"])]
        device_data[i] = device_data_
    for i in range(len(device_data)):
        device_data[i] = pd.merge(
            device_data[i], pcode_data[["Error codes ", "spn_fmi"]],
            how='left', on="spn_fmi"
        )
        device_data[i] = device_data[i].rename(columns={'Error codes ': 'Pcode'})
    for i in range(len(device_data)):
        device_data[i].sort_values("utc", inplace=True, ascending=True)
    return device_data, ids


def getCodesAround(time_interval_before, time_interval_after, device_data_):  # in minutes
    time_interval_before = int(time_interval_before * 60)
    time_interval_after = int(time_interval_after * 60)
    codes = device_data_.Pcode.notna()
    critical_utcs = device_data_[codes].utc
    critical_ranges = critical_utcs.apply(lambda x: range(x - time_interval_before, x + time_interval_after))
    masks = [device_data_.utc.isin(critical_range) for critical_range in critical_ranges]
    device_dataPcode = [device_data_[mask] for mask in masks]
    return device_dataPcode


def getPDict(device_data, time, when='before'):
    times = (time, 1 / 60) if when == 'before' else (1 / 60, time)
    return [x.spn_fmi.value_counts().to_dict() for x in getCodesAround(*times, device_data)]


def populateData(timeBefore, timeAfter, device_data):
    beforeDicts = getPDict(device_data, timeBefore, 'before')
    afterDicts = getPDict(device_data, timeAfter, 'after')
    codes = [x[x.Pcode.notna()].Pcode.values[0] for x in getCodesAround(1 / 60, 1 / 60, device_data)]
    dataDict = {"Before": beforeDicts, "Codes": codes, "After": afterDicts}
    return dataDict


def populateWrapper(y, timeBefore, timeAfter):
    return populateData(timeBefore, timeAfter, device_data=y)


def getCompleteData(timeBefore, timeAfter, device_data, ids):
    completeData = []
    data_list = []

    wrap = partial(populateWrapper, timeBefore=timeBefore, timeAfter=timeAfter)
    with multiprocessing.Pool() as pool:
        data_list = pool.map(wrap, device_data)
    # data_list = map(wrap, device_data) # Uncomment to compare non-parallel version
    for device_data_, id_ in zip(data_list, ids):
        dic = {'data': device_data_, 'id': id_}
        completeData.append(dic)
    return completeData


def dataPipeline(loadDataFunc=loadData):
    start = time.time()
    unprocessed = loadDataFunc()
    loading_time = time.time()
    intermediate = preProcessData(*unprocessed)
    preprocess_time = time.time()
    data_processed = getCompleteData(30, 30, *intermediate)
    complete_time = time.time()

    complete_time = complete_time - preprocess_time
    preprocess_time = preprocess_time - loading_time
    loading_time = loading_time - start

    print(
        " Loading Time    : {:.2f} Seconds\n".format(loading_time),
        "PreProcess Time : {:.2f} Seconds\n".format(preprocess_time),
        "Process Time    : {:.2f} Seconds".format(complete_time),
    )
    return data_processed


data_processed = dataPipeline()

# Uncomment to Save
# json.dump(str(data_processed) , open("file.json" , 'w+'))
