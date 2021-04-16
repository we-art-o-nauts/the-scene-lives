This is an open dataset of [demoscene](https://en.wikipedia.org/wiki/Demoscene) productions, which could be filtered to individual countries, themes, or platforms, which could be of interest from an art-history perspective to complement our [UNESCO digital heritage](http://demoscene-the-art-of-coding.net/) application - or just be used to introduce people to the history of the 'scene.

The format of this repository is a [Data Package](https://frictionlessdata.io/data-packages/) aimed at making the demoscene more accessible to people who may have never heard about it (:wave: hello [#GLAMhack](https://glam.opendata.ch)!)

:construction: Under construction :construction:

See https://hack.glam.opendata.ch/project/114

# Data

> *Instructions: Accessible data files (ideally in simple data formats such as [CSV](https://frictionlessdata.io/guides/csv/), [JSON](http://json-schema.org/specification.html) and [GeoJSON](http://geojson.org/)), as well as the raw data, are placed in the `data` folder. In this section you should mention the files and formats included. It is good to suggest purposes for this data, such as example applications or use cases. Include any relevant background, contact points, and links that may help people to use this data. You can find examples of this at [datahub.io](https://datahub.io) or [github.com/datasets](https://github.com/datasets), and further tips at [frictionlessdata.io](https://frictionlessdata.io/guides/data-package/) and [datahub.io](https://datahub.io/docs/data-packages/publish-faq)*.

An initial excerpt made out of Demozoo data has been added to the `data` folder. We are working on merging this with Pouët, and investigating also other scene data sources. Please see the notes in our scratch pad or our discussion on Slack for details.

# Preparation

> *Instructions: describe here where you obtained the data, how it was created, where and how it was extracted, and any transformation steps that took place during publication. Link to the sources, as well as to any tools that were used. If you used any scripts to extract and convert the data, add them to a `script` folder in your repository.*

The data in this repository was produced by importing the latest demozoo.org archival dump into a local PostgreSQL database, like this:

```
docker run --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=sceners -e POSTGRES_USER=admin -e POSTGRES_DB=demozoo -d postgres:alpine
gunzip -c demozoo-export.sql.gz | psql -h localhost -p 5432 -U admin demozoo
# Enter the password when prompted: sceners
```

There are lots of utilities for converting Postgres tables to CSV. I used [db-to-sqlite](https://github.com/simonw/db-to-sqlite) to first create a SQLite database, poke around the data model, and export the tables.

Then we used the Frictionless Data [create tool](https://create.frictionlessdata.io/) to generate the `datapackage.json`. Geting it to validate and preview still needs more work. For now, we're focusing on a simple service to compose time series and other queries.

## Service

This repository contains a minimalist backend service API based on the [Falcon](http://falconframework.org/) framework and [Pandas DataPackage Reader](https://github.com/rgieseke/pandas-datapackage-reader). To run:

```
virtualenv env                   # .. or use pipenv
. env/bin/activate               # == pipenv shell
pip install -Ur requirements.txt # == pipenv install
python server.py
```

At this point you should see the message "Serving on port..." Test the API using a REST client such as [RESTer](https://github.com/frigus02/RESTer) with queries such as:

`http://localhost:8000/productions`

You can provide a search string, or adjust the amount of output with a `page` and `per_page` parameter in your query.


# License

This Data Package is made available by its maintainers under the [Public Domain Dedication and License v1.0](http://www.opendatacommons.org/licenses/pddl/1.0/), a copy of the full text of which is in [LICENSE.md](LICENSE.md).
