#!/usr/bin/env python

from dataflows import (
    Flow, load, dump_to_path, dump_to_zip, printer,
    update_resource, add_metadata,
    sort_rows, filter_rows, find_replace, delete_fields,
    select_fields, set_type, validate, unpivot, join
)

import json, os

FASTMODE = '.100' if os.getenv('FASTMODE', False) else ''
print("Speedy Susie mode!" if FASTMODE else 'Full process mode.')

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
    # Add custom type fields to the schema
    package.pkg.descriptor["resources"][0]["schema"]["fields"].append(
        dict(name="uri", type="string", format="uri")
    )
    package.pkg.descriptor["resources"][0]["schema"]["fields"].append(
        dict(name="production_type", type="string")
    )
    package.pkg.descriptor["resources"][0]["schema"]["fields"].append(
        dict(name="production_subtype", type="string")
    )
    package.pkg.descriptor["resources"][0]["schema"]["fields"].append(
        dict(name="platform_name", type="string")
    )
    # Must yield the modified datapackage
    yield package.pkg

    # Now iterate on all resources
    resources = iter(package)
    productions = next(resources)

    def f(row):
        id = int(row['id'])
        row["uri"] = ""
        row["platform_name"] = ""
        row["production_type"] = ""
        if 'productiontype_id' in row and row['productiontype_id']:
            ptid = int(row['productiontype_id'])
            if ptid in production_type:
                ptype = production_type[ptid]
                row["production_type"] = ptype['top'] or ptype['name']
                row["production_subtype"] = ptype['name'] or ""
            else:
                # print("Warning: production type missing on %d - data out of sync?" % id)
                pass
        if 'platform_id' in row and row['platform_id']:
            pfid = int(row['platform_id'])
            if pfid in platform_name:
                row["platform_name"] = platform_name[pfid]
            else:
                # print("Warning: platform type %s not found on %d" % (str(pfid), id))
                pass
        if 'supertype' in row and row['supertype']:
            supertype = row['supertype']
            if supertype == 'production': supertype += 's' # :_) ...
            row["uri"] = "https://demozoo.org/%s/%d/" % (supertype, id)
        return row

    yield map(f, productions)


def productions_csv():
    flow = Flow(
        # Load source data
        load('data/demozoo/productions_production_types.csv', format='csv',
            name='productiontypes'),
        load('data/demozoo/productions_production_platforms.csv', format='csv',
            name='productionplatforms'),
        load('data/demozoo/productions_screenshot%s.csv' % FASTMODE, format='csv',
            name='screenshot'),
        load('data/demozoo/productions_production%s.csv' % FASTMODE, format='csv',
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
        join(
            "screenshot",       # Source resource
            ["production_id"],
            "production",       # Target resource
            ["id"],
            {
                'standard_url': { 'aggregate': 'first' },
                'thumbnail_url': { 'aggregate': 'first' }
            },
            mode="half-outer",  # "null" values at the Source
        ),

        # Process to aggregate
        aggregate_productions,

        # Clear unused fields
        select_fields([
            'id', 'title', 'notes',
            'release_date_date', 'release_date_precision',
            'created_at', 'updated_at',
            'supertype', 'data_source',
            'scene_org_id',
            'thumbnail_url', 'standard_url',
            'production_type', 'production_subtype',
            'platform_name',
            'uri'
        ]),

        # Save the results
        update_resource('productions', name='production'),
        add_metadata(name='productions', title='''Productions'''),
        # printer(),
        dump_to_path('data'),
    )
    flow.process()


if __name__ == '__main__':
    productions_csv()
