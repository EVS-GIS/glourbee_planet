import ee
import geemap


def imageVisualization(collection, time_starts, dgo_shp):
    
    output_map = geemap.Map()
    output_map.addLayer(dgo_shp, name='DGOs')
    output_map.center_object(dgo_shp)

    output_map.add_labels(
        dgo_shp,
        "DGO_FID",
        font_size="12pt",
        font_color="black",
        font_family="arial",
        font_weight="bold",
    )
    
    image = collection.filter(ee.Filter.eq('system:time_start', time_starts)).first()
    
    #TODO add layers if band exists
    output_map.addLayer(image, {'bands': ['red', 'green', 'blue']}, 'RGB image')
    output_map.addLayer(image, {'bands': ['nir', 'green', 'blue']}, 'NIR image')
    output_map.addLayer(image, {'bands': ['MNDWI'], 'palette': 'viridis', 'min': -1, 'max': 1}, 'MNDWI image')
    output_map.addLayer(image, {'bands': ['NDVI'], 'palette': 'viridis', 'min': -1, 'max': 1}, 'NDVI image')
    output_map.addLayer(image, {'bands': ['WATER'], 'palette': 'Blues'}, 'Water')
    output_map.addLayer(image, {'bands': ['VEGETATION'], 'palette': 'Greens'}, 'Vegetation')
    output_map.addLayer(image, {'bands': ['AC'], 'palette': 'Reds'}, 'Active Channel')
    
    output_map.addLayerControl()  
    
    return output_map
