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
import logging
import json
from urllib.parse import quote_plus
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

    def _build_post_data(self, items):
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
        return data


    async def _save_item(self, data):
        if data["item_type"] == "image":
            img_data = await self._save_image(data)
            logger.debug("IMAGE_DATA {}".format(img_data))
            data = self._build_image_item(data, img_data)
        data["blog"] = self.target_id
        url = "{}/{}".format(self.endpoint, "items")
        item = await self._post(url, json.dumps(data), status=201)
        return item

    def _build_image_item(self, item, resource):
        caption = item["meta"].get("caption", "")
        credit = item["meta"].get("credit", "")
        new_item = {
            "item_type": "image",
            "meta": {
                "caption": caption,
                "credit": credit,
                "media": {
                    "_id": resource.get("_id"),
                    "renditions": resource.get("renditions", {}),
                }
            }
        }
        text = '<figure> <img src="{}" alt="{}" srcset="{} {}w, {} {}w, {} {}w, {} {}w" />'
        text += '<figcaption>{}</figcaption></figure>'
        byline = caption
        if credit:
            byline += " Credit: {}".format(credit)
        media = new_item["meta"]["media"]["renditions"]
        new_item["text"] = text.format(
            media["thumbnail"]["href"], quote_plus(caption),
            media["baseImage"]["href"], media["baseImage"]["width"],
            media["viewImage"]["href"], media["viewImage"]["width"],
            media["thumbnail"]["href"], media["thumbnail"]["width"],
            media["original"]["href"], media["original"]["width"],
            byline)
        return new_item

    async def _save_image(self, img_item):
        new_img = None
        try:
            url = "{}/{}".format(self.endpoint, "archive")
            files = {"media": open(img_item["tmp_path"], "rb")}
            connector = aiohttp.TCPConnector(verify_ssl=False, conn_timeout=10)
            async with aiohttp.post(url, data=files, headers=self._get_auth_header(), connector=connector) as r:
                if r.status == 201:
                    new_img = await r.json()
                else:
                    raise Exception("Image{} could not be saved!".format(img_item))
        except Exception as e:
            logger.error("Posting image failed for [{}] - {}".format(self, img_item))
            logger.exception(e)
        return new_img

    async def post_item(self, post):
        """Build your request to create post at service."""
        await self._login()
        # save item parts
        logger.debug("IMAGES: {}".format(post.images))
        logger.debug("POST: {}".format(post.content))
        items = []
        for item in post.content:
            items.append(await self._save_item(item))
        # save new post
        data = self._build_post_data(items)
        url = "{}/{}".format(self.endpoint, "posts")
        return TargetResponse(await self._post(url, json.dumps(data), status=201))

    async def update_item(self, post):
        """Build your request to update post at service."""
        await self._login()
        # save item parts
        items = []
        for item in post.content:
            items.append(await self._save_item(item))
        # patch exsiting post
        data = self._build_post_data(items)
        url = "{}/{}/{}".format(self.endpoint, "posts", self.get_id_at_target(post))
        return TargetResponse(await self._patch(url, json.dumps(data), etag=self.get_etag_at_target(post)))

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


