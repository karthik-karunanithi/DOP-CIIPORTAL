import pandas as pd
import numpy as np
import json
import os
import pathlib
from datetime import datetime
import math
from random import sample
from azure.storage.blob import BlobServiceClient, ContainerClient
import logging

# Handling Path for correct file reference
PATH = pathlib.Path(__file__).parent.resolve()

with open(os.path.join(PATH,"_cnn.json"), "r") as d: _CONN = json.load(d)
blob_conn = _CONN["blob_storage_account"]["conn"]
blob_container = _CONN["blob_storage_account"]["container"]


# Download blob content for processing
def dlod_blob(DOC_PATH) : 
    # Downloading PDF from blob storage
    container_client = ContainerClient.from_connection_string(conn_str=blob_conn, container_name=blob_container)
    blob = container_client.get_blob_client(DOC_PATH)
    file = (blob.download_blob().readall())
    return file

def load_data():
    # Reading modelConfig.json file
    d = dlod_blob("ml/cii/modelConfig.json")
    data = json.loads(d)
    return data

def load_draft():
    # Reading draftConfig.json file
    with open(os.path.join(PATH,"draftConfig.json"), "r") as d: draft = json.load(d)
    return draft

def fscurve(vessel,draft,speed = None):

    # Loading all required configurations
    MODELS = load_data()
    model = MODELS[vessel]
    draftLimit = load_draft()[model["VesselClass"]]
    LASTDRYDOCK = model["LastDryDock"]
    HULLPERF_YEAR = float(math.floor((datetime.now()-datetime.strptime(LASTDRYDOCK,"%Y-%m-%d %H:%M:%S")).days/365/5))
    # print(model["Yearly"]["Ballast"][str(HULLPERF_YEAR)])
    
    # Setting which model parameters to use for model (base model)
    condition = "Loaded" if draft > draftLimit else "Ballast"
    print(f"Performing simulation under {condition} condition")
    try: model = model[condition]
    except KeyError : 
        # If base model is not available, find YoY hull performance model
        print(f"Extracting model using YoY Hull Performance at {str(HULLPERF_YEAR)}")
        try : model = model["Yearly"][condition][str(HULLPERF_YEAR)]
        except KeyError : 
            # If YoY hull performance model is not available, use sister vessel's YoY Hull Performance 
            # from same Class Type as representative model
            rep_vessel = sample([i for i in MODELS.keys() if ((MODELS[i]["VesselClass"]==model["VesselClass"]) & (i != vessel))],1)[0]
            print(f"Using Vessel {rep_vessel} as Representative")
            try: model = MODELS[rep_vessel]["Yearly"][condition][str(HULLPERF_YEAR)]
            except KeyError as ex:
                logging.error(ex)
                print("Model Does not Exist")
    try:
        # Building Fuel-Speed Curve Data
        res = []
        for x in np.arange(10.0,20,0.1): 
            res.append({"CalcSpeed" : x, "Scored Labels":model["Speed_coefficient"]*(x**2)+model["Intercept"]})
            # res.append([x, model["Speed_coefficient"]*(x**2)+model["Intercept"]])

        if speed is None : 
            return res
        else : 
            return (
                res, #return fuelspeed curve at index [0]
                model["Speed_coefficient"]*(speed**2)+model["Intercept"] # return exact fuel consumption at given speed at index [1]
                )
    except KeyError as err:
        logging.error(err)
        return "Model Data Does Not Exist"

if __name__ == "__main__" : 
    isDesiredCii = False
    isDesireSchedule = True
    VESSELID = "MSMA00000196"
    MEANDRAFT = 20
    _CALCSPEED = 15
    
    try:
        if isDesiredCii : 
            dat_fscurve = fscurve(VESSELID,MEANDRAFT)
            # print(dat_fscurve)
            # Continue existing code to find fuel consimption

        else : 
            dat_fscurve = fscurve(VESSELID,MEANDRAFT,_CALCSPEED)
            print(pd.DataFrame(dat_fscurve[0])) # Fuel-Speed curve list data
            print(dat_fscurve[1]) # Fuel Consumption Per day at calculated Speed
        

    except Exception as ex :
        print(ex)
