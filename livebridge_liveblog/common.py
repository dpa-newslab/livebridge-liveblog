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
import base64
import json
import logging
from os.path import join as path_join
from urllib.parse import urlencode, urljoin
from livebridge.base import InvalidTargetResource

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
        self.target_id = config.get("target_id")
        self.verify_ssl = config.get("verify_ssl", True)
        self.endpoint = config.get("endpoint")
        self.endpoint = self.endpoint[:-1] if self.endpoint.endswith("/") else self.endpoint
        self.label = config.get("label")
        self.save_as_draft = config.get("draft", False)
        self.save_as_contribution = config.get("submit", False)
        self._session = None

        self._source_meta = {}
        self._source_status = True
        self._source_check_interval = int(config.get("source_check_interval", 600))
        self._source_check_handler = None

    def __repr__(self):
        return "<Liveblog [{}] {}client_blogs/{}>".format(self.label, self.endpoint, self.source_id or self.target_id)

    def _get_auth_header(self):
        return {"Authorization": "Basic "+base64.b64encode(bytes(self.session_token+":", "UTF-8")).decode("utf-8")}

    @property
    def session(self):
        if self._session:
            return self._session
        headers = {"Content-Type": "application/json;charset=utf-8"}
        if self.session_token:
            headers.update(self._get_auth_header())
        conn = aiohttp.TCPConnector(ssl=self.verify_ssl)
        self._session = aiohttp.ClientSession(connector=conn, headers=headers, conn_timeout=10)
        return self._session

    async def stop(self):
        if self._source_check_handler is not None:
            self._source_check_handler.cancel()

        if self._session:
            await self._session.close()

    async def _login(self):
        params = json.dumps({"username": self.user, "password": self.password})
        login_url = "{}/auth".format(self.endpoint)
        try:
            resp = await self._post(login_url, params, status=201)
            if resp.get("token"):
                self.session_token = resp["token"]
                # reset session
                if self._session:
                    self._session.close()
                    self._session = None
                return self.session_token
        except aiohttp.client_exceptions.ClientOSError as e:
            logger.error("Login failed for [{}] - {}".format(self, login_url))
            logger.error(e)
        return False

    async def _post(self, url, data, status=200, headers=None):
        try:
            async with self.session.post(url, data=data.encode(), headers=headers) as resp:
                if resp.status == status:
                    return await resp.json()
                else:
                    logger.error("POST failed: {} [{}]".format(await resp.text(), resp.status))
                    raise Exception()
        except Exception as e:
            logger.error("Posting post failed for [{}] - {}".format(self, url))
            logger.exception(e)

    async def _patch(self, url, data, status=200, etag=None):
        try:
            headers = {"If-Match": etag} if etag else None
            async with self.session.patch(url, data=data.encode(), headers=headers) as resp:
                if resp.status == status:
                    return await resp.json()
                elif resp.status == 412:
                    raise InvalidTargetResource("Resource was edited at target, can't be updated anymore. {}".format(await resp.text()))
                else:
                    logger.error("PATCH failed: {} [{}]".format(await resp.text(), resp.status))
                    raise Exception()
        except InvalidTargetResource:
            raise
        except Exception as e:
            logger.error("Patching post failed for [{}] - {}".format(self, url))
            logger.exception(e)

    async def _get(self, url, *, status=200):
        try:
            async with self.session.get(url) as resp:
                if resp.status == status:
                    return await resp.json()
                else:
                    logger.warning("No data got fetched! [Status: {}] - {}".format(resp.status, url))
        except Exception as e:
            logger.error("Requesting posts failed for [{}] {}client_blogs/{}".format(self.label or "-", self.endpoint, self.source_id))
            logger.error(e)
        return {}
