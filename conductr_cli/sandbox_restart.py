from conductr_cli.sandbox_common import LATEST_SANDBOX_RUN_ARGS_FILE
import conductr_cli
from conductr_cli import validation


@validation.handle_sandbox_restart_error
def restart(args):
    """`sandbox restart` command"""
    with open(LATEST_SANDBOX_RUN_ARGS_FILE, 'r') as f:
        run_args = f.read()
    conductr_cli.sandbox_main.run(['stop'], configure_logging=False)
    conductr_cli.sandbox_main.run(['run'] + run_args.split(' '), configure_logging=False)
    return True
