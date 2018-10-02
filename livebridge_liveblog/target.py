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
from livebridge.base import BaseTarget, TargetResponse, InvalidTargetResource
from livebridge_liveblog.common import LiveblogClient


logger = logging.getLogger(__name__)


class LiveblogTarget(LiveblogClient, BaseTarget):

    type = "liveblog"

    def get_id_at_target(self, post):
        """Extracts id from the given **post** of the target resource.

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
        """Extracts etag from the given **post** of the target resource.

        :param post: post  being processed
        :type post: livebridge.posts.base.BasePost
        :returns: string"""
        etag_at_target = None
        if post.target_doc:
            etag_at_target = post.target_doc.get("_etag")
        else:
            logger.warning("No id at target found.")
        return etag_at_target

    def _get_post_status(self):
        if self.save_as_draft == True:
            return "draft"
        elif self.save_as_contribution == True:
            return "submitted"
        return "open"

    def _build_post_data(self, post, items):
        data = {
            "post_status": self._get_post_status(),
            "sticky": True if post.is_sticky else False,
            "lb_highlight":  True if post.is_highlighted else False,
            "blog": self.target_id,
            "groups": [{
                "id": "root",
                "refs": [{
                    "idRef": "main"
                }],
                "role": "grpRole:NEP"
            }, {
                "id": "main",
                "refs": [{"residRef": item["guid"]} for item in items],
                "role": "grpRole:Main"
            }]
        }
        return data

    def _build_image_item(self, item, resource):
        caption = item["meta"].get("caption", "")
        credit = item["meta"].get("credit", "")
        # byline
        byline = caption
        byline += " Credit: {}".format(credit) if credit else ""
        # text value for image item
        text = '<figure> <img src="{}" alt="{}" srcset="{} {}w, {} {}w, {} {}w, {} {}w" />'
        text += '<figcaption>{}</figcaption></figure>'
        media = resource.get("renditions", {})
        text = text.format(
            media["thumbnail"]["href"], quote_plus(caption),
            media["baseImage"]["href"], media["baseImage"]["width"],
            media["viewImage"]["href"], media["viewImage"]["width"],
            media["thumbnail"]["href"], media["thumbnail"]["width"],
            media["original"]["href"], media["original"]["width"],
            byline)
        # build item
        new_item = {
            "item_type": "image",
            "text": text,
            "meta": {
                "caption": caption,
                "credit": credit,
                "media": {
                    "_id": resource.get("_id"),
                    "renditions": media,
                }
            }
        }
        return new_item

    async def _save_item(self, data):
        if data["item_type"] == "image":
            # special handling for image items
            img_data = await self._save_image(data)
            data = self._build_image_item(data, img_data)
        # save item in target blog
        data["blog"] = self.target_id
        url = "{}/{}".format(self.endpoint, "items")
        item = await self._post(url, json.dumps(data), status=201)
        return item

    async def _save_image(self, img_item):
        new_img = None
        try:
            # upload photo to liveblog instance
            url = "{}/{}".format(self.endpoint, "archive")
            # build form data
            data = aiohttp.FormData()
            data.add_field('media',
               open(img_item["tmp_path"], 'rb'),
               content_type='image/jpg')
            # send data
            connector = aiohttp.TCPConnector(ssl=False)
            headers = self._get_auth_header()
            session = aiohttp.ClientSession(connector=connector, headers=headers, conn_timeout=10)
            async with session.post(url, data=data) as r:
                if r.status == 201:
                    new_img = await r.json()
                else:
                    raise Exception("Image{} could not be saved!".format(img_item))
            await session.close()
        except Exception as e:
            logger.error("Posting image failed for [{}] - {}".format(self, img_item))
            logger.exception(e)
        return new_img

    async def post_item(self, post):
        """Build your request to create a post."""
        await self._login()
        # save item parts
        items = []
        for item in post.content:
            items.append(await self._save_item(item))
        # save new post
        data = self._build_post_data(post, items)
        url = "{}/{}".format(self.endpoint, "posts")
        return TargetResponse(await self._post(url, json.dumps(data), status=201))

    async def update_item(self, post):
        """Build your request to update a post."""
        await self._login()
        # save item parts
        items = []
        for item in post.content:
            items.append(await self._save_item(item))
        data = self._build_post_data(post, items)
        # get id of post at target
        id_at_target = self.get_id_at_target(post)
        if not id_at_target:
            raise InvalidTargetResource("No id for resource at target found!")
        # patch existing post
        url = "{}/{}/{}".format(self.endpoint, "posts", id_at_target)
        return TargetResponse(await self._patch(url, json.dumps(data), etag=self.get_etag_at_target(post)))

    async def delete_item(self, post):
        """Build your request to delete a post."""
        await self._login()
        # get id of post at target
        id_at_target = self.get_id_at_target(post)
        if not id_at_target:
            raise InvalidTargetResource("No id for resource at target found!")
        # delete post
        url = "{}/{}/{}".format(self.endpoint, "posts", id_at_target)
        data = {"deleted": True, "post_status": "open"}
        return TargetResponse(await self._patch(url, json.dumps(data), etag=self.get_etag_at_target(post)))

    async def handle_extras(self, post):
        return None
