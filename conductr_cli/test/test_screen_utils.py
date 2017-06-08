from unittest import TestCase
from conductr_cli.test.cli_test_case import strip_margin
from conductr_cli import screen_utils


class TestProgressBar(TestCase):
    def test_display(self):
        self.assertEqual('[                                                  ]   0%', screen_utils.progress_bar(0.0))
        self.assertEqual('[#####                                             ]  10%', screen_utils.progress_bar(0.1))
        self.assertEqual('[#########################                         ]  50%', screen_utils.progress_bar(0.5))
        self.assertEqual('[##################################################] 100%', screen_utils.progress_bar(1.0))
        self.assertEqual('[##################################################] 100%', screen_utils.progress_bar(1.5))


class TestHeadlines(TestCase):
    def test_h1(self):
        self.assertEqual(
            strip_margin("""||------------------------------------------------|
                            || Summary                                        |
                            ||------------------------------------------------|"""),
            screen_utils.h1('Summary'))

    def test_h1_wrapping(self):
        self.assertEqual(
            strip_margin("""||------------------------------------------------|
                            || Starting logging feature based on              |
                            || elasticsearch and kibana                       |
                            ||------------------------------------------------|"""),
            screen_utils.h1('Starting logging feature based on elasticsearch and kibana'))

    def test_h2(self):
        self.assertEqual(
            strip_margin("""||- - - - - - - - - - - - - - - - - - - - - - - - |
                            || Sub headline                                   |
                            ||- - - - - - - - - - - - - - - - - - - - - - - - |"""),
            screen_utils.h2('Sub headline'))

    def test_h2_odd_bar_length(self):
        self.assertEqual(
            strip_margin("""||- - - - - - - - - - - - - - - - - - - - - - - - -|
                            || Sub headline                                    |
                            ||- - - - - - - - - - - - - - - - - - - - - - - - -|"""),
            screen_utils.h2('Sub headline', bar_length=51))
