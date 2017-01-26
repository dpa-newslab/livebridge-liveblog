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
from collections import UserDict
from livebridge_liveblog import LiveblogTarget 
from livebridge_liveblog.common import LiveblogClient
from livebridge.base import BaseTarget, TargetResponse
from tests import load_json
from .test_source import TestResponse

class LiveblogTargetTests(asynctest.TestCase):

    def setUp(self):
        self.conf = {
            "auth": {
                "user": "foo",
                "password": "bla",
            },
            "target_id": 12345,
            "endpoint": "https://example.com/api",
            "label": "Testlabel"
        }
        self.target = LiveblogTarget(config=self.conf)        

    @asynctest.ignore_loop
    def test_init(self):
        assert self.target.target_id == self.conf["target_id"]
        assert self.target.type == "liveblog"
        assert type(self.target) == LiveblogTarget
        assert repr(self.target).startswith("<Liveblog ") == True
        assert self.target.user == self.conf["auth"]["user"]
        assert self.target.password == self.conf["auth"]["password"]
        assert self.target.endpoint == self.conf["endpoint"]
        assert self.target.label == self.conf["label"]
        assert self.target.save_as_draft == False
        assert issubclass(LiveblogTarget, LiveblogClient) == True
        assert issubclass(LiveblogTarget, BaseTarget) == True

    @asynctest.ignore_loop
    def test_conf_draft(self):
        self.conf["draft"] = True
        target = LiveblogTarget(config=self.conf)
        assert target.save_as_draft == True

    @asynctest.ignore_loop
    def test_get_id_from_target(self):
        res = self.target.get_id_at_target(asynctest.MagicMock(target_doc={"_id": "foo"}))
        assert res == "foo"
    
        res = self.target.get_id_at_target(asynctest.MagicMock(target_doc=None))
        assert res == None

    @asynctest.ignore_loop
    def test_get_etag_from_target(self):
        res = self.target.get_etag_at_target(asynctest.MagicMock(target_doc={"_etag": "foo"}))
        assert res == "foo"
    
        res = self.target.get_etag_at_target(asynctest.MagicMock(target_doc=None))
        assert res == None

    @asynctest.ignore_loop
    def test_build_post_data(self):
        post = asynctest.Mock(is_highlighted = True, is_sticky=False)
        res = self.target._build_post_data(post, [{"guid": "urn-1"}, {"guid": "urn-2"}])
        assert res["blog"] == 12345
        assert res["highlight"] == True
        assert res["sticky"] == False
        assert res["post_status"] == "open"
        assert res["groups"][1]["refs"] == [{'residRef': 'urn-1'}, {'residRef': 'urn-2'}]

        self.target.save_as_draft = True
        post = asynctest.Mock(is_highlighted=False, is_sticky=True)
        res = self.target._build_post_data(post, [{"guid": "urn-1"}, {"guid": "urn-2"}])
        assert res["highlight"] == False
        assert res["sticky"] == True
        assert res["post_status"] == "draft"

    @asynctest.ignore_loop
    def test_build_image_item(self):
        post = load_json('post_to_convert.json')
        resource = post["groups"][1]["refs"][1]["item"]["meta"]["media"]
        item = {"meta": {"caption": "Unterschrift", "credit": "Rechte"}}
        res = self.target._build_image_item(item, resource)
        assert type(res) == dict
        assert res["item_type"] == "image"
        assert res["text"].startswith("<figure> ") == True
        assert res["meta"]["caption"] == item["meta"]["caption"]
        assert res["meta"]["credit"] == item["meta"]["credit"]
        assert res["meta"]["media"]["renditions"] == resource["renditions"]

    async def test_save_item(self):
        data = {"item_type": "image", "tmp_path": "/tmp/test.jpg"}
        self.target._save_image = asynctest.CoroutineMock(return_value={"img": "data"})
        self.target._build_image_item = asynctest.Mock(return_value={"item_type": "image"})
        self.target._post = asynctest.CoroutineMock(return_value={"item": "data"})
        res = await self.target._save_item(data)
        assert res == {"item": "data"}
        assert self.target._save_image.call_count ==  1
        assert self.target._build_image_item.call_count == 1
        assert self.target._post.call_count == 1

    async def test_save_image(self):
        self.target.session_token = "foo"
        img_item = {"item_type": "image", "tmp_path": "tests/test.jpg"}
        resp = TestResponse(url="http://example.com")
        with asynctest.patch("aiohttp.post") as patched:
            patched.return_value = resp
            res = await self.target._save_image(img_item)
            assert res == {"foo": "baz"}
            assert patched.call_count ==  1

            # failing 
            resp._status = 404
            res = await self.target._save_image(img_item)
            assert res == None

    async def test_post_item(self):
        self.target._login = asynctest.CoroutineMock(return_value=True)
        self.target._save_item = asynctest.CoroutineMock(return_value={"one": "two"})
        self.target._build_post_data = asynctest.Mock(return_value='{"foo": "baz"}')
        self.target._post = asynctest.CoroutineMock(return_value={"res": "true"})
        res = await self.target.post_item(asynctest.Mock(content=[1,2,3]))
        assert type(res) == TargetResponse
        assert res.data == {"res": "true"}
        assert self.target._login.call_count == 1
        assert self.target._build_post_data.call_count == 1
        assert self.target._save_item.call_count == 3
        assert self.target._post.call_count == 1

    async def test_update_item(self):
        self.target._login = asynctest.CoroutineMock(return_value=True)
        self.target._save_item = asynctest.CoroutineMock(return_value={"one": "two"})
        self.target._build_post_data = asynctest.Mock(return_value='{"foo": "baz"}')
        self.target._patch = asynctest.CoroutineMock(return_value={"res": "true"})
        res = await self.target.update_item(asynctest.Mock(content=[1,2,3]))
        assert type(res) == TargetResponse
        assert res.data == {"res": "true"}
        assert self.target._login.call_count == 1
        assert self.target._build_post_data.call_count == 1
        assert self.target._save_item.call_count == 3
        assert self.target._patch.call_count == 1

    async def test_delete_item(self):
        self.target._login = asynctest.CoroutineMock(return_value=True)
        self.target._patch = asynctest.CoroutineMock(return_value={"res": "true"})
        res = await self.target.delete_item(asynctest.Mock(content=[1,2,3]))
        assert type(res) == TargetResponse
        assert res.data == {"res": "true"}
        assert self.target._login.call_count == 1
        assert self.target._patch.call_count == 1

    async def test_handle_extras(self):
        res = await self.target.handle_extras(asynctest.Mock(content=[1,2,3]))
        assert res == None
