import os


def logs_args(args):
    core_log = os.path.abspath('{}/core/logs/conductr.log'.format(args.image_dir))
    agent_log = os.path.abspath('{}/agent/logs/conductr-agent.log'.format(args.image_dir))

    tail_args = ['/usr/bin/env', 'tail', '-q']

    if args.follow:
        tail_args.append('-f')
        tail_args.append('--follow=name')
        tail_args.append('--retry')

    if args.lines:
        tail_args.append('-n')
        tail_args.append(str(args.lines))

    tail_args.append(core_log)
    tail_args.append(agent_log)

    return tail_args


def logs(args):
    os.execv('/usr/bin/env', logs_args(args))
