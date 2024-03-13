import ee

######
## Indicators

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
    
    collection = collection.map(calculateNDVI).map(calculateNDWI)
    
    return collection


######
## Thresholds to classify objects

def extractWater(image):
    # Seuillage du raster
    output_img = image.expression('NDWI > -0.25', {'NDWI': image.select('NDWI')}).rename('WATER')
    
    # Filtre modal pour retirer les pixels isolés
    output_img = output_img.focalMode(3)
    
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


def extractActiveChannel(image):
    # Seuillage du raster
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


def classifyObjects(collection):
    
    collection = collection.map(extractWater).map(extractVegetation).map(extractActiveChannel)

    return collection
