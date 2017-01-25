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
import asynctest
import os.path
from livebridge_liveblog import LiveblogLiveblogConverter
from livebridge.base import ConversionResult
from tests import load_json

class LiveblogLiveblogConverterTest(asynctest.TestCase):

    def setUp(self):
        self.converter = LiveblogLiveblogConverter()

    async def test_convert(self):
        post = load_json('post_to_convert.json')
        result = await self.converter.convert(post)
        assert type(result.content) == list
        assert len(result.content) == 6
        assert result.content[4] == {'item_type': 'text','text': 'Nochmal <i><b>abschließender</b></i> Text.'}
        assert result.content[1]["item_type"] == "image"
        assert result.content[3]["meta"]["quote"] == "Mit dem Wissen wächst der Zweifel."

    async def test_convert_invalid_image(self):
        post = load_json('post_to_convert.json')
        del post["groups"][1]["refs"][1]["item"]["meta"]["media"]["renditions"]
        result = await self.converter.convert(post)
        assert len(result.content) == 5

    async def test_convert_invalid_items(self):
        post = load_json('post_to_convert.json')
        post["groups"] = "foo"
        result = await self.converter.convert(post)
        assert len(result.content) == 0

    async def test_convert_unknown_type(self):
        post = load_json('post_to_convert.json')
        post["groups"][1]["refs"][1]["item"]["item_type"] = "baz"
        result = await self.converter.convert(post)
        assert len(result.content) == 5
