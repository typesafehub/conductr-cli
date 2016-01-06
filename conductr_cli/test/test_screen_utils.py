from unittest import TestCase
from conductr_cli import screen_utils


class TestProgressBar(TestCase):
    def test_display(self):
        self.assertEqual('[         ]   0%', screen_utils.progress_bar(0, 10, bar_length=10))
        self.assertEqual('[#        ]  10%', screen_utils.progress_bar(1, 10, bar_length=10))
        self.assertEqual('[#####    ]  50%', screen_utils.progress_bar(5, 10, bar_length=10))
        self.assertEqual('[#########] 100%', screen_utils.progress_bar(10, 10, bar_length=10))
        self.assertEqual('[#########] 100%', screen_utils.progress_bar(15, 10, bar_length=10))
