import ee

def calculateClearScore(image, dgo_shape, scale):
    
    # Calculate the number of clear pixels within the AOI.
    clear_size = image.unmask().select('CLEAR').eq(1).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=dgo_shape.geometry(),
        scale=scale
    ).getNumber('CLEAR')
    
    # Calculate the total number of pixels within the AOI.
    full_size = image.select('CLEAR').reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=dgo_shape.geometry(),
        scale=scale
    ).getNumber('CLEAR')
    
    # Calculate the clear score as the ratio of clear pixels to total pixels, multiplied by 100 to get a percentage.
    clear_score = clear_size.divide(full_size).multiply(100).round()

    return clear_score
    

def calculateCoverage(image, dgo_shape, scale):
    # Calculate how much an image covers a DGO

    # Calculate the expected total number of pixels in the AOI at the given scale
    aoi_pixel_count = dgo_shape.area().divide(scale**2)
    
    # Ensure the image is unmasked to count all pixels within the geometry
    unmasked_image = image.unmask(0)

    # Count the number of actual data pixels within the AOI
    act_pixels = unmasked_image.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=dgo_shape.geometry(),
        scale=scale,
        maxPixels=1e16
    ).getNumber('blue')  # Assuming B2 as a representative band

    # Calculate the expected total number of pixels in the AOI at the given scale
    aoi_pixel_count = dgo_shape.area().divide(scale**2)

    # Calculate the coverage score as the ratio of actual to expected pixels
    coverage_score = act_pixels.divide(aoi_pixel_count).multiply(100).round()

    return coverage_score


def calculateWaterMetrics(image, dgo, scale):
    # Vectorisation des surfaces
    water = image.select('WATER').reduceToVectors(
        geometry = dgo.geometry(),
        scale = scale,
        eightConnected = True,
        maxPixels = 1e16,
        geometryType = 'polygon')
    
    # Séparer les surfaces en eau et les surfaces émergées
    vector_water = water.filter("label == 1")
    # vector_dry = water.filter("label == 0")
    
    # Simplifier les géométries pour le périmètre
    geoms_water = vector_water.geometry()

    # Calculer les percentiles de taille de polygones
    water_percentiles = vector_water.aggregate_array('count').reduce(ee.Reducer.percentile(
        percentiles=list(range(0,110,10)),
        outputNames=[f'WATER_POLYGONS_p{pc}' for pc in range(0,110,10)]
    ))

    # Initialisation du dictionnaire des résultats
    results = ee.Dictionary(water_percentiles).combine(ee.Dictionary({
        # Calculer le nombre de polygones d'eau
        'WATER_POLYGONS': vector_water.size(),

        # Calculer l'aire des surfaces en eau
        'WATER_AREA': image.select('WATER').reduceRegion(
                reducer = ee.Reducer.sum(),
                geometry = vector_water,
                scale = scale
            ).getNumber('WATER'),

        # Calculer les périmètres
        'WATER_PERIMETER': geoms_water.perimeter(scale),

        # Calcul du NDWI moyen des surfaces en eau
        'MEAN_WATER_NDWI': image.select('NDWI').reduceRegion(
                reducer = ee.Reducer.mean(),
                geometry = vector_water,
                scale = scale
            ).getNumber('NDWI'),

        # Calcul du NDWI moyen de tout le DGO
        'MEAN_NDWI': image.select('NDWI').reduceRegion(
                reducer = ee.Reducer.mean(),
                geometry = dgo.geometry(),
                scale = scale
            ).getNumber('NDWI'),
    }))
    
    return results


def calculateVegetationMetrics(image, dgo, scale):
    # Vectorisation des surfaces
    vectors = image.select('VEGETATION').reduceToVectors(
        geometry = dgo.geometry(),
        scale = scale,
        eightConnected = True,
        maxPixels = 1e16,
        geometryType = 'polygon')
    
    # Séparer les surfaces végétation du reste
    vector_vegetation = vectors.filter("label == 1")
    
    # Simplifier les géométries pour le périmètre.
    geom_vegetation = vector_vegetation.geometry()

    # Calculer les percentiles de taille de polygones
    veget_percentiles = vector_vegetation.aggregate_array('count').reduce(ee.Reducer.percentile(
        percentiles=list(range(0,110,10)),
        outputNames=[f'VEGETATION_POLYGONS_p{pc}' for pc in range(0,110,10)]
    ))

    # Initialisation du dictionnaire des résultats
    results = ee.Dictionary(veget_percentiles).combine(ee.Dictionary({
        # Calculer le nombre de polygones
        'VEGETATION_POLYGONS': vector_vegetation.size(),

        # Calculer l'aire des surfaces végétation
        'VEGETATION_AREA': image.select('VEGETATION').reduceRegion(
            reducer = ee.Reducer.sum(),
            geometry = vector_vegetation,
            scale = scale
        ).getNumber('VEGETATION'),
        
        # Calucler les périmètres
        'VEGETATION_PERIMETER': geom_vegetation.perimeter(scale),
        
        # Calcul du ndvi moyen des surfaces végétation
        'MEAN_VEGETATION_NDVI': image.select('NDVI').reduceRegion(
            reducer = ee.Reducer.mean(),
            geometry = vector_vegetation,
            scale = scale
            ).getNumber('NDVI'),
        
        # Calcul du NDWI moyen des surfaces végétation
        'MEAN_VEGETATION_NDWI': image.select('NDWI').reduceRegion(
            reducer = ee.Reducer.mean(),
            geometry = vector_vegetation,
            scale = scale
            ).getNumber('NDWI'),
        
        # Calcul du ndvi moyen de tout le DGO
        'MEAN_NDVI': image.select('NDVI').reduceRegion(
            reducer = ee.Reducer.mean(),
            geometry = dgo.geometry(),
            scale = scale
            ).getNumber('NDVI'),
    }))
        
    return results


def calculateACMetrics(image, dgo, scale):
    # Vectorisation des surfaces
    vectors = image.select('AC').reduceToVectors(
        geometry = dgo.geometry(),
        scale = scale,
        eightConnected = True,
        maxPixels = 1e16,
        geometryType = 'polygon')
    
    # Séparer les surfaces végétation du reste
    vector_ac = vectors.filter("label == 1")
    
    # Initialisation du dictionnaire des résultats
    results = ee.Dictionary({
        # Calculer l'aire des surfaces végétation
        'AC_AREA': image.select('AC').reduceRegion(
            reducer = ee.Reducer.sum(),
            geometry = vector_ac,
            scale = scale
        ).getNumber('AC'),
        
        # Calcul du ndvi moyen des surfaces végétation
        'MEAN_AC_NDVI': image.select('NDVI').reduceRegion(
            reducer = ee.Reducer.mean(),
            geometry = vector_ac,
            scale = scale
            ).getNumber('NDVI'),
        
        # Calcul du NDWI moyen des surfaces végétation
        'MEAN_AC_NDWI': image.select('NDWI').reduceRegion(
            reducer = ee.Reducer.mean(),
            geometry = vector_ac,
            scale = scale
            ).getNumber('NDWI'),
    })

    return results


def dgoMetrics(collection, scale):
    def mapDGO(dgo):
        # Filtrer la collection d'images sur l'emprise du DGO traité
        dgo_images_collection = collection.filterBounds(dgo.geometry())

        # Définir une fonction qui ajoute les métriques d'une image à la liste des métriques du DGO
        def addMetrics(image, metrics_list, scale):
            # Récupérer la Feature du DGO qui est stocké dans le premier élément de la liste
            dgo = ee.Feature(ee.List(metrics_list).get(0))
            
            # Calculer les métriques
            clear_score = calculateClearScore(image, dgo, scale)
            coverage_score = calculateCoverage(image, dgo, scale)
            water_metrics = calculateWaterMetrics(image, dgo, scale)
            vegetation_metrics = calculateVegetationMetrics(image, dgo, scale)
            ac_metrics = calculateACMetrics(image, dgo, scale)
            
            # Créer un dictionnaire avec toutes les métriques
            image_metrics = dgo.set(ee.Dictionary({
                                     'DATE': ee.Date(image.get('acquired')).format("YYYY-MM-dd"),
                                     'CLEAR_SCORE': clear_score, 
                                     'COVERAGE_SCORE': coverage_score,
                                    }).combine(water_metrics).combine(vegetation_metrics).combine(ac_metrics))
            
            # Always add the image metrics to the list, ignoring the clear score filter.
            output_list = ee.List(metrics_list).add(image_metrics)
            # Ajouter ce dictionnaire à la liste des métriques
            return output_list

        # Stocker le DGO traité dans le premier élément de la liste
        first = ee.List([dgo])

        # Ajouter les métriques calculées sur chaque image à la liste
        # Using a lambda function to pass the scale parameter
        metrics = dgo_images_collection.iterate(lambda image, list: addMetrics(ee.Image(image), list, scale), first)

        # Supprimer le DGO traité de la liste pour alléger le résultat
        metrics = ee.List(metrics).remove(dgo)

        # Renvoyer la Feature en ajoutant l'attribut metrics
        return dgo.set({'metrics': metrics})
    return mapDGO


def calculateDGOsMetrics(collection, dgos, scale):
    # Ajouter les listes de métriques aux attributs des DGOs
    # Use a lambda function to pass the scale argument to mapDGO
    metrics = dgos.map(lambda dgo: dgoMetrics(collection, scale)(dgo))

    # Dé-empiler les métriques stockées dans un attribut de la FeatureCollection
    unnested = ee.FeatureCollection(metrics.aggregate_array('metrics').flatten())

    # Retourner uniquement les métriques (pas la Feature complète)
    return unnested

