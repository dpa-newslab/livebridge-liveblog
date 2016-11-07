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
from livebridge.base import PollingSource
from tests import load_json

class LiveblogSourceTests(asynctest.TestCase):

    def setUp(self):
        self.conf = {
            "auth": {
                "user": "foo",
                "password": "bla",
            },
            "source_id": 12345,
            "endpoint": "https://example.com/api",
            "label": "Testlabel"
        }
        self.client = LiveblogSource(config=self.conf)

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
        assert issubclass(LiveblogSource, LiveblogClient) == True
        assert issubclass(LiveblogSource, PollingSource) == True

    @asynctest.ignore_loop
    def test_session(self):
        assert self.client._session == None
        session = self.client.session
        assert type(session) == aiohttp.client.ClientSession
        assert self.client._session == session

    @asynctest.ignore_loop
    def test_close_session(self):
        session = asynctest.MagicMock()
        session.close =  asynctest.CoroutineMock(return_value=True)
        self.client._session = session
        assert self.client.session == session
        self.client.__del__()
        assert session.close.called == 1

    async def test_login_ok(self):
        api_res = {"token": "foo"}
        self.client._post =  asynctest.CoroutineMock(return_value=api_res)
        res = await self.client._login()
        assert res == api_res["token"]
        assert self.client._post.call_args_list[0][0][0] == 'https://example.com/api/auth'
        assert json.loads(self.client._post.call_args_list[0][0][1]) == {'password': 'bla', 'username': 'foo'}
        assert self.client._post.call_args_list[0][1]["status"] == 201

    async def test_login_not_ok(self):
        self.client._post = asynctest.CoroutineMock(side_effect=aiohttp.errors.ClientOSError)
        res = await self.client._login()
        assert res == False

    async def test_get_failing(self):
        self.client._session = "will fail"
        res = await self.client._get("http://example.com")
        assert res == {}
 
    @asynctest.ignore_loop
    def test_get_posts_url(self):
        url = self.client._get_posts_url()
        assert type(url) == str
        assert True == url.startswith("https://example.com/api/client_blogs/12345/posts?max_results=20&page=1&source=%7B%22")
        assert True == url.endswith("%7D")

        self.client.endpoint= "https://example.com/api/"
        url = self.client._get_posts_url()
        assert type(url) == str
        assert True == url.startswith("https://example.com/api/client_blogs/12345/posts?max_results=20&page=1&source=%7B%22")
        assert True == url.endswith("%7D")

    @asynctest.ignore_loop
    def test_get_posts_params(self):
        # without last_updated time
        params = self.client._get_posts_params()
        p = parse_qs(params)
        assert p["max_results"] == ["20"]
        assert p["page"] == ["1"]
        assert p["source"][0].find('[{"range": {"_updated": {}}}]') > 0

        # with last_updated time
        self.client.last_updated = datetime(2014,10,20, 14, 48, 34)
        params = self.client._get_posts_params()
        p = parse_qs(params)
        assert p["max_results"] == ["20"]
        assert p["page"] == ["1"]
        assert p["source"][0].find('{"gt": "2014-10-20T14:48:34+00:00"}') > 0

        # with last_updated as string, will fail
        self.client.last_updated = "2014-10-20T14:48:34+00:00"
        with self.assertRaises(Exception):
            params = self.client._get_posts_params()

    async def test_get_api_posts(self):
        api_res = load_json('posts.json')
        self.client._get = asynctest.CoroutineMock(return_value=api_res)
        # first run
        assert self.client.last_updated == None
        posts = await self.client.poll()
        assert type(posts) == list
        assert posts == []
        assert self.client._get.call_args_list[0][0][0].startswith("https://example.com") == True

        # second run, set last updated timestamp before
        self.client.last_updated = datetime(2016, 10, 20, 15, 22, 30)
        posts = await self.client.poll()
        assert type(posts) == list
        assert [] == [p for p in posts if type(p) != LiveblogPost]

    async def test_get_api_posts_failing(self):
        assert self.client.last_updated == None
        posts = await self.client.poll()
        assert posts == []
        assert self.client.last_updated == None

