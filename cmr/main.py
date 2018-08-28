from xml.etree import ElementTree
from urllib.parse import urljoin, urlparse
from os.path import basename
from threading import Thread
from argparse import ArgumentParser
import requests


def get_args():
    cmr_hosts = ['cmr.earthdata.nasa.gov', 'cmr.uat.earthdata.nasa.gov', 'cmr.sit.earthdata.nasa.gov']
    parser = ArgumentParser()
    parser.add_argument('--source_host', default='cmr.earthdata.nasa.gov', choices=cmr_hosts)
    parser.add_argument('--source_collection_concept_id', required=True)
    parser.add_argument('--target_host', default='cmr.uat.earthdata.nasa.gov', choices=cmr_hosts)
    parser.add_argument('--provider', required=True)
    parser.add_argument('--echo_token', required=True)
    parser.add_argument('--new_granule_ur_suffix', default='')
    parser.add_argument('--new_dataset_id', required=True)
    parser.add_argument('--new_product_url', required=True)
    parser.add_argument('--new_browse_url', required=True)
    parser.add_argument('--num_threads', type=int, default=8)
    args = parser.parse_args()
    return args


def split_list(my_list, num_chunks):
    chunk_size = int(len(my_list)/num_chunks) + 1
    for i in range(0, len(my_list), chunk_size):
        yield my_list[i:i + chunk_size]


def parse_granules(echo10_response):
    xml_element_tree = ElementTree.fromstring(echo10_response)
    granules = [granule for granule in xml_element_tree.findall('result/Granule')]
    return granules


def get_granules(cmr_host, collection_concept_id):
    print('Fetching granule metadata for collection {0} from {1}'.format(collection_concept_id, cmr_host))
    search_url = 'https://{0}/search/granules'.format(cmr_host)
    parameters = {
        'collection_concept_id': collection_concept_id,
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

    print('{0} granules fetched'.format(len(granules)))
    return granules


def update_granules(granules, new_granule_ur_suffix, new_dataset_id, new_browse_url, new_product_url):
    print('Updating granule metadata')
    for granule in granules:
        granule.find('GranuleUR').text += new_granule_ur_suffix
        granule.find('Collection/DataSetId').text = new_dataset_id

        browse_url = granule.find('AssociatedBrowseImageUrls/ProviderBrowseUrl/URL')
        browse_file = basename(urlparse(browse_url.text).path)
        browse_url.text = urljoin(new_browse_url, browse_file)

        product_url = granule.find('OnlineAccessURLs/OnlineAccessURL/URL')
        product_file = basename(urlparse(product_url.text).path)
        product_url.text = urljoin(new_product_url, product_file)


def submit_granules(granules, cmr_host, provider, echo_token):
    ingest_url = 'https://{0}/ingest/providers/{1}/granules/'.format(cmr_host, provider)
    session = requests.Session()
    headers = {
        'Content-Type': 'application/echo10+xml',
        'Echo-Token': echo_token,
    }
    session.headers.update(headers)

    for granule in granules:
        granule_ur = granule.find('GranuleUR').text
        url = urljoin(ingest_url, granule_ur)
        response = session.put(url, data=ElementTree.tostring(granule))
        response.raise_for_status()


if __name__ == '__main__':
    args = get_args()
    granules = get_granules(args.source_host, args.source_collection_concept_id)
    update_granules(granules, args.new_granule_ur_suffix, args.new_dataset_id, args.new_browse_url, args.new_product_url)

    print('Ingesting updated granules into {0}'.format(args.target_host))
    for granule_list in split_list(granules, args.num_threads):
        t = Thread(target=submit_granules, args=(granule_list, args.target_host, args.provider, args.echo_token))
        t.start()
