from planet import Session, DataClient, OrdersClient
import json
import requests

# request all images matching the filter
def request_itemids(satellite_product: "PSScene", img_filter, planet_session, planet_baseURL):
    
    # Setup the quick search endpoint url
    search_url = "{}/quick-search".format(planet_baseURL)

    # Construct the request.
    request = {
        "item_types" : [satellite_product],
        "filter" : img_filter
    }

    # Send the POST request to the API quick search endpoint
    res = planet_session.post(search_url, json=request)
    geojson = res.json()

    # Initialize the item_ids list to collect all item ids
    item_ids = []

    # Collect item IDs from current page
    features = geojson["features"]
    current_page_item_ids = [f['id'] for f in features]
    item_ids.extend(current_page_item_ids)

    # loop to paginate through all available pages to extract >250 items
    while current_page_item_ids:

        # Check if there's a next page, if not, break the loop
        next_url = geojson["_links"]["_next"] 
    
        # Update the request URL for the next iteration
        res_next = planet_session.get(next_url)
        geojson = res_next.json()
    
        # Collect item IDs from next page
        features_next = geojson["features"]
        current_page_item_ids = [f['id'] for f in features_next]
        item_ids.extend(current_page_item_ids)

    return item_ids