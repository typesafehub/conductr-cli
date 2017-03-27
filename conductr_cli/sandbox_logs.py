import fcntl
import os
import sys
import time

READ_SIZE_KB = 8
FOLLOW_SLEEP_SECONDS = 0.25


def logs(args):
    return tail(log_files(args), args.follow, sys.stdout, READ_SIZE_KB, FOLLOW_SLEEP_SECONDS)


def log_files(args):
    core_log = os.path.abspath('{}/core/logs/conductr.log'.format(args.image_dir))
    agent_log = os.path.abspath('{}/agent/logs/conductr-agent.log'.format(args.image_dir))

    return [core_log, agent_log]


def tail(paths, follow, print_file, read_size_kb, follow_sleep_seconds):
    """
    Reads an array of paths, line-by-line, and sends their contents
    to `print_file`. If `follow` is enabled, emulates UNIX `tail -F`
    (follow-by-name) behavior.

    :param paths: array filesystem paths
    :param follow: boolean whether to follow or not (analogous to tail -F)
    :param print_file: supplied to print() - must have write(string) method
    :param read_size_kb: buffer size for read operations
    :param follow_sleep_seconds: time to wait between polling
    """

    def empty_file(path):
        return {'path': p, 'file': False, 'size': 0, 'buffer': ''}

    # opens a path and sets non-blocking flags on it
    def do_open(path):
        try:
            file = open(p, 'r')
            fd = file.fileno()
            flag = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)

            return {'path': path, 'file': file, 'size': os.path.getsize(path), 'buffer': ''}
        except:
            return empty_file(path)

    def do_read(files):
        done = True

        for i, f in enumerate(files):
            try:
                if not f['file'] or os.path.getsize(f['path']) < f['size']:
                    f = do_open(f['path'])

                if f['file']:
                    data = f['file'].read(read_size_kb * 1024)

                    if len(data) > 0:
                        f['buffer'] += data
                        done = False

                files[i] = f
            except:
                files[i] = empty_file(f['path'])

        return done, files

    def do_output(files):
        for f in files:
            if len(f['buffer']) > 0:
                ends_on_line = f['buffer'][-1] == '\n'

                lines = f['buffer'].splitlines()
                num_lines = len(lines)

                for i, line in enumerate(lines):
                    if ends_on_line or i < num_lines - 1:
                        print(line, file=print_file)

                if ends_on_line:
                    f['buffer'] = ''
                else:
                    f['buffer'] = lines[-1]

    # we pass through the entire log files one by one (i.e. not interleaved).
    # once completed, if following is enabled, interleave files as data is appended

    files = []

    for p in paths:
        f = do_open(p)

        full_done = False

        while not full_done:
            full_done, fs = do_read([f])

            f = fs[0]

            do_output([f])

        files.append(f)

    if follow:
        while True:
            _, files = do_read(files)

            do_output(files)

            time.sleep(follow_sleep_seconds)
