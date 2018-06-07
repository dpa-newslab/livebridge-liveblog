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
import asynctest
import aiohttp
import json
from datetime import datetime
from urllib.parse import parse_qs
from livebridge_liveblog.common import LiveblogClient
from livebridge_liveblog import LiveblogPost, LiveblogSource
from livebridge.base import PollingSource, InvalidTargetResource
from tests import load_json


class TestResponse:

    def __init__(self, url, data="", headers={}):
        self._status = 201
        self.req_data = data
        self.headers = headers

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass

    @property
    def status(self):
        return self._status

    async def json(self):
        return json.loads(self.req_data.decode("utf-8")) if self.req_data else {"foo": "baz"}

    async def text(self):
        return "text"


class InvalidResponse(TestResponse):
    status = 412


class LiveblogSourceTests(asynctest.TestCase):

    def setUp(self):
        self.conf = {
            "auth": {
                "user": "foo",
                "password": "bla",
            },
            "source_id": 12345,
            "endpoint": "https://example.com/api",
            "label": "Testlabel",
            "verify_ssl": False,
        }
        self.client = LiveblogSource(config=self.conf)

    async def tearDown(self):
        await self.client.stop()

    @asynctest.ignore_loop
    def test_init(self):
        assert self.client.type == "liveblog"
        assert self.client.mode == "polling"
        assert type(self.client) == LiveblogSource
        assert repr(self.client).startswith("<Liveblog ") == True
        assert self.client.user == self.conf["auth"]["user"]
        assert self.client.password == self.conf["auth"]["password"]
        assert self.client.source_id == self.conf["source_id"]
        assert self.client.endpoint == self.conf["endpoint"]
        assert self.client.label == self.conf["label"]
        assert self.client.verify_ssl == self.conf["verify_ssl"]
        assert issubclass(LiveblogSource, LiveblogClient) == True
        assert issubclass(LiveblogSource, PollingSource) == True

    @asynctest.ignore_loop
    def test_session(self):
        assert self.client._session == None
        self.client.session_token = "baz"
        self.client._get_auth_header = asynctest.CoroutineMock(return_value={})
        session = self.client.session
        assert type(session) == aiohttp.client.ClientSession
        assert self.client._session == session
        assert self.client._get_auth_header.call_count == 1

    async def test_stop_bridge(self):
        session = asynctest.MagicMock()
        session.close =  asynctest.CoroutineMock(return_value=True)
        self.client._session = session
        self.client.source_check_handler = asynctest.MagicMock(cancel=asynctest.CoroutineMock(return_value=None))
        assert self.client.session == session
        await self.client.stop()
        assert session.close.called == 1
        assert self.client.source_check_handler.cancel.call_count == 1

    @asynctest.ignore_loop
    def test_get_auth_header(self):
        self.client.session_token = "baz"
        header = self.client._get_auth_header()
        assert list(header.keys()) == ["Authorization"]

    async def test_login_ok(self):
        api_res = {"token": "foo"}
        self.client._session = asynctest.MagicMock(close=asynctest.CoroutineMock(return_value=None))
        self.client._post =  asynctest.CoroutineMock(return_value=api_res)
        res = await self.client._login()
        assert res == api_res["token"]
        assert self.client._post.call_args_list[0][0][0] == 'https://example.com/api/auth'
        assert json.loads(self.client._post.call_args_list[0][0][1]) == {'password': 'bla', 'username': 'foo'}
        assert self.client._post.call_args_list[0][1]["status"] == 201
        assert self.client._session == None

    async def test_login_not_ok(self):
        self.client._post = asynctest.CoroutineMock(side_effect=aiohttp.client_exceptions.ClientOSError)
        res = await self.client._login()
        assert res == False

    async def test_get_failing(self):
        self.client._session = asynctest.MagicMock(
            close=asynctest.CoroutineMock(return_value=None))
        res = await self.client._get("http://example.com")
        assert res == {}
 
    async def test_get_posts_url(self):
        self.client.last_updated = datetime(2014,10,20, 14, 48, 34)
        url = await self.client._get_posts_url()
        assert type(url) == str
        assert True == url.startswith("https://example.com/api/client_blogs/12345/posts?max_results=20&page=1&source=%7B%22")
        assert True == url.endswith("%7D")

    async def test_get_posts_params_new(self):
        # without last_updated time
        self.client._get_updated = asynctest.CoroutineMock(return_value={'gt': '2016-12-13T14:37:25+00:00'})
        params = await self.client._get_posts_params()
        p = parse_qs(params)
        assert p["max_results"] == ["20"]
        assert p["page"] == ["1"]
        assert p["source"][0].find('[{"range": {"_updated": {"gt": "2016-12-13T14:37:25+00:00"}}}]') > 0

    async def test_get_posts_params(self):
        # with last_updated time
        self.client.last_updated = datetime(2014,10,20, 14, 48, 34)
        params = await self.client._get_posts_params()
        p = parse_qs(params)
        assert p["max_results"] == ["20"]
        assert p["page"] == ["1"]
        assert p["source"][0].find('{"gt": "2014-10-20T14:48:34+00:00"}') > 0

        # with last_updated as string, will fail
        self.client.last_updated = "2014-10-20T14:48:34+00:00"
        with self.assertRaises(Exception):
            params = await self.client._get_posts_params()

    async def test_get_api_posts(self):
        self.client._is_source_open = asynctest.CoroutineMock(return_value=True)
        self.client._get = asynctest.CoroutineMock(return_value={})
        # first run
        assert self.client.last_updated == None
        self.client.get_last_updated = asynctest.CoroutineMock(return_value=None)
        posts = await self.client.poll()
        assert type(posts) == list
        assert posts == []
        assert self.client._get.call_args_list[0][0][0].startswith("https://example.com") == True
        assert self.client.get_last_updated.call_count == 1
        assert type(self.client.last_updated) == datetime

        # second run, set last updated timestamp before
        api_res = load_json('posts.json')
        self.client._get = asynctest.CoroutineMock(return_value=api_res)
        self.client.last_updated = datetime(2016, 10, 20, 15, 22, 30)
        posts = await self.client.poll()
        assert type(posts) == list
        assert [] == [p for p in posts if type(p) != LiveblogPost]
        assert self.client.last_updated == posts[-1].updated

        self.client._get = asynctest.CoroutineMock(return_value=api_res)
        self.client._is_source_open = asynctest.CoroutineMock(return_value=False)
        posts = await self.client.poll()
        assert type(posts) == list
        assert posts == []
        assert self.client._get.call_count == 0
        assert self.client._is_source_open.call_count == 1

    async def test_get_api_posts_failing(self):
        self.client._is_source_open = asynctest.CoroutineMock(return_value=True)
        assert self.client.last_updated == None
        self.client._get_updated = asynctest.CoroutineMock(return_value={"gt": "2016-12-13T13:17:54+00:00"})
        posts = await self.client.poll()
        assert posts == []
        assert self.client.last_updated == None

    async def test_post(self):
        data = '{"one": 1, "two": 2}'
        with asynctest.patch("aiohttp.client.ClientSession") as patched:
            patched.post = TestResponse
            self.client._session = patched
            res = await self.client._post("https://dpa.com/resource", data, 201)
            assert type(res) == dict
            assert res == json.loads(data)

            # failing
            res = await self.client._post("https://dpa.com/resource", data, 200)
            assert res == None

    async def test_patch(self):
        data = '{"one": 1, "two": 2}'
        with asynctest.patch("aiohttp.client.ClientSession") as patched:
            patched.patch = TestResponse
            self.client._session = patched
            res = await self.client._patch("https://dpa.com/resource", data, 201)
            assert type(res) == dict
            assert res == json.loads(data)

            # failing
            res = await self.client._patch("https://dpa.com/resource", data, 200)
            assert res == None

    async def test_patch_invalid_etag(self):
        with asynctest.patch("aiohttp.client.ClientSession") as patched:
            patched.patch = InvalidResponse
            self.client._session = patched
            with self.assertRaises(InvalidTargetResource):
                await self.client._patch("https://dpa.com/resource", '{"one": 1}', 200)

    async def test_get(self):
        with asynctest.patch("aiohttp.client.ClientSession") as patched:
            patched.get = TestResponse
            self.client._session = patched
            res = await self.client._get("https://dpa.com/resource", status=201)
            assert type(res) == dict
            assert res == {"foo": "baz"}

            # failing
            res = await self.client._get("https://dpa.com/resource", status=404)
            assert res == {}

    async def test_get_catch_exception(self):
        res = await self.client._get(None)
        assert res == {}

    @asynctest.ignore_loop
    def test_reset_blog_meta(self):
        self.client.source_meta = {"foo": "bla"}
        self.client._reset_source_meta()
        assert self.client.source_meta == {}

    async def test_is_source_open(self):
        self.client._get = asynctest.CoroutineMock(return_value={"blog_status": "open"})
        res = await self.client._is_source_open()
        assert res == True

        self.client.source_meta = {}
        self.client._get = asynctest.CoroutineMock(return_value={"blog_status": "closed"})
        res = await self.client._is_source_open()
        assert res == False
