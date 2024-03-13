import ee

######
## Indicators

def calculateMNDWI(image):
    # Calculer l'image de MNDWI
    output_img = image.normalizedDifference(['green','swir1']).rename('MNDWI')
    
    return image.addBands(output_img)


def calculateNDVI(image):
    # Calculer l'image de MNDWI
    output_img = image.normalizedDifference(['nir','red']).rename('NDVI')
    
    return image.addBands(output_img)


def calculateNDWI(image):
    # Calculer l'image de MNDWI
    output_img = image.normalizedDifference(['green','nir']).rename('NDWI')
    
    return image.addBands(output_img)


def calculateIndicators(collection):
    '''
    Documentation
    '''
    
    collection = collection.map(calculateMNDWI).map(calculateNDVI).map(calculateNDWI)
    
    return collection


######
## Thresholds to classify objects

def extractWater(image, satellite_type):
    
    # Seuillage du raster
    if satellite_type == 'Landsat':
        output_img = image.expression('MNDWI >  0.0', {'MNDWI': image.select('MNDWI')}).rename('WATER')

    elif satellite_type == 'Sentinel-2':
        output_img = image.expression('NDWI >  -0.1', {'NDWI': image.select('NDWI')}).rename('WATER')

    
    # Filtre modal pour retirer les pixels isolés
    output_img = output_img.focalMode(3)

    # ## Meilleure option : tamisage. Je ne suis pas certain que ça fonctionne a 100% pour le moment.
    # # Labellisation
    # object_id = output_img.connectedComponents(ee.Kernel.square(1), maxSize=128)

    # # Mesurer la taille des patch en pixels : résultat dépendant de l'échelle ?
    # object_size = object_id.select('labels').connectedPixelCount(maxSize=128, eightConnected=True)

    # # Convertir les taille en surfaces m2
    # pixel_area = ee.Image.pixelArea()
    # object_area = object_size.multiply(pixel_area)
    
    # # Mettre à jour l'image en sortie
    # output_img = output_img.where(object_area.lt(1800), ee.Number(0))
    
    # Masquer ce qui n'est pas classé
    output_img = output_img.selfMask()
    
    return image.addBands(output_img)


def extractVegetation(image):
    # Seuillage du raster
    output_img = image.expression('NDVI > 0.15', {'NDVI': image.select('NDVI')}).rename('VEGETATION')
    
    # Filtre modal pour retirer les pixels isolés
    output_img = output_img.focalMode(3)
    
    # Masquer ce qui n'est pas classé
    mask = (output_img.eq(1))
    output_img = output_img.updateMask(mask)
    
    return image.addBands(output_img)


def extractActiveChannel(image, satellite_type):

    # Seuillage du raster
    if satellite_type == 'Landsat':
        output_img = image.expression('MNDWI > -0.4 && NDVI < 0.2', 
                                                         {'MNDWI': image.select('MNDWI'),
                                                          'NDVI': image.select('NDVI')}
                                                         ).rename('AC')
    elif satellite_type == 'Sentinel-2':
        output_img = image.expression('NDWI > -0.4 && NDVI < 0.2', 
                                                         {'NDWI': image.select('NDWI'),
                                                          'NDVI': image.select('NDVI')}
                                                         ).rename('AC')
    
    # Filtre modal pour retirer les pixels isolés
    output_img = output_img.focalMode(3)
    
    # Masquer ce qui n'est pas classé
    mask = (output_img.eq(1))
    output_img = output_img.updateMask(mask)
    
    return image.addBands(output_img)


def classifyObjects(collection, satellite_type):

    def extractWaterWrapper(image):
        return extractWater(image, satellite_type)
    
    def extractActiveChannelWrapper(image):
        return extractActiveChannel(image, satellite_type)

        
    collection = (collection
                  .map(extractWaterWrapper)
                  .map(extractVegetation)
                  .map(extractActiveChannelWrapper))


    return collection
