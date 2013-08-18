# Copyright 2013 Hynek Schlawack
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

from __future__ import absolute_import, division, print_function

import datetime
import json
import sys
import traceback

from structlog._compat import StringIO, unicode_type


def render_kv(_, __, event_dict):
    """
    Render `event_dict` as a list of `Key=Value` pairs.
    """
    return ' '.join(k + '=' + repr(v) for k, v in sorted(event_dict.items()))


class UnicodeEncoder(object):
    """
    Encode unicode values in `event_dict`.
    """
    def __init__(self, encoding='utf-8', errors='backslashreplace'):
        self._encoding = encoding
        self._errors = errors

    def __call__(self, logger, name, event_dict):
        for key, value in event_dict.items():
            if isinstance(value, unicode_type):
                event_dict[key] = value.encode(self._encoding, self._errors)
        return event_dict


class JSONRenderer(object):
    """
    Render the `event_dict` using `json.dumps(even_dict, **json_kw)`.
    """
    def __init__(self, **json_kw):
        self._json_kw = json_kw

    def __call__(self, logger, name, event_dict):
        return json.dumps(event_dict, cls=_ReprFallbackEncoder,
                          **self._json_kw)


class _ReprFallbackEncoder(json.JSONEncoder):
    """
    A JSONEncoder that will use the repr(obj) as the default serialization
    for objects that the base JSONEncoder does not know about.

    This will ensure that even log messages that include unserializable objects
    (like from 3rd party libraries) will still have reasonable representations
    in the logged JSON and will actually be logged and not discarded by the
    logging system because of a formatting error.

    Shamelessly stolen from Rackspace's otter.
    """
    def default(self, obj):
        """
        Serialize obj as repr(obj).
        """
        return repr(obj)


def add_timestamp(logger, name, event_dict):
    """
    Add an UTC timestamp to `event_dict`.
    """
    event_dict['timestamp'] = datetime.datetime.utcnow()
    return event_dict


def format_exc_info(logger, name, event_dict):
    """
    Replace an `exc_info` field by an `exception` string field:

    - if `exc_info` is a tuple, render it
    - if `exc_info` is true, obtain exc_info ourselve and render that
    """
    exc_info = event_dict.pop('exc_info', None)
    if exc_info:
        if not isinstance(exc_info, tuple):
            exc_info = sys.exc_info()
        event_dict['exception'] = _format_exception(exc_info)
    return event_dict


def _format_exception(exc_info):
    """
    Prettyprint an `exc_info` tuple.

    Shamelessly stolen from stdlib's logging module.
    """
    sio = StringIO()
    traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], None, sio)
    s = sio.getvalue()
    sio.close()
    if s[-1:] == "\n":
        s = s[:-1]
    return s
