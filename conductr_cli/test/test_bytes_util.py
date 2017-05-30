# Copyright (c) 2010 Jason Moiron and Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from unittest import TestCase
from conductr_cli import bytes_util


class TestBytesUtil(TestCase):
    def test_natural_size(self):
        tests_and_expected_results = [
            (300, '300 Bytes'),
            (3000, '3.0 kB'),
            (3000000, '3.0 MB'),
            (3000000000, '3.0 GB'),
            (3000000000000, '3.0 TB'),
            ((300, True), '300 Bytes'),
            ((3000, True), '2.9 KiB'),
            ((3000000, True), '2.9 MiB'),
            ((300, False, True), '300B'),
            ((3000, False, True), '2.9K'),
            ((3000000, False, True), '2.9M'),
            ((1024, False, True), '1.0K'),
            ((10**26 * 30, False, True), '2481.5Y'),
            ((10**26 * 30, True), '2481.5 YiB'),
            (10**26 * 30, '3000.0 YB'),
            ((3141592, False, False, '%.2f'), '3.14 MB'),
            ((3000, False, True, '%.3f'), '2.930K'),
            ((3000000000, False, True, '%.0f'), '3G'),
            ((10**26 * 30, True, False, '%.3f'), '2481.542 YiB')
        ]
        for args, expected_result in tests_and_expected_results:
            if isinstance(args, tuple):
                result = bytes_util.natural_size(*args)
            else:
                result = bytes_util.natural_size(args)
            self.assertEqual(expected_result, result)
