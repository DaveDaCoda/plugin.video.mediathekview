# -*- coding: utf-8 -*-
"""
Utilities module

Copyright (c) 2017-2018, Leo Moll
Licensed under MIT License
"""

from __future__ import unicode_literals

import os
import sys
import stat
import string

import urllib
import urllib2

from contextlib import closing
from resources.lib.exceptions import ExitRequested

# -- Kodi Specific Imports ----------------------------------
try:
    import xbmcvfs
    IS_KODI = True
except ImportError:
    IS_KODI = False


def dir_exists(name):
    """
    Tests if a directory exists

    Args:
        name(str): full pathname of the directory
    """
    try:
        state = os.stat(name)
        return stat.S_ISDIR(state.st_mode)
    except OSError:
        return False


def file_exists(name):
    """
    Tests if a file exists

    Args:
        name(str): full pathname of the file
    """
    try:
        state = os.stat(name)
        return stat.S_ISREG(state.st_mode)
    except OSError:
        return False


def file_size(name):
    """
    Get the size of a file

    Args:
        name(str): full pathname of the file
    """
    try:
        state = os.stat(name)
        return state.st_size
    except OSError:
        return 0


def file_remove(name):
    """
    Delete a file

    Args:
        name(str): full pathname of the file
    """
    if file_exists(name):
        try:
            os.remove(name)
            return True
        except OSError:
            pass
    return False


def find_xz():
    """
    Return the full pathname to the xz decompressor
    executable
    """
    for xzbin in ['/bin/xz', '/usr/bin/xz', '/usr/local/bin/xz']:
        if file_exists(xzbin):
            return xzbin
    return None


def make_search_string(val):
    """
    Reduces a string to a simplified representation
    containing only a well defined set of characters
    for a simplified search
    """
    cset = string.letters + string.digits + ' _-#'
    search = ''.join([c for c in val if c in cset])
    return search.upper().strip()


def make_duration(val):
    """
    Converts a string in `hh:mm:ss` representation
    to the equivalent number of seconds

    Args:
        val(str): input string in format `hh:mm:ss`
    """
    if val == "00:00:00":
        return None
    elif val is None:
        return None
    parts = val.split(':')
    if len(parts) != 3:
        return None
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


def cleanup_filename(val):
    """
    Strips strange characters from a string in order
    to create a valid filename

    Args:
        val(str): input string
    """
    cset = string.letters + string.digits + \
        u' _-#äöüÄÖÜßáàâéèêíìîóòôúùûÁÀÉÈÍÌÓÒÚÙçÇœ'
    search = ''.join([c for c in val if c in cset])
    return search.strip()


def url_retrieve(url, filename, reporthook, chunk_size=8192, aborthook=None):
    """
    Copy a network object denoted by a URL to a local file

    Args:
        url(str): the source url of the object to retrieve

        filename(str): the destination filename

        reporthook(function): a hook function that will be called once on
            establishment of the network connection and once after each
            block read thereafter. The hook will be passed three arguments;
            a count of blocks transferred so far, a block size in bytes,
            and the total size of the file.

        chunk_size(int, optional): size of the chunks read by the function.
            Default is 8192

        aborthook(function, optional): a hook function that will be called
            once on establishment of the network connection and once after
            each block read thereafter. If specified the operation will be
            aborted if the hook function returns `True`
    """
    with closing(urllib2.urlopen(url)) as src, closing(open(filename, 'wb')) as dst:
        _chunked_url_copier(src, dst, reporthook, chunk_size, aborthook)


def url_retrieve_vfs(url, filename, reporthook, chunk_size=8192, aborthook=None):
    """
    Copy a network object denoted by a URL to a local file using
    Kodi's VFS functions

    Args:
        url(str): the source url of the object to retrieve

        filename(str): the destination filename

        reporthook(function): a hook function that will be called once on
            establishment of the network connection and once after each
            block read thereafter. The hook will be passed three arguments;
            a count of blocks transferred so far, a block size in bytes,
            and the total size of the file.

        chunk_size(int, optional): size of the chunks read by the function.
            Default is 8192

        aborthook(function, optional): a hook function that will be called
            once on establishment of the network connection and once after
            each block read thereafter. If specified the operation will be
            aborted if the hook function returns `True`
    """
    with closing(urllib2.urlopen(url)) as src, closing(xbmcvfs.File(filename, 'wb')) as dst:
        _chunked_url_copier(src, dst, reporthook, chunk_size, aborthook)


def build_url(query):
    """
    Builds a valid plugin url based on the supplied query object

    Args:
        query(object): a query object
    """
    return sys.argv[0] + '?' + urllib.urlencode(query)


def _chunked_url_copier(src, dst, reporthook, chunk_size, aborthook):
    aborthook = aborthook if aborthook is not None else lambda: False
    total_size = int(
        src.info().getheader('Content-Length').strip()
    ) if src.info() and src.info().getheader('Content-Length') else 0
    total_chunks = 0

    while not aborthook():
        reporthook(total_chunks, chunk_size, total_size)
        chunk = src.read(chunk_size)
        if not chunk:
            # operation has finished
            return
        dst.write(chunk)
        total_chunks += 1
    # abort requested
    raise ExitRequested('Reception interrupted.')
