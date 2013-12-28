# Copyright 2009-2013 Justin Riley
#
# This file is part of StarCluster.
#
# StarCluster is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# StarCluster is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with StarCluster. If not, see <http://www.gnu.org/licenses/>.

"""
Based on StarCluster logging module
"""
import os
import sys
import types
import logging
import logging.handlers
import textwrap
import datetime

INFO = logging.INFO
DEBUG = logging.DEBUG
WARN = logging.WARN
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
FATAL = logging.FATAL
RAW = "raw"

RAW_FORMAT = "%(message)s"
INFO_FORMAT = " ".join([">>>", RAW_FORMAT])
DEFAULT_CONSOLE_FORMAT = " - ".join(["%(levelname)s", RAW_FORMAT])
ERROR_CONSOLE_FORMAT = " ".join(["!!!", DEFAULT_CONSOLE_FORMAT])
WARN_CONSOLE_FORMAT = " ".join(["***", DEFAULT_CONSOLE_FORMAT])
FILE_INFO_FORMAT = " - ".join(["%(filename)s:%(lineno)d",
                               DEFAULT_CONSOLE_FORMAT])
DEBUG_FORMAT = " ".join(["%(asctime)s", FILE_INFO_FORMAT])

class ConsoleLogger(logging.StreamHandler):

    formatters = {
        INFO: logging.Formatter(INFO_FORMAT),
        DEBUG: logging.Formatter(DEBUG_FORMAT),
        WARN: logging.Formatter(WARN_CONSOLE_FORMAT),
        ERROR: logging.Formatter(ERROR_CONSOLE_FORMAT),
        CRITICAL: logging.Formatter(ERROR_CONSOLE_FORMAT),
        FATAL: logging.Formatter(ERROR_CONSOLE_FORMAT),
        RAW: logging.Formatter(RAW_FORMAT),
    }

    def __init__(self, stream=sys.stdout, error_stream=sys.stderr):
        self.error_stream = error_stream or sys.stderr
        logging.StreamHandler.__init__(self, stream or sys.stdout)

    def format(self, record):
        if hasattr(record, '__raw__'):
            result = self.formatters[RAW].format(record)
        else:
            result = self.formatters[record.levelno].format(record)
        return result

    def _wrap(self, msg):
        tw = textwrap.TextWrapper(width=60, replace_whitespace=False)
        if hasattr(tw, 'break_on_hyphens'):
            tw.break_on_hyphens = False
        if hasattr(tw, 'drop_whitespace'):
            tw.drop_whitespace = True
        return tw.wrap(msg) or ['']

    def _emit_textwrap(self, record):
        lines = []
        for line in record.msg.splitlines():
            lines.extend(self._wrap(line))
        if hasattr(record, '__nosplitlines__'):
            lines = ['\n'.join(lines)]
        for line in lines:
            record.msg = line
            self._emit(record)

    def _emit(self, record):
        msg = self.format(record)
        fs = "%s\n"
        if hasattr(record, '__nonewline__'):
            msg = msg.rstrip()
            fs = "%s"
        stream = self.stream
        if record.levelno in [ERROR, CRITICAL, FATAL]:
            stream = self.error_stream
        if not hasattr(types, "UnicodeType"):
             # if no unicode support...
            stream.write(fs % msg)
        else:
            try:
                stream.write(fs % msg)
            except UnicodeError:
                stream.write(fs % msg.encode("UTF-8"))
        self.flush()

    def emit(self, record):
        try:
            if hasattr(record, '__textwrap__'):
                self._emit_textwrap(record)
            else:
                self._emit(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class NullHandler(logging.Handler):
    def emit(self, record):
        pass



now = datetime.datetime.utcnow().strftime('%Y-%m-%d')
DOTO_CFG_DIR = os.path.join(os.path.expanduser('~'), '.doto-logs')
DOTO_LOG_DIR = os.path.join(DOTO_CFG_DIR, 'logs')
DEBUG_FILE = os.path.join(DOTO_LOG_DIR, 'debug-%s.log' % (now))

def __makedirs(path, exit_on_failure=False):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            if exit_on_failure:
                sys.stderr.write("!!! ERROR - %s *must* be a directory\n" %
                                 path)
    elif not os.path.isdir(path) and exit_on_failure:
        sys.stderr.write("!!! ERROR - %s *must* be a directory\n" % path)
        sys.exit(1)

def create_log_config_dirs():
    __makedirs(DOTO_CFG_DIR, exit_on_failure=True)
    __makedirs(DOTO_LOG_DIR)

def get_doto_logger():
    log = logging.getLogger('doto')
    log.addHandler(NullHandler())
    return log

log = get_doto_logger()
console = ConsoleLogger()

def configure_doto_logging(use_syslog=False,filename=''):
    """
    Configure logging for StarCluster *application* code

    By default StarCluster's logger has no formatters and a NullHandler so that
    other developers using StarCluster as a library can configure logging as
    they see fit. This method is used in StarCluster's application code (i.e.
    the 'starcluster' command) to toggle StarCluster's application specific
    formatters/handlers

    use_syslog - enable logging all messages to syslog. currently only works if
    /dev/log exists on the system (standard for most Linux distros)
    """
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter(DEBUG_FORMAT)
    create_log_config_dirs()
    if filename:
        rfh = logging.FileHandler(filename)
    else:
        rfh = logging.handlers.RotatingFileHandler(DEBUG_FILE,
                                               maxBytes=1048576,
                                               backupCount=2)

    rfh.setLevel(logging.DEBUG)
    rfh.setFormatter(formatter)
    log.addHandler(rfh)
    console.setLevel(logging.INFO)
    log.addHandler(console)
    syslog_device = '/dev/log'
    if use_syslog and os.path.exists(syslog_device):
        log.debug("Logging to %s" % syslog_device)
        syslog_handler = logging.handlers.SysLogHandler(address=syslog_device)
        syslog_handler.setFormatter(formatter)
        syslog_handler.setLevel(logging.DEBUG)
        log.addHandler(syslog_handler)


configure_doto_logging()