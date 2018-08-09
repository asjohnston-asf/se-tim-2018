from xml.etree import ElementTree
from urllib.parse import urljoin
import requests


source_host = 'https://cmr.earthdata.nasa.gov'
source_url = '/search/granules'
source_collection_concept_id = ''
granule_ur_suffix = ''
old_product_url = ''
new_product_url = ''
old_browse_url = ''
new_browse_url = ''

target_cmr_url = 'https://cmr.uat.earthdata.nasa.gov/ingest/providers/ASF/granules/'
echo_token = ''
target_dataset_id = ''

parameters = {
  'collection_concept_id': source_collection_concept_id,
  'scroll': 'true',
  'page_size': 2000,
}

headers = {
  'Accept': 'application/echo10+xml',
}

def parse_granules(echo10_response):
    granules = []
    xml_element_tree = ElementTree.fromstring(echo10_response)
    for result in xml_element_tree.findall('result'):
        granules.append(result.find('Granule'))
    return granules
    

granules = []

search_url = urljoin(source_host, source_url)
response = requests.get(search_url, params=parameters, headers=headers)
response.raise_for_status()
granules += parse_granules(response.text)

total_hits = int(response.headers['CMR-Hits'])
headers['CMR-Scroll-Id'] = response.headers['CMR-Scroll-Id']

while len(granules) < total_hits:
    response = requests.get(search_url, headers=headers)
    response.raise_for_status()
    granules += parse_granules(response.text)

for granule in granules:
    granule.find('GranuleUR').text += granule_ur_suffix
    granule.find('Collection/DataSetId').text = target_dataset_id
    browse_url = granule.find('AssociatedBrowseImageUrls/ProviderBrowseUrl/URL')
    browse_url.text = browse_url.text.replace(old_browse_url, new_browse_url)
    product_url = granule.find('OnlineAccessURLs/OnlineAccessURL/URL')
    product_url.text = product_url.text.replace(old_product_url, new_product_url)

session = requests.Session()
headers = {
    'Content-Type': 'application/echo10+xml',
    'Echo-Token': echo_token,
}
session.headers.update(headers)

for granule in granules:
    granule_ur = granule.find('GranuleUR').text
    url = urljoin(target_cmr_url, granule_ur)
    response = session.put(url, data=ElementTree.tostring(granule))
    response.raise_for_status()
    print(response.text)
