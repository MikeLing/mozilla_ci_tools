#!/usr/bin/env python
"""
This module helps with the buildjson data generated by the Release Engineering
systems: http://builddata.pub.build.mozilla.org/builddata/buildjson
"""
import logging
import os

from mozci.utils.tzone import utc_dt, utc_time, utc_day
from mozci.utils.transfer import load_file, path_to_file

LOG = logging.getLogger('mozci')

BUILDJSON_DATA = "http://builddata.pub.build.mozilla.org/builddata/buildjson"
BUILDS_4HR_FILE = "builds-4hr.js"
BUILDS_DAY_FILE = "builds-%s.js"

# This helps us read into memory and load less from disk
BUILDS_CACHE = {}


class BuildjsonException(Exception):
    pass


def _fetch_data(filename):
    """
    Helper method to fetch the buildjson data we need.

    This function caches the uncompressed gzip files requested in the past.

    Returns all jobs inside of this buildjson file.
    """
    global BUILDS_CACHE
    if filename in BUILDS_CACHE:
        return BUILDS_CACHE[filename]
    url = "%s/%s.gz" % (BUILDJSON_DATA, filename)

    if not os.path.isabs(filename):
        filepath = path_to_file(filename)
    else:
        filepath = filename

    # If the file exists and is valid we won't download it again
    json_contents = load_file(filepath, url)
    BUILDS_CACHE[filename] = json_contents["builds"]
    return json_contents["builds"]


def _find_job(request_id, jobs, loaded_from):
    """
    Look for request_id in a list of jobs.

    loaded_from is simply to indicate where those jobs were loaded from.
    """
    LOG.debug("We are going to look for %s in %s." % (request_id, loaded_from))

    for job in jobs:
        # XXX: Issue 104 - We have an unclear source of request ids
        prop_req_ids = job["properties"].get("request_ids", [])
        root_req_ids = job["request_ids"]
        if request_id in list(set(prop_req_ids + root_req_ids)):
            return job

    return None


def query_job_data(complete_at, request_id):
    """
    Look for a job identified by `request_id` inside of a buildjson
    file under the "builds" entry.

    Through `complete_at`, we can determine on which day we can find the
    metadata about this job.

    raises BuildjsonException when we can't find the job.

    WARNING: "request_ids" and the ones from "properties" can differ. Issue filed.

    If found, the returning entry will look like this (only important values
    are referenced):

    .. code-block:: python

        {
            "builder_id": int, # It is a unique identifier of a builder
            "starttime": int,
            "endtime": int,
            "properties": {
                "blobber_files": json, # Mainly applicable to test jobs
                "buildername": string,
                "buildid": string,
                "log_url", string,
                "packageUrl": string, # It only applies for build jobs
                "revision": string,
                "repo_path": string, # e.g. projects/cedar
                "request_ids": list of ints, # Scheduling ID
                "slavename": string, # e.g. t-w864-ix-120
                "symbolsUrl": string, # It only applies for build jobs
                "testsUrl": string,   # It only applies for build jobs
            },
            "request_ids": list of ints, # Scheduling ID
            "requesttime": int,
            "result": int, # Job's exit code
            "slave_id": int, # Unique identifier for the machine that run it
        }

    NOTE: Remove this block once https://bugzilla.mozilla.org/show_bug.cgi?id=1135991
    is fixed.

    There is so funkiness in here. A buildjson file for a day is produced
    every 15 minutes all the way until midnight pacific time. After that, a new
    _UTC_ day commences. However, we will only contain all jobs ending within the
    UTC day and not the PT day. If you run any of this code in the last 4 hours of
    the pacific day, you will have a gap of 4 hours for which you won't have buildjson
    data (between 4-8pm PT). The gap starts appearing after 8pm PT when builds-4hr
    cannot cover it.

    If we look all endtime values on a day and we print the minimum and maximum values,
    this is what we get:

    .. code-block:: python

        1424649600 Mon, 23 Feb 2015 00:00:00  () Sun, 22 Feb 2015 16:00:00 -0800 (PST)
        1424736000 Tue, 24 Feb 2015 00:00:00  () Mon, 23 Feb 2015 16:00:00 -0800 (PST)

    This means that since 4pm to midnight we generate the same file again and again
    without adding any new data.
    """
    global BUILDS_CACHE

    assert type(request_id) is int
    assert type(complete_at) is int

    date = utc_day(complete_at)
    LOG.debug("Job identified with complete_at value: %d run on %s UTC." % (complete_at, date))

    then = utc_dt(complete_at)
    hours_ago = (utc_dt() - then).total_seconds() / (60 * 60)
    LOG.debug("The job completed at %s (%d hours ago)." % (utc_time(complete_at), hours_ago))

    # If it has finished in the last 4 hours
    if hours_ago < 4:
        # We might be able to grab information about pending and running jobs
        # from builds-running.js and builds-pending.js
        filename = BUILDS_4HR_FILE
    else:
        filename = BUILDS_DAY_FILE % date
    job = _find_job(request_id, _fetch_data(filename), filename)

    if job:
        return job

    # If we have not found the job, it might be that our cache for this
    # file is old. We will clean the cache and try one more time. If
    # it fails, we will raise an Exception
    LOG.debug("We did not find %d in %s, we'll clear our cache and try again."
              % (request_id, filename))
    del BUILDS_CACHE[filename]

    job = _find_job(request_id, _fetch_data(filename), filename)
    if job:
        return job

    raise BuildjsonException(
        "We have not found the job. If you see this problem please grep "
        "in %s for %d and run again with --debug and --dry-run. If you report "
        "this issue please upload the mentioned file somewhere for "
        "inspection. Thanks!" % (filename, request_id))
