import json


# print to stderr
def error(message, *objs):
    print("ERROR:", message.format(*objs), file=sys.stderr)

def pretty_json(message):
    message_json = json.loads(message)
    print(json.dumps(message_json, sort_keys=True, indent=2))
