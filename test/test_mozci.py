"""This file contains tests for mozci/mozci.py."""

import json
import pytest
import unittest

import mozci.mozci
from mozci.query_jobs import SUCCESS, PENDING, RUNNING, COALESCED

from mock import patch


MOCK_JSON = '''{
                "real-repo": {
                    "repo": "https://hg.mozilla.org/integration/real-repo",
                    "graph_branches": ["Real-Repo"],
                    "repo_type": "hg"}}'''

MOCK_JOBS = """
[{
    "submit_timestamp": 1435806434,
    "build_system_type": "buildbot",
    "machine_name": "tst-linux64-spot-1083",
    "job_group_symbol": "M",
    "job_group_name": "Mochitest",
    "platform_option": "opt",
    "job_type_description": "integration test",
    "result_set_id": 16679,
    "build_platform_id": 9,
    "result": "%(result)s",
    "id": 11294317,
    "machine_platform_architecture": "x86_64",
    "end_timestamp": 1435807607,
    "build_platform": "linux64",
    "job_guid": "56e77044a516ff857a21ebd52a97d73f7fdf29de",
    "job_type_name": "Mochitest",
    "ref_data_name": "Ubuntu VM 12.04 x64 mozilla-inbound opt test mochitest-1",
    "platform": "linux64",
    "state": "%(state)s",
    "running_eta": 1907,
    "pending_eta": 6,
    "build_os": "linux",
    "option_collection_hash": "102210fe594ee9b33d82058545b1ed14f4c8206e",
    "who": "tests-mozilla-inbound-ubuntu64_vm-opt-unittest",
    "failure_classification_id": 1,
    "job_type_symbol": "1",
    "reason": "scheduler",
    "job_group_description": "fill me",
    "tier": 1,
    "job_coalesced_to_guid": null,
    "machine_platform_os": "linux",
    "start_timestamp": 1435806437,
    "build_architecture": "x86_64",
    "device_name": "vm",
    "last_modified": "2015-07-02T03:29:09",
    "signature": "41f96d52f5fc013ae82825172d9e13f4e517c5ac"
  },
  {
    "submit_timestamp": 1455882877,
    "build_system_type": "taskcluster",
    "machine_name": "i-a5947c10",
    "job_group_symbol": "tc",
    "job_group_name": "Submitted by taskcluster",
    "platform_option": "opt",
    "job_type_description": "fill me",
    "signature": "3681e7bdec56673c80e85486dcfd66d4e2c57185",
    "result_set_id": 27064,
    "result": "%(result)s",
    "machine_platform_os": "-",
    "ref_data_name": "3681e7bdec56673c80e85486dcfd66d4e2c57185",
    "machine_platform_architecture": "-",
    "end_timestamp": 1455884086,
    "build_platform": "lint",
    "job_guid": "6657633e-a463-4955-bc9c-3a561b236308/0",
    "job_type_name": "[TC] - ESLint",
    "id": 22009433,
    "platform": "lint",
    "state": "%(state)s",
    "job_type_id": 4293,
    "build_os": "-",
    "option_collection_hash": "102210fe594ee9b33d82058545b1ed14f4c8206e",
    "who": "mozilla-taskcluster-maintenance@mozilla.com",
    "failure_classification_id": 1,
    "job_type_symbol": "ES",
    "reason": "scheduled",
    "job_group_description": "fill me",
    "tier": 1,
    "job_coalesced_to_guid": "None",
    "running_eta": 317,
    "start_timestamp": 1455883462,
    "build_architecture": "-",
    "last_modified": "2016-02-19T12:14:47",
    "build_platform_id": 144,
    "job_group_id": 41
  }]
"""

MOCK_ARTIFACTS = """
{
  "artifacts": [
    {
      "storageType": "s3",
      "name": "public/build/buildprops.json",
      "expires": "2016-09-09T07:33:05.268Z",
      "contentType": "application/json"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.langpack.xpi",
      "expires": "2016-09-09T07:31:57.620Z",
      "contentType": "application/x-xpinstall"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.checksums",
      "expires": "2016-09-09T07:32:51.285Z",
      "contentType": "text/plain"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.common.tests.zip",
      "expires": "2016-09-09T07:31:59.953Z",
      "contentType": "application/zip"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.cppunittest.tests.zip",
      "expires": "2016-09-09T07:32:03.353Z",
      "contentType": "application/zip"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.crashreporter-symbols.zip",
      "expires": "2016-09-09T07:32:33.841Z",
      "contentType": "application/zip"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.json",
      "expires": "2016-09-09T07:32:38.501Z",
      "contentType": "application/json"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.mochitest.tests.zip",
      "expires": "2016-09-09T07:32:18.314Z",
      "contentType": "application/zip"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.mozinfo.json",
      "expires": "2016-09-09T07:32:40.213Z",
      "contentType": "application/json"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.reftest.tests.zip",
      "expires": "2016-09-09T07:32:25.971Z",
      "contentType": "application/zip"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.talos.tests.zip",
      "expires": "2016-09-09T07:32:23.389Z",
      "contentType": "application/zip"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.%(suffixes)s",
      "expires": "2016-09-09T07:31:51.823Z",
      "contentType": "application/octet-stream"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.txt",
      "expires": "2016-09-09T07:32:37.564Z",
      "contentType": "text/plain"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.web-platform.tests.zip",
      "expires": "2016-09-09T07:32:29.944Z",
      "contentType": "application/zip"
    },
    {
      "storageType": "s3",
      "name": "public/build/firefox-43.0a1.en-US.%(branch)s.xpcshell.tests.zip",
      "expires": "2016-09-09T07:32:13.594Z",
      "contentType": "application/zip"
    },
    {
      "storageType": "s3",
      "name": "public/build/test_packages.json",
      "expires": "2016-09-09T07:32:41.175Z",
      "contentType": "application/json"
    }
  ]
}
"""


class TestQueries(unittest.TestCase):

    """This class tests the function query_repo_name_from_buildername."""

    @patch('mozci.repositories.query_repositories',
           return_value=json.loads(MOCK_JSON))
    def test_query_repo_name_from_buildername_b2g(self, query_repositories):
        """Test query_repo_name_from_buildername with a b2g job."""
        self.assertEquals(
            mozci.mozci.query_repo_name_from_buildername("b2g_real-repo_win32_gecko build"),
            "real-repo")

    @patch('mozci.repositories.query_repositories',
           return_value=json.loads(MOCK_JSON))
    def test_query_repo_name_form_buildername_normal(self, query_repositories):
        """Test query_repo_name_from_buildername with a normal job."""
        self.assertEquals(
            mozci.mozci.query_repo_name_from_buildername("Linux real-repo opt build"),
            "real-repo")

    @patch('mozci.repositories.query_repositories',
           return_value=json.loads(MOCK_JSON))
    def test_query_repo_name_from_buildername_invalid(self, query_repositories):
        """If no repo name is found at the job, the function should raise an Exception."""
        with pytest.raises(Exception):
            mozci.mozci.query_repo_name_from_buildername("Linux not-a-repo opt build")


class TestJobValidation(unittest.TestCase):
    """Test functions that deal with alljobs."""

    def setUp(self):
        self.alljobs = [
            {'build_id': 64090958,
             'status': 2,
             'branch': 'repo',
             'buildername': 'Platform repo test',
             'claimed_by_name': 'buildbot-releng-path',
             'buildnumber': 16,
             'starttime': 1424960497,
             'requests': [
                 {'complete_at': 1424961882,
                  'complete': 1,
                  'buildername': 'Platform repo test',
                  'claimed_at': 1424961710,
                  'priority': 0,
                  'submittime': 1424960493,
                  'reason': 'Self-serve: Requested by nobody@mozilla.com',
                  'branch': 'repo',
                  'request_id': 62949190,
                  'revision': '4f2decfeb9c5'}],
             'endtime': 1424961882,
             'revision': '4f2decfeb9c5'},
            {'build_id': 63420134,
             'status': 0,
             'branch': 'repo',
             'buildername': 'Platform repo other test',
             'claimed_by_name': 'buildbot-releng-path2',
             'buildnumber': 40,
             'starttime': 1424317413,
             'requests': [
                 {'complete_at': 1424319198,
                  'complete': 1,
                  'buildername': 'Platform repo other test',
                  'claimed_at': 1424318934,
                  'priority': 0,
                  'submittime': 1424314389,
                  'reason': 'scheduler',
                  'branch': 'repo',
                  'request_id': 62279073,
                  'revision': '4f2decfeb9c552c6323525385ccad4b450237e20'}],
             'endtime': 1424319198,
             'revision': u'4f2decfeb9c552c6323525385ccad4b450237e20'}]

        self.jobs = self.alljobs[:1]

    @patch('mozci.query_jobs.BuildApi.get_job_status',
           return_value=SUCCESS)
    def test_status_summary_successful(self, get_status):
        """
        StatusSummary depends on get_job_status that uses query_job_data.

        We will only test StatusSummary with simple mocks of get_job_status here.
        This test is with a success state.
        """
        assert mozci.mozci.StatusSummary(self.jobs).successful_jobs == 1

    @patch('mozci.query_jobs.BuildApi.get_job_status',
           return_value=PENDING)
    def test_status_summary_pending(self, get_status):
        """Test StatusSummary with a running state."""
        assert mozci.mozci.StatusSummary(self.jobs).pending_jobs == 1

    @patch('mozci.query_jobs.BuildApi.get_job_status',
           return_value=RUNNING)
    def test_status_summary_running(self, get_status):
        """Test StatusSummary with a running state."""
        assert mozci.mozci.StatusSummary(self.jobs).running_jobs == 1

    @patch('mozci.query_jobs.BuildApi.get_job_status',
           return_value=COALESCED)
    def test_status_summary_coalesced(self, get_status):
        """Test StatusSummary with a coalesced state."""
        assert mozci.mozci.StatusSummary(self.jobs).coalesced_jobs == 1


class TestTriggerfunctions(unittest.TestCase):
    def setUp(self):
        self.revision = "3681e7bdec56673c80e85486dcfd6"
        self.buildername = "Ubuntu VM 12.04 x64 mozilla-inbound opt test mochitest-1"
        self.taskid = "t1dd870CQsWqlVFB_qo0ag"

    @patch('mozci.sources.tc.get_artifacts',
           return_value=json.loads(MOCK_ARTIFACTS %
                                   {'branch': "linux-x86_64", 'suffixes': "tar.bz2"}))
    def test_find_files_with_tar(self, get_artifacts):
        mock_files = {
            'packageUrl': 'public/build/firefox-43.0a1.en-US.linux-x86_64.'
                          'tar.bz2',
            'testsUrl': 'public/build/test_packages.json'
        }

        self.assertEqual(mozci.mozci._find_files(self.taskid), mock_files)

    @patch('mozci.sources.tc.get_artifacts',
           return_value=json.loads(MOCK_ARTIFACTS %
                                   {'branch': "OSX", 'suffixes': "dmg"}))
    def test_find_files_with_dmg(self, get_artifacts):
        mock_files = {
            'packageUrl': 'public/build/firefox-43.0a1.en-US.OSX.'
                          'dmg',
            'testsUrl': 'public/build/test_packages.json'
        }

        self.assertEqual(mozci.mozci._find_files(self.taskid), mock_files)

    @patch('mozci.sources.tc.get_artifacts',
           return_value=json.loads(MOCK_ARTIFACTS %
                                   {'branch': "android", 'suffixes': "apk"}))
    def test_find_files_with_apk(self, get_artifacts):
        mock_files = {
            'packageUrl': 'public/build/firefox-43.0a1.en-US.android.'
                          'apk',
            'testsUrl': 'public/build/test_packages.json'
        }

        self.assertEqual(mozci.mozci._find_files(self.taskid), mock_files)

#    @patch('mozci.mozci.query_repo_name_from_buildername',
#          return_value="mozilla-inbound")
#    @patch('mozci.platforms.determine_upstream_builder',
#           return_value="Ubuntu VM 12.04 x64")
#    @patch('mozci.mozci.valid_builder', return_value=True)
#    @patch('mozci.query_jobs.TreeherderApi.get_matching_jobs',
#           return_value=json.loads(MOCK_JOBS % {'result': "success", 'state': "completed"}))
#    @patch('mozci.query_jobs.TreeherderApi.get_job_status',
#           return_value=SUCCESS)
