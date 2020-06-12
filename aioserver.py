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
from logger import logger
from pyjugex_handler.pyjugex_analysis import app as pyjugex_analysis_app

logger.log('info', {"message": "pyjugex webwrapper - aiohttp server starting"})
app = web.Application()
app.add_subapp('/pyjugex', pyjugex_analysis_app)

if __name__=='__main__':
    PORT = os.getenv('PORT') or 1234
    web.run_app(app,host="0.0.0.0",port=PORT)
