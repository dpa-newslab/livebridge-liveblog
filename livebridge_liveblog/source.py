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
from datetime import datetime
from os.path import join as path_join
from urllib.parse import urlencode, urljoin
from livebridge_liveblog.post import LiveblogPost
from livebridge_liveblog.common import LiveblogClient
from livebridge.base import PollingSource

logger = logging.getLogger(__name__)


class LiveblogSource(LiveblogClient, PollingSource):

    type = "liveblog"

    def _reset_source_meta(self):
        logger.debug("++++++++++ resetting source meta")
        self.source_meta = {}

    async def _check_source_status(self):
        if not self.source_meta:
            asyncio.get_event_loop().call_later(30, self._reset_source_meta)

            url = "{}/{}".format(self.endpoint, path_join("client_blogs", str(self.source_id)))
            logger.debug("#######  checking blog meta")
            self.source_meta = await self._get(url)
            self.is_archived = True if self.source_meta.get("blog_status") == "closed" else False
        return False if self.is_archived else True

    async def _get_updated(self):
        if not self.last_updated:
            self.last_updated = await self.get_last_updated(self.source_id)

        if not self.last_updated:
            self.last_updated = datetime.utcnow()

        return {"gt": datetime.strftime(self.last_updated, "%Y-%m-%dT%H:%M:%S+00:00")}

    async def _get_posts_params(self):
        # define "updated" filter param
        updated = await self._get_updated()

        # build query param
        source = {"query": {
                        "filtered": {
                            "filter": {
                                "and": [{
                                    "range": {
                                        "_updated": updated
                                    }
                                }]
                            }
                        }
                    },
                    "sort": [{
                        "_updated": {
                            "order": "asc"
                        }
                    }],
                }
        return urlencode([
            ("max_results", 20),
            ("page", 1),
            ("source", json.dumps(source))
        ])

    async def _get_posts_url(self):
        params = await self._get_posts_params()
        url = "{}/{}?{}".format(self.endpoint, path_join("client_blogs", str(self.source_id), "posts"), params)
        return url

    async def poll(self):
        if not await self._check_source_status():
            logger.info("==> Liveblog {} archived, skipping poll requests ...".format(self.source_id))
            return []
        url = await self._get_posts_url()
        res = await self._get(url)
        posts = [LiveblogPost(p) for p in res.get("_items",[])]
        logger.debug("++>Calling {}".format(self.source_id))
        # remember updated timestamp
        for p in posts:
            self.last_updated = p.updated

        return posts

