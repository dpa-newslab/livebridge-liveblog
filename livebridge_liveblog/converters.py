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
from livebridge.base import BaseConverter, ConversionResult


logger = logging.getLogger(__name__)


class LiveblogLiveblogConverter(BaseConverter):

    source = "liveblog"
    target = "liveblog"

    async def _convert_image(self, item):
        logger.debug("CONVERTING IMAGE")
        content = ""
        tmp_path = None
        """try:
            # handle image
            image_data = item["item"]["meta"]["media"]["renditions"]["baseImage"]
            if image_data:
                tmp_path = await self._download_image(image_data)

            # handle text
            caption = item["item"]["meta"]["caption"]
            if caption:
                content += "<br>{} ".format(caption)
            credit = item["item"]["meta"]["credit"]
            if credit:
                content += "<i>({})</i>".format(credit)
            if caption or credit:
                content += "<br>"
            # assure at last a whitespace!
            content += " "
        except Exception as e:
            logger.error("Fatal downloading image item.")
            logger.exception(e)"""
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
        try:
            for g in post.get("groups", []):
                if g["id"] != "main":
                    continue

                for item in g["refs"]:
                    if item["item"]["item_type"] == "text":
                        post_items.append(await self._convert_text(item))
                    elif item["item"]["item_type"] == "quote":
                        post_items.append(await self._convert_quote(item))
                    #elif item["item"]["item_type"] == "image":
                    #    caption, img_path = await self._convert_image_inline(item)
                    #    if caption:
                    #        content += caption
                        #if img_path:
                        #    content += caption
                        #    images.append(img_path)
                    elif item["item"]["item_type"] == "embed":
                        post_items.append(await self._convert_embed(item))
                    else:
                        logger.debug("CONVERSION UNKNOWN")
                        logger.debug("Typ: {}".format(item["type"]))
                        logger.debug("Item-Type: {}".format(item["item"]["item_type"]))
                        logger.debug(item)
                        logger.debug("\n\n")
        except Exception as e:
            logger.error("Converting post failed.")
            logger.exception(e)
        return ConversionResult(content=post_items, images=images)#, data={"items": post_items})
