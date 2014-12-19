import conduct_run


# `conduct stop` command
def stop(args):
    args.scale = 0
    conduct_run.run(args)
