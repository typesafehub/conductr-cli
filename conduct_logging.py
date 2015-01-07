import json
import sys


# print to stderr
def error(message, *objs):
    print("ERROR:", message.format(*objs), file=sys.stderr)


def pretty_json(s):
    s_json = json.loads(s)
    print(json.dumps(s_json, sort_keys=True, indent=2))
