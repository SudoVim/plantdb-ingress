#!/usr/bin/env python3
"""
collect shaded plants from Central Texas Gardener site
"""

import sys
import pprint
import argparse

import pymongo
import requests
import bs4 as bs

SHADED_PLANTS_URL = "https://www.centraltexasgardener.org/resource/made-for-the-shade-well-adapted-plants-for-shady-areas/"

def main(argv):
    """ main function """
    parser = argparse.ArgumentParser(
        description="collect shaded plants from Central Texas Gardener site",
    )
    args = parser.parse_args(argv)

    rsp = requests.get(SHADED_PLANTS_URL)
    soup = bs.BeautifulSoup(rsp.text, "lxml")
    article = soup.find('article')

    categories = article.find_all('p')[2:7]
    plant_lists = article.find_all('ul')[:5]

    structure = {'categories': [], 'plants': []}
    for category, plant_list in zip(categories, plant_lists):
        category_name = category.find('b').text.lower()
        structure['categories'].append(category_name)

        for plant_item in plant_list.find_all('li'):
            plant_name = plant_item.find('b').text.lower()

            try:
                plant_latin_name = plant_item.find('i').text.lower()

            # Not latin name found
            except AttributeError:
                plant_latin_name = None

            try:
                plant_description = plant_item.text.split(chr(8212), 1)[1].strip().replace('\n', ' ')

            except IndexError:
                plant_description = plant_item.text.split(chr(8211), 1)[1].strip().replace('\n', ' ')
            structure['plants'].append(
                {
                    'name': plant_name,
                    'latin': plant_latin_name,
                    'category': category_name,
                    'description': plant_description,
                    'tags': [
                        'central_texas',
                        'shade',

                    ],

                },

            )

    print("Structure:")
    pprint.pprint(structure)

    client = pymongo.MongoClient()
    result = client.plantsdb.categories.bulk_write(
        [
            pymongo.UpdateOne(
                {'name': c},
                {'$setOnInsert': {'name': c}},
                upsert=True,

            ) for c in structure['categories']

        ]

    )

    print()
    print("Category update result:")
    pprint.pprint(result.bulk_api_result)

    result = client.plantsdb.plants.bulk_write(
        [
            pymongo.UpdateOne(
                {'name': p['name']},
                {'$set': p},
                upsert=True,

            ) for p in structure['plants']

        ]

    )

    print()
    print("Plants update result:")
    pprint.pprint(result.bulk_api_result)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

