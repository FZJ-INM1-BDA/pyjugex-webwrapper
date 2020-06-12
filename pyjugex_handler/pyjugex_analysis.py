# Copyright 2020 Forschungszentrum Jülich
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from aiohttp import web
import pyjugex
import requests
import json

from .util import get_filename_from_resp, get_pmap, read_byte_via_nib, is_gzipped
from .constants import default_param
from logger import logger

routes = web.RouteTableDef()
app = web.Application()

gene_cache_dir = os.getenv('GENE_CACHE_DIR') or '.pyjugex'

current_dir = os.path.dirname(os.path.abspath(__file__))
gene_symbol_path = os.getenv('GENE_SYMBOL_PATH') or os.path.join(current_dir, 'files/genesymbols.json')
with open(gene_symbol_path, "r") as f:
    gene_symbols = f.read()

routes = web.RouteTableDef()

def get_roi_img_array(obj):
    pmap_resp = get_pmap(obj['PMapURL'], obj.get('body', None))
    filename = get_filename_from_resp(pmap_resp)
    return read_byte_via_nib(pmap_resp.content, gzip=is_gzipped(filename))

def run_pyjugex_analysis(jsonobj):
    roi1 = {}
    roi2 = {}

    roi1_obj = jsonobj['area1']
    roi1['data'] = get_roi_img_array(roi1_obj)
    roi1['name'] = jsonobj['area1']['name']

    roi2_obj = jsonobj['area2']
    roi2['data'] = get_roi_img_array(roi2_obj)
    roi2['name'] = jsonobj['area2']['name']

    single_probe_mode = jsonobj.get('mode', default_param['mode'])
    filter_threshold = jsonobj.get('threshold', default_param['threshold'])
    n_rep = jsonobj.get('nPermutations', default_param['nPermutations'])

    jugex = pyjugex.PyjugexAnalysis(
        filter_threshold=float(filter_threshold),
        single_probe_mode = single_probe_mode,
        verbose=True,
        n_rep=n_rep,
        gene_list=jsonobj['selectedGenes'],
        roi1=roi1['data'],
        roi2=roi2['data']
    )

    jugex.differential_analysis()
    
    coord=jugex.get_filtered_coord() 
    anova_result=jugex.anova.result
    return [
        coord,
        anova_result ]

@routes.get('/gene_symbols')
async def get_gene_symbols(request):
    if gene_symbols is None:
        return web.Response(status=404)
    else:
        return web.Response(status=200, content_type='application/json', body=gene_symbols)

@routes.post('/analysis')
async def start_analysis(request):
    logger.log('[info]', 'POST /analysis called')
    if request.can_read_body:
        jsonobj = await request.json()
    else:
        return web.Response(status=400)
    if "cbUrl" in jsonobj:
        web.Response(status=200)
        try:
            data = run_pyjugex_analysis(jsonobj)
            requests.post(jsonobj["cbUrl"], json=data)
        except Exception as e:
            error = {
                "error": str(e),
                "detail": {
                    "jsonobj": jsonobj
                }
            }
            logger.log('error', error)
            requests.post(jsonobj["cbUrl"], json=error)
    else:
        try:
            data = run_pyjugex_analysis(jsonobj)
            return web.Response(status=200, content_type="application/json", body=data)
        except Exception as e:
            logger.log('error', {"error":str(e)})
            return web.Response(status=400,body=str(e))

app.router.add_routes(routes)

if __name__ == '__main__':
    PORT = os.getenv('PORT') or 1234
    web.run_app(app, port=PORT)