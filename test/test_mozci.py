"""This file contains tests for mozci/mozci.py."""

import json
import pytest
import unittest

from helpers import (
    ALLTHETHINGS
)

from mozci.mozci import (
    StatusSummary,
    valid_builder,
    query_repo_name_from_buildername,
)
from mozci.query_jobs import SUCCESS, PENDING, RUNNING, COALESCED

from mock import patch


MOCK_JSON = '''{
    "real-repo": {
        "repo": "https://hg.mozilla.org/integration/real-repo",
        "graph_branches": ["Real-Repo"],
        "repo_type": "hg"
    }
}'''


class TestQueries(unittest.TestCase):

    """This class tests the function query_repo_name_from_buildername."""

    @patch('mozci.repositories.query_repositories',
           return_value=json.loads(MOCK_JSON))
    def test_query_repo_name_from_buildername_b2g(self, query_repositories):
        """Test query_repo_name_from_buildername with a b2g job."""
        assert query_repo_name_from_buildername("b2g_real-repo_win32_gecko build") == "real-repo"

    @patch('mozci.repositories.query_repositories',
           return_value=json.loads(MOCK_JSON))
    def test_query_repo_name_form_buildername_normal(self, query_repositories):
        """Test query_repo_name_from_buildername with a normal job."""
        assert query_repo_name_from_buildername("Linux real-repo opt build") == "real-repo"

    @patch('mozci.repositories.query_repositories',
           return_value=json.loads(MOCK_JSON))
    def test_query_repo_name_from_buildername_invalid(self, query_repositories):
        """If no repo name is found at the job, the function should raise an Exception."""
        with pytest.raises(Exception):
            query_repo_name_from_buildername("Linux not-a-repo opt build")


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
        assert StatusSummary(self.jobs).successful_jobs == 1

    @patch('mozci.query_jobs.BuildApi.get_job_status',
           return_value=PENDING)
    def test_status_summary_pending(self, get_status):
        """Test StatusSummary with a running state."""
        assert StatusSummary(self.jobs).pending_jobs == 1

    @patch('mozci.query_jobs.BuildApi.get_job_status',
           return_value=RUNNING)
    def test_status_summary_running(self, get_status):
        """Test StatusSummary with a running state."""
        assert StatusSummary(self.jobs).running_jobs == 1

    @patch('mozci.query_jobs.BuildApi.get_job_status',
           return_value=COALESCED)
    def test_status_summary_coalesced(self, get_status):
        """Test StatusSummary with a coalesced state."""
        assert StatusSummary(self.jobs).coalesced_jobs == 1

    @patch('mozci.platforms.fetch_allthethings_data')
    def test_valid_builder(self, fetch_allthethings_data):
        fetch_allthethings_data.return_value = ALLTHETHINGS
        buildername = 'Windows XP 32-bit mozilla-inbound pgo test mochitest-browser-chrome-1'
        assert valid_builder(buildername)
