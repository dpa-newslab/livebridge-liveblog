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
from datetime import datetime
from livebridge_liveblog import LiveblogPost
from tests import load_json

class LiveblogPostTest(asynctest.TestCase):

    def setUp(self):
        self.post = load_json('post_to_convert.json')
        self.images = ["/tmp/one.jpg"]
        self.content= "foobaz"
        self.lp = LiveblogPost(self.post, content=self.content, images=self.images)

    @asynctest.ignore_loop
    def test_init(self):
        assert self.lp.data == self.post
        assert hasattr(self.lp, "is_deleted") == True
        assert hasattr(self.lp, "is_update") == True
        assert hasattr(self.lp, "is_sticky") == True
        assert self.lp.id ==  "urn:newsml:localhost:2016-04-28T11:24:22.973191:666890f6-9054-4f81-81ac-cc6d5f02b2c9"
        assert self.lp.source_id ==  "56fceedda505e600f71959c8"
        assert type(self.lp.updated) == datetime
        assert type(self.lp.created) == datetime
        assert self.lp.created.year ==  2016
        assert self.lp.created.minute ==  24
        assert self.lp.updated.year == 2016
        assert self.lp.updated.second == 22
        assert self.lp.images == self.images
        assert self.lp.content == self.content

    @asynctest.ignore_loop
    def test_get_action(self):
        # ignore/submitted
        self.lp._existing = None
        self.post["post_status"] = "submitted"
        assert self.lp.get_action() == "ignore"
        # ignore/draft
        self.post["post_status"] = "draft"
        assert self.lp.get_action() == "ignore"
        # no ignore, post is known
        self.lp._existing = {"foo":"baz"}
        assert self.lp.get_action() != "ignore"

        # should be update
        self.post["post_status"] = ""
        assert self.lp.get_action() == "update"

        # test delete
        self.lp._deleted = True
        assert self.lp.get_action() == "delete"

        # test ignore for unknown
        self.lp._deleted = None
        self.lp._existing = None
        assert self.lp.get_action() == "create"

        # test ignore for deleted
        self.lp._deleted = True
        assert self.lp.get_action() == "ignore"

    @asynctest.ignore_loop
    def test_is_not_delete(self):
        assert self.lp.is_deleted == False

    @asynctest.ignore_loop
    def test_is_deleted(self):
        self.lp.data["deleted"] = True
        assert self.lp.is_deleted == True

        self.lp._deleted = False
        assert self.lp.is_deleted == False

    @asynctest.ignore_loop
    def test_is_deleted_unpublished(self):
        self.lp.data["unpublished_date"] = "2016-05-06T15:00:59+00:00"
        self.lp.data["published_date"] = "2016-05-06T15:00:39+00:00"
        assert self.lp.is_deleted == True

    @asynctest.ignore_loop
    def test_is_sticky(self):
        assert self.lp.is_sticky == False
        self.lp.data["sticky"] = True
        assert self.lp.is_sticky == True

    @asynctest.ignore_loop
    def test_is_highlighted(self):
        assert self.lp.is_highlighted == False
        self.lp.data["lb_highlight"] = True
        assert self.lp.is_highlighted == True

    @asynctest.ignore_loop
    def test_is_submitted(self):
        assert self.lp.is_submitted == False 
        self.lp.data["post_status"] = "submitted"
        assert self.lp.is_submitted == True

    @asynctest.ignore_loop
    def test_is_draft(self):
        assert self.lp.is_draft == False
        self.lp.data["post_status"] = "draft"
        assert self.lp.is_draft == True

    @asynctest.ignore_loop
    def test_is_update(self):
        self.lp.data["_created"] = "new"
        self.lp.data["_updated"] = "new"
        assert self.lp.is_update == False

        self.lp.data["_updated"] = "new2"
        assert self.lp.is_update == True

    @asynctest.ignore_loop
    def test_existing(self):
        assert self.lp.get_existing() == None
        assert self.lp.is_known == False
        self.lp.set_existing({"foo": "baz"})
        assert self.lp.get_existing() == {"foo": "baz"}
        assert self.lp.is_known == True

    @asynctest.ignore_loop
    def test_target_doc(self):
        assert self.lp.target_doc == None
        self.lp._existing = {"target_doc": {"doc": "foo"}}
        assert self.lp.target_doc == self.lp._existing["target_doc"]

    @asynctest.ignore_loop
    def test_target_id(self):
        assert self.lp._target_id == None
        self.lp._target_id = "foobaz"
        assert self.lp.target_id == "foobaz"

    @asynctest.ignore_loop
    def test_target_id_from_existing(self):
        self.lp.set_existing({"target_id": "foobaz"})
        assert self.lp.target_id == "foobaz"
