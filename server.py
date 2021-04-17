import falcon
from wsgiref.simple_server import make_server
from pandas_datapackage_reader import read_datapackage

data = read_datapackage(".")

def get_paginated_json(req, df):
    per_page = req.get_param_as_int('per_page', default=10, required=False)
    at_page = req.get_param_as_int('page', default=1, required=False)
    page = (at_page-1)*per_page
    return df[page:page+per_page].to_json(orient='records')

class ProductionsResource:

    def __init__(self, data):
        self.productions = data

    def on_get(self, req, resp):
        df = self.productions.copy()
        for fld in self.productions._metadata['schema']['fields']:
            fn = fld['name']
            q = req.get_param(fn, None)
            if q is not None:
                try:
                    q = q.strip()
                    q = int(q)
                    df = df.loc[df[fn] == q]
                except:
                    pass

        resp.status = falcon.HTTP_200
        resp.body = get_paginated_json(req, df)

print("Deploying falcon brigade")

app = falcon.API(middleware=falcon.CORSMiddleware(allow_origins='*', allow_credentials='*'))

app.add_route('/productions', ProductionsResource(data))

if __name__ == '__main__':
    with make_server('', 8000, app) as httpd:
        print('Serving on port 8000...')
        httpd.serve_forever()
