# glourbee_planet
Download Planet Labs satellite imagery into a Google Earth Engine (GEE) ImageCollection and extract GloUrb metrics and indicators from these images (or other PlanetScope imagery saved as a GEE-asset)


## description
- planet_gee_delivery.ipynb assists to request images for a given AOI and period and order and deliver them into a GEE-ImageCollection asset
- glourbee_planet_workflow.ipynb runs the GloUrbEE-workflow for PlanetScope-imagery to extract metrics such as the Water, vegetation, and acitve channel area for specific dates
- example_aois.txt contains the geojson-code for some examples of braided river reaches in the french alps
