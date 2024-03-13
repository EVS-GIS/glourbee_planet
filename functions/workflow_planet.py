import ee
import os
import uuid
import numpy as np
import pandas as pd

import tempfile

from urllib.request import urlretrieve
from urllib.error import HTTPError

from glourbee import (
    classification_planet,
    dgo_metrics_planet,
    workflow_planet
)

# Définition des noms de bandes 
tempdir = tempfile.mkdtemp(prefix='glourbee_')

def startWorkflow(dgo_assetID: str,
                  ee_project_name: str,
                  planet_collection_assetID: str):
    
    dgo_features = ee.FeatureCollection(dgo_assetID)

    workflow_id = uuid.uuid4().hex

    bnd_names = ['blue', 'green', 'red', 'nir', 'CLEAR']
    scale = 3

    # 1 - load Image Collection
    planet_IC = ee.ImageCollection(planet_collection_assetID).select(['B1', 'B2', 'B3', 'B4','Q1'], bnd_names).filterBounds(dgo_features)

    # 2 - Apply NDVI and NDWI calculation
    collection = classification_planet.calculateIndicators(planet_IC)

    # 3 - Classify the objects using the indicators
    collection = classification_planet.classifyObjects(collection)

    # 4 - Metrics calculation
    metrics = dgo_metrics_planet.calculateDGOsMetrics(collection=collection, dgos=dgo_features, scale = scale)

    # Create computation task
    assetName = f'{workflow_id}'
    assetId = f'projects/{ee_project_name}/assets/metrics/tmp/{assetName}'

    task = ee.batch.Export.table.toAsset(
        collection=metrics,
        description=f'Computation task for run {workflow_id}',
        assetId=assetId
    )
    task.start()

    print(f'Computation task started')
    
    return workflow_id

def workflowState(run_id):
    ee_tasks = ee.data.getTaskList()
    tasks = [t for t in ee_tasks if f'run {run_id}' in t['description']]

    # Check all tasks
    completed = len([t for t in tasks if t['state'] == 'COMPLETED'])
    running = len([t for t in tasks if t['state'] == 'RUNNING'])
    pending = len([t for t in tasks if t['state'] == 'PENDING'])
    ready = len([t for t in tasks if t['state'] == 'READY'])
    failed = len([t for t in tasks if t['state'] == 'FAILED'])

    print(f'{completed} tasks completed.')
    print(f'{running} tasks running.')
    print(f'{pending} tasks pending.')
    print(f'{ready} tasks ready.')
    print(f'{failed} tasks failed.')

    return tasks


def cancelWorkflow(run_id):
    ee_tasks = ee.data.getTaskList()
    tasks = [t for t in ee_tasks if f'run {run_id}' in t['description']]

    task_ids = [t['id'] for t in tasks]

    for tid in task_ids:
        ee.data.cancelTask(tid)


def getResults(run_id, ee_project_name, output_csv, overwrite=False, remove_tmp=False):
    ee_tasks = ee.data.getTaskList()
    stacked_uris = [t['destination_uris'] for t in ee_tasks if f'run {run_id}' in t['description'] and t['state'] == 'COMPLETED']
    uris = [uri.split(f'{ee_project_name}/assets/')[1] for sublist in stacked_uris for uri in sublist]

    assets = [f'projects/{ee_project_name}/assets/{uri}' for uri in uris]
    temp_csv_list = [os.path.join(tempdir, f'{os.path.basename(a)}.tmp.csv') for a in assets]

    properties_list = [
        'DATE',
        'DGO_FID',
        'acquired',
        'AC_AREA',
        'CLEAR_SCORE',
        'COVERAGE_SCORE',
        'MEAN_AC_NDWI',
        'MEAN_AC_NDVI',
        'MEAN_NDWI',
        'MEAN_NDVI',
        'MEAN_VEGETATION_NDWI',
        'MEAN_VEGETATION_NDVI',
        'MEAN_WATER_NDWI',
        'VEGETATION_AREA',
        'VEGETATION_PERIMETER',
        'WATER_AREA',
        'WATER_PERIMETER']
    
    for assetName, path in zip(assets, temp_csv_list):
        if not os.path.exists(path) or overwrite:
            asset = ee.FeatureCollection(assetName)
            clean_fc = asset.select(propertySelectors=properties_list,
                            retainGeometry=False)
            try:
                urlretrieve(clean_fc.getDownloadUrl(), path)
            except HTTPError:
                # Si c'est impossible de télécharger l'asset nettoyé, télécharger l'asset complet et le nettoyer localement
                urlretrieve(asset.getDownloadUrl(), path)
                df = pd.read_csv(path, index_col=None, header=0)
                df = df[properties_list]
                df.to_csv(path)
        else:
            continue

    output_dfs = []
    for filename in temp_csv_list:
        df = pd.read_csv(filename, index_col=None, header=0)
        output_dfs.append(df)

        if remove_tmp:
            os.remove(filename)

    df = pd.concat(output_dfs, axis=0, ignore_index=True)
    df.to_csv(output_csv)


def cleanAssets(run_id, ee_project_name):
    ee_tasks = ee.data.getTaskList()
    stacked_uris = [t['destination_uris'] for t in ee_tasks if f'run {run_id}' in t['description'] and t['state'] == 'COMPLETED']
    uris = [uri.split(f'{ee_project_name}/assets/')[1] for sublist in stacked_uris for uri in sublist]

    assets_list = [f'projects/{ee_project_name}/assets/{uri}' for uri in uris]
    for asset in assets_list:
        ee.data.deleteAsset(asset)