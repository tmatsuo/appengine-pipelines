#!/usr/bin/env python
#
# Copyright 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Test utilities for the Google App Engine Pipeline API."""

# Code originally from:
#   http://code.google.com/p/pubsubhubbub/source/browse/trunk/hub/testutil.py

import logging
import os
import sys
import tempfile


TEST_APP_ID = 'my-app-id'
TEST_VERSION_ID = 'my-version.1234'

# Assign the application ID up front here so we can create db.Key instances
# before doing any other test setup.
os.environ['APPLICATION_ID'] = TEST_APP_ID
os.environ['CURRENT_VERSION_ID'] = TEST_VERSION_ID
os.environ['HTTP_HOST'] = '%s.appspot.com' % TEST_APP_ID
os.environ['DEFAULT_VERSION_HOSTNAME'] = os.environ['HTTP_HOST']
os.environ['CURRENT_MODULE_ID'] = 'foo-module'


def setup_for_testing(require_indexes=True, define_queues=[]):
  """Sets up the stubs for testing.

  Args:
    require_indexes: True if indexes should be required for all indexes.
    define_queues: Additional queues that should be available.
  """
  from google.appengine.api import apiproxy_stub_map
  from google.appengine.api import memcache
  from google.appengine.api import queueinfo
  from google.appengine.datastore import datastore_stub_util
  from google.appengine.ext import testbed
  from google.appengine.ext.testbed import TASKQUEUE_SERVICE_NAME
  before_level = logging.getLogger().getEffectiveLevel()
  try:
    testbed = testbed.Testbed()
    logging.getLogger().setLevel(100)
    testbed.activate()
    testbed.setup_env(app_id=TEST_APP_ID)
    testbed.init_memcache_stub()

    hr_policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=1)
    testbed.init_datastore_v3_stub(consistency_policy=hr_policy)

    testbed.init_taskqueue_stub()

    root_path = os.path.realpath(os.path.dirname(__file__))
    
    # Actually need to flush, even though we've reallocated. Maybe because the
    # memcache stub's cache is at the module level, not the API stub?
    memcache.flush_all()
  finally:
    logging.getLogger().setLevel(before_level)

  taskqueue_stub = apiproxy_stub_map.apiproxy.GetStub('taskqueue')
  taskqueue_stub.queue_yaml_parser = (
      lambda x: queueinfo.LoadSingleQueue(
          'queue:\n- name: default\n  rate: 1/s\n' +
          '\n'.join('- name: %s\n  rate: 1/s' % name
                    for name in define_queues)))
