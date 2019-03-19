#!/usr/bin/env python3
"""
collect images for listed plants
"""

import os
import sys
import json
import argparse

import pymongo
import requests

def main(argv):
    """ main function """
    parser = argparse.ArgumentParser(
        description="collect images for listed plants",
    )
    args = parser.parse_args(argv)

    certs = {}
    with open(os.path.join(os.path.dirname(__file__), ".certs")) as fobj:
        certs = json.load(fobj)

    client = pymongo.MongoClient()
    for plant in client.plantdb.plants.find({}):
        if plant.get('image', None):
            continue

        def query_name(name):
            req = requests.get(
                "https://pixabay.com/api/",
                params={
                    "key": certs['pixabay_key'],
                    "q": name,
                    "image_type": "photo",
                    "per_page": 20,
                    "safesearch": "true",
                    "order": "popular",
                },
            )
            if req.status_code != 200:
                print("Failed querying", name, ":", req.text, file=sys.stderr)

            try:
                vals = req.json()

            except Exception:
                print("Invalid response for", name, file=sys.stderr)
                return None

            assert 'hits' in vals

            if not len(vals['hits']):
                print("No image found for %s" % name, file=sys.stderr)
                return None

            assert 'largeImageURL' in vals['hits'][0]
            return vals['hits'][0]['largeImageURL']

        image_url = query_name(plant['latin'])
        if image_url is None:
            if ' or ' in plant['name']:
                poss_names = plant['name'].split(' or ')
                for name in poss_names:
                    image_url = query_name(name)
                    if image_url is not None:
                        break

                else:
                    print("Gave up looking for %s" % plant['name'], file=sys.stderr)
                    continue

            else:
                image_url = query_name(plant['name'])
                if image_url is None:
                    print("Gave up looking for %s" % plant['name'], file=sys.stderr)
                    continue

        print("%s - %s" % (plant['name'], image_url))
        client.plantdb.plants.update_one(
            {
                "_id": plant['_id'],

            },
            {
                "$set": {"image": image_url},

            },

        )

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

