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
            return '#'
        else:
            return ' '

    progress = ''.join([progress_character(i) for i in range(1, bar_length)])
    return '[{}] {}'.format(progress, '%3d%%' % percent)
