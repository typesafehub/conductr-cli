# print to stderr
def error(message, *objs):
    print("ERROR:", message.format(*objs), file=sys.stderr)
