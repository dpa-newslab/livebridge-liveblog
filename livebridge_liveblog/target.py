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
import logging
import json
from livebridge.base import BaseTarget, TargetResponse
from livebridge_liveblog.common import LiveblogClient


logger = logging.getLogger(__name__)


class LiveblogTarget(LiveblogClient, BaseTarget):

    type = "liveblog" 

    def get_id_at_target(self, post):
        """Extracts from the given **post** the id of the target resource.
        
        :param post: post  being processed
        :type post: livebridge.posts.base.BasePost
        :returns: string"""  
        id_at_target = None
        if post.target_doc:
            id_at_target = post.target_doc.get("_id")
        else:
            logger.warning("No id at target found.")
        return id_at_target

    def get_etag_at_target(self, post):
        """Extracts from the given **post** the etag of the target resource.
        
        :param post: post  being processed
        :type post: livebridge.posts.base.BasePost
        :returns: string"""  
        etag_at_target = None
        if post.target_doc:
            etag_at_target = post.target_doc.get("_etag")
        else:
            logger.warning("No id at target found.")
        return etag_at_target

    async def _save_post(self, items):
        refs = []
        for item in items:
            refs.append({"residRef": item["guid"]})

        data = {
            "post_status": "open",
            "sticky": False,
            "highlight": False,
            "blog": self.target_id,
            "groups": [{
                "id": "root",
                "refs": [{
                    "idRef": "main"
                }],
                "role": "grpRole:NEP"
            }, {
                "id": "main",
                "refs": refs,
                "role": "grpRole:Main"
            }]
        }
        url = "{}/{}".format(self.endpoint, "posts")
        post = await self._post(url, json.dumps(data), status=201)
        return post


    async def _save_item(self, data):
        data["blog"] = self.target_id
        url = "{}/{}".format(self.endpoint, "items")
        item = await self._post(url, json.dumps(data), status=201)
        return item

    async def post_item(self, post):
        """Build your request to create post at service."""
        await self._login()
        items = []
        for item in post.content:
            items.append(await self._save_item(item))
        return TargetResponse(await self._save_post(items))

    async def update_item(self, post):
        """Build your request to update post at service."""
        update_url = "/api/update"
        await self._login()
        data = {"text": post.content, "id": post.data.get("id")}
        return TargetResponse(await self._do_action(update_url, data))

    async def delete_item(self, post):
        """Build your request to update post at service."""
        await self._login()
        url = "{}/{}/{}".format(self.endpoint, "posts", self.get_id_at_target(post))
        data = {"deleted": True, "post_status": "open"}
        return TargetResponse(await self._patch(url, json.dumps(data), etag=self.get_etag_at_target(post)))

    async def handle_extras(self, post):
        """Do exta actions here if needed.
           Will be called after methods above."""
        return None


