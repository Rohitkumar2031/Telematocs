#!/usr/bin/env python
# coding: utf-8

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import LocallyLinearEmbedding
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans , DBSCAN
from sklearn.metrics import silhouette_score
import os
from matplotlib import pyplot as plt
from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import argparse

def attributesAdder(df , dataType , sorting_col):
    if dataType == 'HD':
        df["dateSeconds"] = df["updateddate"].apply(
                    lambda x: datetime.strptime(x , "%Y-%m-%d %H:%M:%S")).apply(
                    lambda x: (x - datetime(2000,1,1)).total_seconds() )
        df.sort_values( sorting_col , inplace=True)
        df["fuel_per_sec"] = df["current_fuel_level"].diff() / df["dateSeconds"].diff()
        df["total_fuel_per_sec"] = df["total_fuel_consumption"].diff() / df["dateSeconds"].diff()
        df.drop(columns="dateSeconds" , inplace=True)
        df.drop(columns="updateddate" , inplace=True)
    elif dataType == 'LMD':
        df.sort_values( sorting_col , inplace=True)
        df["fuel_per_sec"] = df["tripFuel"].diff() / df["utc"].diff()
        df.drop(columns="utc" , inplace=True)
        df.drop(columns="date" , inplace=True)
    df = df.values
    df[np.isnan(df)] = 0
    df[np.isinf(df)] = 0
    return df

parser = argparse.ArgumentParser()
parser.add_argument(
    "--base-dir" , default=r"/home/parth/Machine Learning/Datasets/North Corp/LMD/Raw"
)
parser.add_argument(
    "--plot" , default=False , type=bool
)
parser.add_argument(
    "--threshold" , type=float , default=0.01
)
parser.add_argument(
    "data" , type=str , default="LMD"
)
parser.add_argument(
    "--eps" , type=float , default=0.5
)
args = parser.parse_args()

if __name__ == '__main__':
    first = True
    dataType = args.data
    base_dir = args.base_dir
    plot = args.plot
    threshold = args.threshold
    file_list = os.listdir(base_dir)
    file_list_correct = []

    for file_ in file_list:
        if file_.endswith(".csv"):
            file_list_correct.append(file_)

    for file_ in file_list_correct:
        filename = os.path.join(base_dir , file_)
        data = pd.read_csv(filename , delimiter=',')
        if len(data.columns) == 1:
            data = pd.read_csv(filename , delimiter=';')
        #usefull_cols = [ 'updateddate', 'total_fuel_consumption', 'total_engine_hours', 'latitude' , 'longitude',
        #       'total_distance' , 'time_idle' , 'time_drive', 'speed' , 'current_fuel_level' ]
        if dataType == 'LMD':
            if not len(data.deviceID.unique()) == 1:
                raise Exception("LMD data not Unique ID")
            useful_cols = [ "utc" , "date", 'vehicleSpeed', 'tripFuel' , 'engineCoolantTemp' , 'engineOilPressure' , 'engineOperatingHours' ]
            sorting_col = "utc"
        elif dataType == 'HD':
            if not len(data.vehicleid.unique()) == 1:
                raise Exception("HD data not Unique ID")
            useful_cols = [ 'updateddate', 'total_fuel_consumption', 'current_fuel_level' ]
            sorting_col = "dateSeconds"
        data_use = data[useful_cols]
        data_use = attributesAdder(data_use , dataType , sorting_col)
        scaler = StandardScaler()
        data_use_ = scaler.fit_transform(data_use)
        pca = PCA(n_components = 0.95 )
        ## LLE
        #lle = LocallyLinearEmbedding(n_components=3 , n_neighbors=10 , method='dense')
        #data_use_lle = lle.fit_transform(data_use_)
        data_use_pca = pca.fit_transform(data_use_)
        clustering = DBSCAN(eps=args.eps)
        labels = pd.Series(clustering.fit_predict(data_use_pca))
        data["cluster"] = labels
        print(labels.value_counts())
        n_cluster = len(labels.unique())
        markcluster = data["cluster"].value_counts() < len(data) * threshold
        markcluster = dict(markcluster)
        if plot:
            fig = plt.figure(figsize=[10 , 10])
            ax = plt.axes(projection="3d")
            for cluster in labels.unique():
                data_temp = data_use_pca[data["cluster"] == cluster]
                if not markcluster[cluster] and not cluster == -1:
                    ax.scatter3D(data_temp[: , 0], data_temp[: , 1], data_temp[: , 2] , c=data_temp[: , 3] , marker='o', cmap= plt.get_cmap("brg"))
                else :
                    print("HEre")
                    ax.scatter3D(data_temp[: , 0], data_temp[: , 1], data_temp[: , 2] , c=data_temp[: , 3] , marker='x', cmap= plt.get_cmap("brg") )
            ax.set_title("Abstract Feature Plot with Anomalies (x)")
            plt.show()
        data["Anomaly"] = None
        counter = 0
        for index in range(len(data)):
            x = markcluster[data["cluster"].iloc[ index ]]
            data.at[index , "Anomaly"] = x
            if x :
                counter = counter + 1
        choice = input("{:3d} Anomalies Detected! Save ? (y/n) File:{} ".format(counter , file_.split('.')[0]))
        if choice.lower() == "y":
            data.to_csv("{} anomaly {}.csv".format( dataType , file_.split('.')[0]))
        if first:
            first=False
