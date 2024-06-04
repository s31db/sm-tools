from string import ascii_letters, digits


def r(s):
    return "" if s is None or str(s) == "None" else str(s)


def str_file(title):
    valid_chars = "-_.() %s%s" % (ascii_letters, digits)
    filename = "".join(c for c in title if c in valid_chars)
    return filename.replace(" ", "_")
