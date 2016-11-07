# -*- coding: utf-8 -*-
#
# Copyright 2016 dpa-infocom GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import aiohttp
import asyncio
import json
import logging
from os.path import join as path_join
from urllib.parse import urlencode, urljoin


logger = logging.getLogger(__name__)


class LiveblogClient(object):
    
    type = "liveblog"

    def __init__(self, *, config={}, **kwargs):
        self.session_token = None
        self.last_updated = None
        auth_creds = config.get("auth", {})
        self.user = auth_creds.get("user")
        self.password = auth_creds.get("password")
        self.source_id = config.get("source_id")
        self.endpoint = config.get("endpoint")
        self.label = config.get("label")
        self._session = None

    def __del__(self):
        if self._session:
            self._session.close()

    def __repr__(self):
        return "<Liveblog [{}] {}client_blogs/{}>".format(self.label, self.endpoint, self.source_id)

    @property
    def session(self):
        if self._session:
            return self._session
        headers = (("Content-Type", "application/json;charset=utf-8"),)
        conn = aiohttp.TCPConnector(verify_ssl=False, force_close=True, conn_timeout=10)
        self._session =  aiohttp.ClientSession(connector=conn, headers=headers)
        return self._session

    async def _login(self):
        params = json.dumps({"username": self.user, "password": self.password})
        login_url = "{}/auth".format(self.endpoint)
        try:
            resp = await self._post(login_url, params, status=201)
            if resp.get("token"):
                self.session_token = resp["token"]
                return self.session_token
        except aiohttp.errors.ClientOSError as e:
            logger.error("Login failed for [{}] on {}".format(self.user, self.endpoint))
            logger.error(e)
        return False

    async def _post(self, url, data, status=200):
        async with self.session.post(url, data=data.encode()) as resp:
            if resp.status == status:
                return await resp.json()
            else:
                raise Exception()

    async def _get(self, url, *, status=200):
        try:
            async with self.session.get(url) as resp:
                if resp.status == status:
                    return await resp.json()
                else:
                    logger.warning("No posts got fetched! [Status: {}]".format(resp.status))
        except Exception as e:
            logger.error("Requesting posts failed for [{}] {}client_blogs/{}".format(self.label or "-", self.endpoint, self.source_id))
            logger.error(e)
        return {}
