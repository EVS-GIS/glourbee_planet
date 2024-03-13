"""
Functions used by the GloUrbEE-UI.

@authors: Julie Limonet, Samuel Dunesme
"""

import ee
import geemap
import streamlit as st
import geopandas as gpd
import os
import numpy as np

from glourbee import __version__ as glourbee_version


### UI

def addHeader(title: str = "Default title"):

    if 'authenticated' not in st.session_state:
        st.switch_page('00_🏠_HomePage.py')

    image_path = os.path.join(st.session_state['ui_directory'], 'lib/img/logo.svg')
    st.image(image_path)

    st.header(title, divider=True)

    with st.sidebar:
        if st.session_state["authenticated"]:
            st.success(f'Authenticated as **{st.session_state["user"]}**', icon="😎")
        else:
            st.warning(f'**Unauthenticated**', icon="🥸")
        
        st.write(f'GloUrbEE version: ```{glourbee_version}```')

        st.write('[Report a bug or ask for new feature](https://github.com/EVS-GIS/glourbee/issues)')


def select_dgos(df, key):
    """
    From https://docs.streamlit.io/knowledge-base/using-streamlit/how-to-get-row-selections
    """
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Selected", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        key=key,
        hide_index=True,
        use_container_width=True,
        column_config={"Selected": st.column_config.CheckboxColumn(required=True),
                       "river_name": st.column_config.TextColumn('Extraction zones name'),
                       "description": st.column_config.TextColumn('Extraction zones description'),
                       "dgo_size": st.column_config.NumberColumn('DGO size if concerned', format='%d m'),
                       "uploader": st.column_config.TextColumn('Uploader'),
                       "upload_date": st.column_config.DatetimeColumn('Upload date')},
        column_order=("Selected", "river_name", "description", "dgo_size", "uploader", "upload_date"),
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Selected]
    return selected_rows.drop('Selected', axis=1)


def select_metrics(df):
    """
    From https://docs.streamlit.io/knowledge-base/using-streamlit/how-to-get-row-selections
    """
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Download", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(df_with_selections,
        hide_index=True,
        use_container_width=True,
        column_config={"Download": st.column_config.CheckboxColumn(required=True),
                       "outdated": st.column_config.TextColumn('Outdated dataset')},
        column_order=("Download", 'outdated', 'satellite_type', 'run_date', 'glourbee_version', 'run_by', 'state', 'start_date', 'end_date', 'cloud_filter', 'cloud_masking', 'mosaic_same_day'),
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Download]
    return selected_rows.drop('Download', axis=1)

"""-----------------------------------------------------------------------------------------------------------------
-------------------------------------------------- Authentication --------------------------------------------------
------------------------------------------------------------------------------------------------------------------"""


def credentials(
    mail="jlimonet@ee-glourb.iam.gserviceaccount.com",
    key1="./ee-glourb-58e556f00841.json",
    key2="./ee-glourb-58e556f00841.json",
):
    """
    Connects to Google Earth Engine using the mail and key provided by the user

    Parameters
    ----------
    mail : str
        mail of the user, by default "jlimonet@ee-glourb.iam.gserviceaccount.com"
    key1 : str
        path to their json file, by default "./ee-glourb-58e556f00841.json"
    key2 : str
        path to their json file if they uploaded it through the streamlit file_uploader,
        by default "./ee-glourb-58e556f00841.json"
    """
    if key1 != "":
        try:
            credentials = ee.ServiceAccountCredentials(mail, key1)
            ee.Initialize(credentials)
            return True

        except ee.EEException as e:
            return False

    if key2 != "":
        try:
            credentials = ee.ServiceAccountCredentials(mail, key2)
            ee.Initialize(credentials)
            return True

        except ee.EEException as e:
            return False


"""-----------------------------------------------------------------------------------------------------------------
------------------------------------------------------ DGOs --------------------------------------------------------
------------------------------------------------------------------------------------------------------------------"""


def upload_dgos(
    DGO="./example_data/Yamuna_segm_2km_UTF8.shp", ee_project_name="ee-glourb"
):
    """Returns the dgos already uploaded to Earth Engine for the same project

    Parameters
    ----------
    DGO : str, optional
        id of the wanted asset, by default './example_data/Yamuna_segm_2km_UTF8.shp'
    ee_project_name : str, optional
        name of the project in Google Earth Engine, by default 'ee-glourb'
    """
    from glourbee import assets_management

    dgo_assetId, dgo_features = assets_management.uploadDGOs(
        DGO, ee_project_name=ee_project_name, simplify_tolerance=15
    )
    return (dgo_assetId, dgo_features)


def display_map(title, location=[0, 0], dgo_features=None, zoom=8):
    """Displays a map centered on the location in Streamlit

    Parameters
    ----------
    title : str
        title of the map
    location : list, optional
        tuple of the latitude, longitude to be centered on, by default [0,0]
    dgo_features : _type_, optional
        dgos that can be added on the map, by default None
    zoom : int, optional
        Zoom on the map, by default 8
    """
    import folium
    import geemap
    from streamlit_folium import folium_static

    # Create a folium map
    m = folium.Map(location=location, zoom_start=zoom, title=title)

    if dgo_features:
        features = dgo_features
        folium.GeoJson(data=features.getInfo(), name="DGO Features").add_to(m)

    return m


def cities(file_path="cities.txt"):
    """Gets the list and position of the cities studied in GloUrb

    Parameters
    ----------
    file_path : str, optional
        _description_ file containing the information
    """
    import re

    with open(file_path, "r") as file:
        lines = file.readlines()

    pattern = re.compile(
        r"(\S+),\((-?\d+\.\d+),(-?\d+\.\d+),(-?\d+\.\d+),(-?\d+\.\d+)\)"
    )

    city_data = {}

    for line in lines:
        match = pattern.match(line)
        if match:
            city_name, lat1, lon1, lat2, lon2 = match.groups()
            city_data[city_name] = {
                "latitude": (float(lat1) + float(lat2)) / 2,
                "longitude": (float(lon1) + float(lon2)) / 2,
            }

    return city_data


def dgo_to_search(town_to_search, river_to_search):
    """Gets the dgos from GEE that match the town_to_search and/or river_to_search

    Parameters
    ----------
    town_to_search : str
        town studied
    river_to_search : str
        river studied

    Returns
    -------
    list
        list of the matching dgos id and time of upload
    """
    list_assets = ee.data.listAssets({'parent': "projects/ee-glourb/assets/dgos"})["assets"]
    id = []
    update_times = []
    for i in range(len(list_assets)):
        id.append(
            ee.data.listAssets({'parent': "projects/ee-glourb/assets/dgos"})["assets"][i]["id"]
        )
        update_times.append(
            ee.data.listAssets({'parent': "projects/ee-glourb/assets/dgos"})["assets"][i][
                "updateTime"
            ]
        )

    matching_lines = []
    matching_times = []
    for i in range(len(list_assets)):
        if (
            town_to_search.lower() in id[i].lower()
            or river_to_search.lower() in id[i].lower()
        ):
            matching_lines.append(id[i])
            matching_times.append(update_times[i])

    return matching_lines, matching_times


def remove_line_by_criteria(id_to_remove):
    """Removes a dgo uploaded on GEE by its id

    Parameters
    ----------
    id_to_remove : str
        id of the dgo to remove
    """
    asset_path_to_delete = id_to_remove
    try:
        ee.data.deleteAsset(asset_path_to_delete)

    except Exception as e:
        st.error(f"Error: {str(e)}")


def uploadDGOs(
    dgo_shapefile, file_name, simplify_tolerance=15, ee_project_name="ee-glourb"
):
    """Function to upload dgos to GEE.

    Parameters
    ----------
    dgo_shapefile : .shp
        shapefile containing the dgos

    file_name : str
        Name of the shape file

    simplify_tolerance : int
        parameter for the upload

    ee_project_name : str
        name of the project on GEE
    """
    from fiona import drvsupport
    import fiona
    from glourbee import assets_management

    gdf = gpd.read_file(dgo_shapefile)
    gdf["geometry"] = gdf.simplify(simplify_tolerance)

    # If there are fewer than 80 DGOs, import directly into GEE
    if gdf.shape[0] <= 80:
        # Convert GeoDataFrame to Earth Engine FeatureCollection
        dgo_shp = geemap.gdf_to_ee(gdf)

        # Upload the asset
        assetName = (
            f"{os.path.splitext(os.path.basename(file_name))[0]}_{uuid.uuid4().hex}"
        )
        assetId = f"projects/{ee_project_name}/assets/dgos/{assetName}"

        if assets_management.uploadAsset(
            dgo_shp, "DGOs uploaded from glourbee notebook", assetId
        ):
            # Return the exported asset and its ID
            return assetId, ee.FeatureCollection(assetId)
        else:
            return  # TODO: replace by raise error

    # If there are more than 80 DGOs, split the shapefile for upload and then reassemble
    else:
        nsplit = round(gdf.shape[0] / 80)
        splitted_gdf = np.array_split(gdf, nsplit)

        assets_list = []
        task_list = []

        for n, subgdf in enumerate(splitted_gdf):
            dgo_shp = geemap.gdf_to_ee(subgdf)

            # Upload the asset
            assetName = (
                f"{os.path.splitext(os.path.basename(file_name))[0]}_{uuid.uuid4().hex}"
            )
            assetId = f"projects/{ee_project_name}/assets/dgos/tmp/{assetName}"
            taskid = assets_management.uploadAsset(
                dgo_shp, "DGOs uploaded from glourbee notebook", assetId, wait=False
            )

            if taskid:
                # Add the assetId to the list to merge
                assets_list.append(assetId)
                # Add the taskid to the list of tasks to monitor
                task_list.append(taskid)

                print(f"Import DGOs part {n + 1}/{len(splitted_gdf)} started.")
            else:
                return  # TODO: replace by raise error

        # Wait for the uploads to finish
        assets_management.waitTasks(task_list=task_list)

        # Merge the uploaded assets into one
        output_fc = ee.FeatureCollection(
            [ee.FeatureCollection(asset) for asset in assets_list]
        ).flatten()

        # Upload the asset
        assetName = f"{os.path.splitext(os.path.basename(file_name))[0]}_final_{uuid.uuid4().hex}"
        assetId = f"projects/{ee_project_name}/assets/dgos/{assetName}"

        if assets_management.uploadAsset(
            output_fc, "DGOs uploaded from glourbee notebook", assetId
        ):
            # Delete temporary assets
            for asset in assets_list:
                ee.data.deleteAsset(asset)

            # Return the final asset and its assetId
            return assetId, ee.FeatureCollection(assetId)
        else:
            return  # TODO: replace by raise error


"""-----------------------------------------------------------------------------------------------------------------
------------------------------------------------------ Metrics --------------------------------------------------------
------------------------------------------------------------------------------------------------------------------"""


def getResults(
    run_id, properties_list, ee_project_name, tempdir, overwrite=False, remove_tmp=False
):
    """Function to get the csv file containing the metrics

    Parameters
    ----------
    run_id : str
        id of the task
    properties_list : list
        list of the metrics to calculate
    ee_project_name : str
        name of the project
    tempdir : directory
        tempory directory
    overwrite : bool, optional
        option to overwrite the file, by default False
    remove_tmp : bool, optional
        option to remove the temporary file , by default False
    """
    from urllib.error import HTTPError
    from urllib.request import urlretrieve
    import pandas as pd

    ee_tasks = ee.data.getTaskList()
    stacked_uris = [
        t["destination_uris"]
        for t in ee_tasks
        if f"run {run_id}" in t["description"] and t["state"] == "COMPLETED"
    ]
    uris = [
        uri.split(f"{ee_project_name}/assets/")[1]
        for sublist in stacked_uris
        for uri in sublist
    ]

    assets = [f"projects/{ee_project_name}/assets/{uri}" for uri in uris]
    temp_csv_list = [
        os.path.join(tempdir, f"{os.path.basename(a)}.tmp.csv") for a in assets
    ]

    # Create a list to store data for Streamlit file download
    download_data = []

    for assetName, path in zip(assets, temp_csv_list):
        if not os.path.exists(path) or overwrite:
            asset = ee.FeatureCollection(assetName)
            clean_fc = asset.select(
                propertySelectors=properties_list, retainGeometry=False
            )

            try:
                # Use Streamlit's st.file_download to add data for download
                st.file_download(
                    path, label=f"Download {os.path.basename(assetName)} CSV"
                )
            except HTTPError:
                # Handle the case if download fails
                st.warning(f"Failed to download {os.path.basename(assetName)} CSV.")

                # If it's impossible to download the cleaned asset, download the complete asset and clean it locally
                st.info(
                    f"Downloading the complete asset {os.path.basename(assetName)} and cleaning it locally."
                )
                urlretrieve(asset.getDownloadUrl(), path)
                df = pd.read_csv(path, index_col=None, header=0)
                df = df[properties_list]
                df.to_csv(path)
        else:
            continue

        # Add data for Streamlit file download
        download_data.append(
            {"asset_name": os.path.basename(assetName), "file_path": path}
        )

    # You can use download_data for customizing download behavior in Streamlit
    st.write(download_data)

    # You may choose to remove the temporary files if needed
    if remove_tmp:
        for filename in temp_csv_list:
            os.remove(filename)


def workflowState(run_id):
    """gives the state of the workflow

    Parameters
    ----------
    run_id : str
        id of the task

    Returns
    -------
    str
        number of tasks in each state
    """
    ee_tasks = ee.data.getTaskList()
    tasks = [t for t in ee_tasks if f"run {run_id}" in t["description"]]

    # Check all tasks
    completed = len([t for t in tasks if t["state"] == "COMPLETED"])
    running = len([t for t in tasks if t["state"] == "RUNNING"])
    pending = len([t for t in tasks if t["state"] == "PENDING"])
    ready = len([t for t in tasks if t["state"] == "READY"])
    failed = len([t for t in tasks if t["state"] == "FAILED"])

    st.write(f"{completed} tasks completed.")
    st.write(f"{running} tasks running.")
    st.write(f"{pending} tasks pending.")
    st.write(f"{ready} tasks ready.")
    st.write(f"{failed} tasks failed.")

    return tasks
