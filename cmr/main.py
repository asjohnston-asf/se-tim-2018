from xml.etree import ElementTree
from urllib.parse import urljoin, urlparse
from os.path import basename
from threading import Thread
import requests


source_host = 'https://cmr.earthdata.nasa.gov'
source_url = '/search/granules'
source_collection_concept_id = 'C1206500991-ASF'

granule_ur_suffix = '-se-tim'
new_product_url = 'http://se-tim-distribution-1848230930.us-east-1.elb.amazonaws.com/distribution/'
new_browse_url = 'https://se-tim-public.s3.amazonaws.com/'

target_cmr_url = 'https://cmr.uat.earthdata.nasa.gov/ingest/providers/ASF/granules/'
echo_token = ''
target_dataset_id = 'SEASAT_SAR_LEVEL1_HDF5_SE_TIM'

num_threads = 8


def split_list(my_list, num_chunks):
    chunk_size = int(len(my_list)/num_chunks) + 1
    for i in range(0, len(my_list), chunk_size):
        yield my_list[i:i + chunk_size]


def parse_granules(echo10_response):
    xml_element_tree = ElementTree.fromstring(echo10_response)
    granules = [granule for granule in xml_element_tree.findall('result/Granule')]
    return granules


def get_granules():
    search_url = urljoin(source_host, source_url)
    parameters = {
        'collection_concept_id': source_collection_concept_id,
        'scroll': 'true',
        'page_size': 2000,
    }
    headers = {
        'Accept': 'application/echo10+xml',
    }

    response = requests.get(search_url, params=parameters, headers=headers)
    response.raise_for_status()
    granules = parse_granules(response.text)

    total_hits = int(response.headers['CMR-Hits'])
    headers['CMR-Scroll-Id'] = response.headers['CMR-Scroll-Id']

    while len(granules) < total_hits:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        granules += parse_granules(response.text)

    return granules


def update_granules(granules):
    for granule in granules:
        granule.find('GranuleUR').text += granule_ur_suffix
        granule.find('Collection/DataSetId').text = target_dataset_id

        browse_url = granule.find('AssociatedBrowseImageUrls/ProviderBrowseUrl/URL')
        browse_file = basename(urlparse(browse_url.text).path)
        browse_url.text = urljoin(new_browse_url, browse_file)

        product_url = granule.find('OnlineAccessURLs/OnlineAccessURL/URL')
        product_file = basename(urlparse(product_url.text).path)
        product_url.text = urljoin(new_product_url, product_file)


def submit_granules(granules):
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


if __name__ == '__main__':
    print('Fetching granule metadata for collection {0} from {1}'.format(source_collection_concept_id, source_host))
    granules = get_granules()
    print('{0} granules fetched'.format(len(granules)))
    print('Updating granule metadata')
    update_granules(granules)
    print('Ingesting updated granules into {0}'.format(target_cmr_url))
    for granule_list in split_list(granules, num_threads):
        t = Thread(target=submit_granules, args=(granule_list,))
        t.start()
