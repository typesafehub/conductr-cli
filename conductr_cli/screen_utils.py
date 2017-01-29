import textwrap

BORDER_CHAR = '|'
H1_CHAR = '-'
H2_CHAR = '- '
SEPARATION_CHAR = ' '
LOADING_CHAR = '#'
DEFAULT_BAR_LENGTH = 50


def calc_column_widths(data):
    column_widths = {}
    for row in data:
        for column, value in row.items():
            column_len = len(str(value))
            width_key = column + '_width'
            if column_len > column_widths.get(width_key, 0):
                column_widths[width_key] = column_len
    return column_widths


def progress_bar(current_size, total_size, bar_length=50):
    if current_size <= total_size:
        percent = int(current_size * 100 / total_size)
    else:
        percent = 100

    def progress_character(number):
        if number * (100 / bar_length) <= percent:
            return LOADING_CHAR
        else:
            return SEPARATION_CHAR

    progress = ''.join([progress_character(i) for i in range(1, bar_length)])
    return '[{}] {}'.format(progress, '%3d%%' % percent)


def h1(text, bar_length=DEFAULT_BAR_LENGTH):
    return headline(text, H1_CHAR, bar_length)


def h2(text, bar_length=DEFAULT_BAR_LENGTH):
    return headline(text, H2_CHAR, bar_length)


def headline(text, headline_char, bar_length):
    def format_text_line(line):
        filling_whitespaces = max_text_length - len(line)
        return \
            BORDER_CHAR + SEPARATION_CHAR + \
            line + (SEPARATION_CHAR * filling_whitespaces) + \
            SEPARATION_CHAR + BORDER_CHAR
    center_length = bar_length - 2
    center_chars = int(center_length / len(headline_char)) * headline_char
    if len(center_chars) < center_length:
        center_chars += headline_char[:(center_length - len(center_chars))]
    separation_line = BORDER_CHAR + center_chars + BORDER_CHAR
    max_text_length = bar_length - 4
    text_lines = textwrap.wrap(text, max_text_length)
    text_lines = [format_text_line(text_line) for text_line in text_lines]
    return \
        separation_line + '\n' + \
        '\n'.join(text_lines) + '\n' + \
        separation_line
