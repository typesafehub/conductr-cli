from unittest import TestCase
from conductr_cli import data_structure_utils
from collections import OrderedDict


class TestSortDict(TestCase):
    def test_simple_dict(self):
        unordered_dict = {
            'a': 1,
            'c': 3,
            'b': 2
        }
        expected_ordered_dict = OrderedDict()
        expected_ordered_dict['a'] = 1
        expected_ordered_dict['b'] = 2
        expected_ordered_dict['c'] = 3

        self.assertEqual(
            data_structure_utils.sort_dict(unordered_dict),
            expected_ordered_dict
        )

    def test_nested_dict(self):
        unordered_dict = {
            'a': 1,
            'c': 3,
            'b': {
                'b': 2,
                'a': 1,
                'c': {
                    'c': 3,
                    'b': 2,
                    'a': 1
                }
            }
        }
        expected_ordered_sub_dict_bc = OrderedDict()
        expected_ordered_sub_dict_bc['a'] = 1
        expected_ordered_sub_dict_bc['b'] = 2
        expected_ordered_sub_dict_bc['c'] = 3
        expected_ordered_sub_dict_b = OrderedDict()
        expected_ordered_sub_dict_b['a'] = 1
        expected_ordered_sub_dict_b['b'] = 2
        expected_ordered_sub_dict_b['c'] = expected_ordered_sub_dict_bc
        expected_ordered_dict = OrderedDict()
        expected_ordered_dict['a'] = 1
        expected_ordered_dict['b'] = expected_ordered_sub_dict_b
        expected_ordered_dict['c'] = 3

        self.assertEqual(
            data_structure_utils.sort_dict(unordered_dict),
            expected_ordered_dict
        )
