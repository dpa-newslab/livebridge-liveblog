# -*- coding: utf-8 -*-
#
# Copyright 2017 dpa-infocom GmbH
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
from livebridge.base import BaseConverter, ConversionResult


logger = logging.getLogger(__name__)


class LiveblogLiveblogConverter(BaseConverter):

    source = "liveblog"
    target = "liveblog"

    async def _convert_image(self, item):
        logger.debug("CONVERTING IMAGE")
        content = ""
        tmp_path = None
        try:
            # handle image
            image_data = item["item"]["meta"]["media"]["renditions"]["baseImage"]
            if image_data:
                tmp_path = await self._download_image(image_data)

            meta = {
                "caption": item["item"]["meta"]["caption"],
                "credit":item["item"]["meta"]["credit"],
            }
            content = {"text": item["item"]["text"],"meta": meta,"item_type":"image", "tmp_path": tmp_path}
        except Exception as e:
            logger.error("Fatal downloading image item.")
            logger.exception(e)
        return content, tmp_path

    async def _convert_text(self, item):
        logger.debug("CONVERTING TEXT")
        text = item["item"]["text"].strip()
        content = {"text":text,"item_type":"text"}
        return content

    async def _convert_quote(self, item):
        logger.debug("CONVERTING QUOTE")
        meta = item["item"]["meta"]
        content = {"text": item["item"]["text"],"meta": item["item"]["meta"],"item_type":"quote"}
        return content

    async def _convert_embed(self, item):
        logger.debug("CONVERTING EMBED")
        content = {"text": item["item"]["text"],"meta": item["item"]["meta"],"item_type":"embed"}
        return content

    async def convert(self, post):
        post_items = []
        images = []
        logger.debug("####")
        logger.debug(post)
        try:
            for g in post.get("groups", []):
                if g["id"] != "main":
                    continue

                for item in g["refs"]:
                    if item["item"]["item_type"] == "text":
                        post_items.append(await self._convert_text(item))
                    elif item["item"]["item_type"] == "quote":
                        post_items.append(await self._convert_quote(item))
                    elif item["item"]["item_type"] == "image":
                        content, img_path = await self._convert_image(item)
                        post_items.append(content)
                        if img_path:
                            images.append(img_path)
                    elif item["item"]["item_type"] == "embed":
                        post_items.append(await self._convert_embed(item))
                    else:
                        logger.debug("CONVERSION UNKNOWN")
                        logger.debug("Typ: {}".format(item["type"]))
                        logger.debug("Item-Type: {}".format(item["item"]["item_type"]))
                        logger.debug(item)
                        logger.debug("\n\n")
            # filter empty items
            post_items = list(filter(None, post_items))
        except Exception as e:
            logger.error("Converting post failed.")
            logger.exception(e)
        return ConversionResult(content=post_items, images=images)
