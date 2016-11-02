import sys
import os
import time
import stat

def btransfer(src, dst, on_write_event, block_size):

    def open_targets():
        tsrc = None
        tdst = None
        if not os.path.exists(src):
            Exception("Input source does not exist")
        else:
            try:
                tsrc = open(src, 'rb')
            except IOError:
                raise Exception("Input source can not open")

        if os.path.exists(dst):
            mode = os.stat(dst).st_mode
            if stat.S_ISBLK(mode):
                tdst = open(dst, 'ab')
            else:
                tdst = open(dst, 'wb')
        else:
            dst_dir = os.path.abspath(os.path.dirname(dst))
            if os.path.isdir(dst_dir):
                tdst = open(dst, 'wb')
            else:
                Exception("Dir for output destination does not exist")

        return (tsrc, tdst)


    def close_targets(targets):
        for t in targets:
            t.close()


    def copy_data(tsrc, tdst):
        st = time.time()
        tsrc_size = os.stat(src).st_size
        buff = tsrc.read(block_size)
        blocks = 0
        totsze = 0
        while buff:
            if totsze <= tsrc_size or tsrc_size == -1:
                tdst.write(buff)
                blocks += 1
                totsze += len(buff)
                if tsrc_size != -1:
                    on_write_event(tsrc_size, totsze, st)
                else:
                    on_write_event(None, totsze, st)
                buff = tsrc.read(block_size)
            else:
                buff = None

    (s, d) = open_targets()
    copy_data(s, d)
    close_targets((s, d))

def pro(a,b,c):
    # Here you could write your progress bar or update
    # any ui variable related to a ui control
    # This handler should be outside from this file
    # when using it seriouslly :p
    pass

if __name__ == '__main__':
    try:
        btransfer('/home/j4nusx/Downloads/Windows_8.1_Pro_X64_Activated.iso', '../../../tmp/test.iso', pro, 40960)
    except Exception as e:
        print(e.message)
