import ee
import geemap
import time
import os
import uuid
import numpy as np
import geopandas as gpd
from urllib.request import urlretrieve


def uploadAsset(collection, description, assetId, wait=True):
    # Créer la tache d'export
    task = ee.batch.Export.table.toAsset(
        collection=collection,
        description=description,
        assetId=assetId
    )

    # Démarrer la tache d'export
    start = time.time()
    task.start()

    # Surveiller la tache d'export si wait
    if wait:
        while task.active():
            print(f'\rUploading asset... ({time.time() - start}s elapsed)', end=" ")
            time.sleep(5)
        print(f'\rEnd of asset upload ({time.time() - start}s elapsed). You can reload your asset with this assetId: {assetId}')

        # Vérifier que la tache d'export s'est terminée correctement
        if task.status()['state'] == 'COMPLETED':
            return True
        else:
            print('{}'.format(task.status()))
            return False #TODO: replace by raise error
    
    # Si pas wait, on attends pas la fin de la tache d'import et on renvoie juste son id
    else:
        return task.id


def waitTasks(task_list):
    start = time.time()

    waitlist = [task for task in ee.batch.Task.list() if task.id in task_list]
    running = [task for task in waitlist if task.active()]

    while len(running) > 0:
        print(f'\rWait for {len(running)}/{len(waitlist)} tasks to finish ({time.time() - start}s elapsed)', end=' ')
        time.sleep(5)
        running = [task for task in waitlist if task.active()]
    
    print(f'\rAll {len(waitlist)} tasks finished ({time.time() - start}s elapsed)')


def uploadDGOs(dgo_shapefile_path, simplify_tolerance=15, ee_project_name='ee-glourb'):

    if simplify_tolerance < 1:
        print('Simplify tolerance should be >= 1')
        return
    
    gdf = gpd.read_file(dgo_shapefile_path)
    gdf['geometry'] = gdf.simplify(simplify_tolerance)

    # Si il y a moins de 80 DGOs, on peux les importer direct dans GEE
    if gdf.shape[0] <= 80:
        # Charger les DGOs dans EarthEngine
        dgo_shp = geemap.gdf_to_ee(gdf)

        # Uploader l'asset
        assetName = f'{os.path.splitext(os.path.basename(dgo_shapefile_path))[0]}_{uuid.uuid4().hex}'
        assetId = f'projects/{ee_project_name}/assets/dgos/{assetName}'
        if uploadAsset(dgo_shp, f'DGOs {assetName} uploaded from glourbee', assetId):
            # Renvoyer l'asset exporté et son id
            return(assetId, ee.FeatureCollection(assetId))
        else:
            return #TODO: replace by raise error
    
    # Si il y a plus de 80 DGOs, on dépasse la payload request size de GEE, il faut découper le shapefile pour l'uploader, puis le réassembler
    else:
        nsplit = round(gdf.shape[0] / 80)
        splitted_gdf = np.array_split(gdf, nsplit)

        assets_list = list()
        task_list = list()

        for n, subgdf in enumerate(splitted_gdf):
            dgo_shp = geemap.gdf_to_ee(subgdf)

            # Uploader l'asset
            assetName = f'{os.path.splitext(os.path.basename(dgo_shapefile_path))[0]}_{uuid.uuid4().hex}'
            assetId = f'projects/{ee_project_name}/assets/dgos/tmp/{assetName}'
            taskid = uploadAsset(dgo_shp, f'DGOs {assetName} uploaded from glourbee task {n}-{nsplit}', assetId, wait=False)
            
            if taskid:
                # Ajouter l'assetId à la liste à fusionner
                assets_list.append(assetId)

                # Ajouter la taskid à la liste de taches à surveiller
                task_list.append(taskid)

                print(f'Import DGOs part {n+1}/{len(splitted_gdf)} started.')
            else:
                return #TODO: replace by raise error
        
        # Attendre la fin des uploads
        waitTasks(task_list=task_list)
            
        # Fusionner les assets uploadés en un seul
        output_fc = ee.FeatureCollection([ee.FeatureCollection(asset) for asset in assets_list]).flatten()

        # Uploader l'asset
        assetName = f'{os.path.splitext(os.path.basename(dgo_shapefile_path))[0]}_final_{uuid.uuid4().hex}'
        assetId = f'projects/{ee_project_name}/assets/dgos/{assetName}'
        if uploadAsset(output_fc, 'DGOs uploaded from glourbee notebook', assetId):
            # Supprimer les assets temporaires
            for asset in assets_list:
                ee.data.deleteAsset(asset)

            # Renvoyer l'asset final et son assetId
            return(assetId, ee.FeatureCollection(assetId))

        else:
            return #TODO: replace by raise error


def downloadMetrics(metrics, output_file, ee_project_name='ee-glourb'):
    # Calculer l'asset
    assetName = f'{os.path.splitext(os.path.basename(output_file))[0]}_{uuid.uuid4().hex}'
    assetId = f'projects/{ee_project_name}/assets/metrics/{assetName}'
    if not uploadAsset(metrics, 'Metrics uploaded from glourbee notebook', assetId):
        return #TODO: replace by raise error
    else:
        # Recharger l'asset
        asset = ee.FeatureCollection(assetId)

        # Nettoyer les champs et supprimer les géométries pour alléger la sortie
        cleaned = asset.select(propertySelectors=[
                                    'DATE',
                                    'AC_AREA',
                                    'CLOUD_SCORE',
                                    'COVERAGE_SCORE',
                                    'DATE_ACQUIRED',
                                    'DGO_FID',
                                    'MEAN_AC_MNDWI',
                                    'MEAN_AC_NDVI',
                                    'MEAN_MNDWI',
                                    'MEAN_NDVI',
                                    'MEAN_VEGETATION_MNDWI',
                                    'MEAN_VEGETATION_NDVI',
                                    'MEAN_WATER_MNDWI',
                                    'VEGETATION_AREA',
                                    'VEGETATION_PERIMETER',
                                    'WATER_AREA',
                                    'WATER_PERIMETER'],
                                retainGeometry=False)

        # Télécharger le csv
        urlretrieve(cleaned.getDownloadURL(), output_file)
