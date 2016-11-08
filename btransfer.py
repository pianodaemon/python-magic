import abc
import os
import time
import stat
import logging
from urllib.parse import urlparse


class Target(object):

    __metaclass__ = abc.ABCMeta
    uri_parsed = None

    def __init__(self, uri_parsed):
        self.uri_parsed = uri_parsed

    @abc.abstractmethod
    def open(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass

    @abc.abstractmethod
    def read(self):
        pass

    @abc.abstractmethod
    def write(self, buff):
        pass

    @abc.abstractmethod
    def size(self):
        pass


class BTransError(Exception):
    def __init__(self, message = None):
        self.message = message
    def __str__(self):
        return self.message


class BTransSupplierError(BTransError):
    def __init__(self, message = None, target = None):
        self.target = target
        super().__init__(message = message)


class HttpITarget(Target):
    import urllib.request

    def __init__(self, uri_parsed , *args, **kwargs):
        super().__init__(uri_parsed)
        self.__logger = logging.getLogger(__name__)

    def size(self):
        req = urllib.request.Request(self.__turl, method="HEAD")
        resp = urllib.request.urlopen(req)
        num_bytes = resp.info().get('content-length')
        return num_bytes

class FileITarget(Target):

    # A default Block segment of 4KB
    __BS = 4960

    __tfd = -1

    def __init__(self, uri_parsed , *args, **kwargs):
        super().__init__(uri_parsed)
        self.__logger = logging.getLogger(__name__)
        self.__check_form()
        self.__mode = os.stat(self.uri_parsed.path).st_mode

    def size(self):
        if not stat.S_ISBLK(self.__mode):
            return self.__size_regular_file()
        else:
            return self.__size_block_device()


    def open(self):
        try:
            self.__tfd = open(self.uri_parsed.path, 'rb')
        except IOError:
            raise BTransError("Input URI can not open")


    def close(self):
        self.__tfd.close()


    def read(self):
        return self.__tfd.read(self.__BS)


    def write(self, buff):
        raise NotImplementedError(
            "Writting methods are not implemented upon input targets"
        )

    def __check_form(self):
        if self.uri_parsed.scheme == 'file':
            pass
        else:
            raise BTransError(
                "File URI fed does not abide with the form 'file://host/path'"
            )
        if not os.path.exists(self.uri_parsed.path):
            raise BTransError("Input URI does not exist")


    def __size_regular_file(self):
        tfs = os.stat(self.uri_parsed.path).st_size
        if tfs == -1:
            raise BTransError("Input URI can not be sized")
        return tfs


    def __size_block_device(self):
        if self.__tfd == -1:
            raise BTransError("Input URI can not be sized")
        tfs = os.lseek(self.__tfd, os.SEEK_SET, os.SEEK_END)
        return tfs



class FileOTarget(Target):

    new_file = False

    def __init__(self, uri_parsed , *args, **kwargs):
        super().__init__(uri_parsed)
        self.__logger = logging.getLogger(__name__)

        if self.uri_parsed.scheme == 'file':
            pass
        else:
            raise BTransError(
                "File URI fed does not abide with the form 'file://host/path'"
            )
        if os.path.exists(self.uri_parsed.path):
            self.__mode = os.stat(self.uri_parsed.path).st_mode
        else:
            self.new_file = True


    def size(self):
        if self.new_file:
            return 0
        else:
            if not stat.S_ISBLK(self.__mode):
                tfs = os.stat(self.uri_parsed.path).st_size
                if tfs == -1:
                    raise BTransError("Input URI can not be sized")
                return tfs
            else:
                return self.__size_block_device()


    def open(self):
        try:
            if self.new_file:
                pass
            else:
                if stat.S_ISBLK(self.__mode):
                    self.__tfd = open(self.uri_parsed.path, 'ab')
                    return
            self.__tfd = open(self.uri_parsed.path, 'wb')
        except IOError:
            raise BTransError("Output URI can not open")


    def close(self):
        self.__tfd.close()

    def read(self):
        raise NotImplementedError(
            "Reading methods are not implemented upon output targets"
        )

    def write(self, buff):
        self.__tfd.write(buff)

    def __size_block_device(self):
        if self.__tfd == -1:
            raise BTransError("Output URI can not be sized")
        tfs = os.lseek(self.__tfd, os.SEEK_SET, os.SEEK_END)
        return tfs


class TargetSupplier(object):

    IN_SENSE, OUT_SENSE = range(2)

    __SUPPORTED = {
        "file": [
            FileITarget,
            FileOTarget
        ]
    }

    @staticmethod
    def get(flow_sense, uri, *args, **kwargs):

        def resolve(n):
            supported = TargetSupplier.__SUPPORTED.get(n.scheme.lower(), None)
            if supported:
                ic = None
                try:
                    ic = supported[flow_sense]
                    return ic(n, *args, **kwargs)
                except KeyError:
                    raise BTransSupplierError("Such flow sense is not supported")
            else:
                raise BTransSupplierError("Such uri is not supported yet")

        uri_parsed = urlparse(uri)
        return resolve(uri_parsed)


def btrans(src_uri, dst_uri, on_write_event):

    def fetch_ts():
        return (
            TargetSupplier.get(TargetSupplier.IN_SENSE, src_uri),
            TargetSupplier.get(TargetSupplier.OUT_SENSE, dst_uri)
        )

    def open_ts(ts):
        for t in ts:
            t.open()

    def close_ts(ts):
        for t in ts:
            t.close()

    def copy(ts):
        start = time.time()
        tsrc_size = ts[TargetSupplier.IN_SENSE].size()
        buff = ts[TargetSupplier.IN_SENSE].read()
        blocks = 0
        totsze = 0
        while buff:
            if totsze <= tsrc_size:
                ts[TargetSupplier.OUT_SENSE].write(buff)
                blocks += 1
                totsze += len(buff)
                on_write_event(tsrc_size, totsze, start)
                buff = ts[TargetSupplier.IN_SENSE].read()
            else:
                buff = None

    ts = None
    try:
        ts = fetch_ts()
        open_ts(ts)
        copy(ts)
        close_ts(ts)
    except (BTransError, BTransSupplierError) as e:
        raise
    except:
        raise BTransError("An unexpected exception happened")


def pro(a,b,c):
    # Here you could write your progress bar or update
    # any ui variable related to a ui control
    # This handler should be outside from this file
    # when using it seriouslly :p
    pass

if __name__ == '__main__':
    try:
        btrans('file:///home/pianodaemon/BORRAME/FreeBSD-10.1-RELEASE-i386-memstick.img', 'file:///home/pianodaemon/BORRAME/test.iso', pro)
    except BTransError as e:
        print(e.message)
