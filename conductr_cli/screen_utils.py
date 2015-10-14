def calc_column_widths(data):
    column_widths = {}
    for row in data:
        for column, value in row.items():
            column_len = len(str(value))
            width_key = column + '_width'
            if column_len > column_widths.get(width_key, 0):
                column_widths[width_key] = column_len
    return column_widths
