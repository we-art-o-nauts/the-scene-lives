from dataflows import Flow, load, dump_to_path, dump_to_zip, printer, add_metadata
from dataflows import sort_rows, filter_rows, find_replace, delete_fields, set_type, validate, unpivot, join

import json

with open('data/demozoo/platform.json', 'r') as jsonfile:
    jsondata = json.load(jsonfile)
    platform_name = {}
    for pt in jsondata:
        platform_name[pt['pk']] = pt['fields']['name']
with open('data/demozoo/production_type.json', 'r') as jsonfile:
    jsondata = json.load(jsonfile)
    production_type = {}
    for pt in jsondata:
        production_type[pt['pk']] = {
            'name': pt['fields']['name'], 'top': None
        }
    # Aggregate the top types
    for pt in jsondata:
        pid = pt['fields']['path'][0:4]
        for pp in jsondata:
            if pp['fields']['path'] == pid:
                parentid = pp['pk']
                if pid != parentid:
                    parent = production_type[parentid]['name']
                    production_type[pt['pk']]['top'] = parent


def aggregate_productions(package):
    # Add new type field to the schema
    package.pkg.descriptor["resources"][0]["schema"]["fields"].append(
        dict(name="production_type", type="string")
    )
    package.pkg.descriptor["resources"][0]["schema"]["fields"].append(
        dict(name="production_subtype", type="string")
    )
    package.pkg.descriptor["resources"][0]["schema"]["fields"].append(
        dict(name="platform", type="string")
    )
    # Must yield the modified datapackage
    yield package.pkg

    # Now iterate on all resources
    resources = iter(package)
    productions = next(resources)

    def f(row):
        row["production_type"] = ""
        if 'productiontype_id' in row and row['productiontype_id']:
            ptid = int(row['productiontype_id'])
            ptype = production_type[ptid]
            row["production_type"] = ptype['top'] or ptype['name']
            row["production_subtype"] = ptype['name'] or ""
        row["platform"] = ""
        if 'platform_id' in row and row['platform_id']:
            row["platform"] = platform_name[int(row['platform_id'])]
        return row

    yield map(f, productions)


def productions_csv():
    flow = Flow(
        # Load source data
        load('data/demozoo/productions_production_types.csv', format='csv',
            name='productiontypes'),
        load('data/demozoo/productions_production_platforms.csv', format='csv',
            name='productionplatforms'),
        load('data/demozoo/productions_production.100.csv', format='csv',
            name='production'),

        # Save a checkpoint to avoid re-downloading
        # checkpoint("productions-types"),

        join(
            "productiontypes",  # Source resource
            ["production_id"],
            "production",       # Target resource
            ["id"],
            {'productiontype_id': { 'aggregate': 'first' }},
            mode="half-outer",  # "null" values at the Source
        ),
        join(
            "productionplatforms",  # Source resource
            ["production_id"],
            "production",       # Target resource
            ["id"],
            {'platform_id': { 'aggregate': 'first' }},
            mode="half-outer",  # "null" values at the Source
        ),

        # Process to aggregate
        aggregate_productions,

        load('data/demozoo/productions_screenshot.csv', format='csv',
            name='screenshot'),

        join(
            "production",       # Target resource
            ["id"],
            "screenshot",       # Source resource
            ["id"],
            {'*': { 'aggregate': 'first' }},
            mode="half-outer",  # "null" values at the Source
        ),

        # Save the results
        add_metadata(name='productions', title='''Productions'''),
        # printer(),
        dump_to_path('data/output'),
    )
    flow.process()


if __name__ == '__main__':
    productions_csv()
