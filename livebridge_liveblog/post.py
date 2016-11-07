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
import asyncio
import logging
from dateutil.parser import parse as parse_date
from livebridge.base import BasePost

logger = logging.getLogger(__name__)

class LiveblogPost(BasePost):

    source = "liveblog"

    @property
    def id(self):
       return self.data.get("_id")

    @property
    def source_id(self):
       return self.data.get("blog")

    @property
    def created(self):
       return parse_date(self.data.get("_created"))

    @property
    def updated(self):
       return parse_date(self.data.get("_updated"))

    @property
    def is_update(self):
       return (self.data["_created"] != self.data["_updated"])

    @property
    def is_deleted(self):
        if hasattr(self, "_deleted"):
            return self._deleted

        self._deleted = self.data["deleted"]
        if self.data.get("unpublished_date") and \
            self.data["unpublished_date"] > self.data["published_date"]:
            self._deleted = True
        return self._deleted

    @property
    def is_sticky(self):
       return self.data.get("sticky", False)

    @property
    def is_submitted(self):
       return bool(self.data.get("post_status") == "submitted")

    @property
    def is_draft(self):
       return bool(self.data.get("post_status") == "draft")

    def get_action(self):
        if (self.is_submitted == True or self.is_draft == True) and not self.is_known:
            return "ignore"

        if not self.is_known:
            if not self.is_deleted:
                return "create"
            else:
                return "ignore"
        else:
            if self.is_deleted:
                return "delete"
            return "update"

