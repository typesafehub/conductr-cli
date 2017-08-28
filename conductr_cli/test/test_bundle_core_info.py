import json

import datetime

from conductr_cli.bundle_core_info import BundleCoreInfo
from conductr_cli.test.cli_test_case import CliTestCase, file_contents


class TestBundleCore(CliTestCase):
    def test_bundle_core_info_creation_from_bundles_json(self):
        bundles_json = file_contents('data/bundles/bundle_json.json')
        result = BundleCoreInfo.from_bundles(json.loads(bundles_json))
        self.assertEqual(6, len(result))
        self.assertEqual('1', result[0].compatibility_Version)

    def test_bundle_core_filter(self):
        bundles_json = file_contents('data/bundles/bundle_json.json')
        bundle_infos = BundleCoreInfo.from_bundles(json.loads(bundles_json))

        bundle_id = 'cabaae7cf37b1cf99b3861515cd5e77a-d54620c7bc91897bbb2f25faaac25f46'
        bundle_info = BundleCoreInfo.filter_by_bundle_id(bundle_infos, bundle_id)
        self.assertIsNotNone(bundle_info)
        self.assertEqual(bundle_id, bundle_info.bundle_id)
        self.assertEqual(1, bundle_info.scale)
        self.assertEqual('2', bundle_info.compatibility_Version)

        bundle_name = 'visualizer'
        bundle_info = BundleCoreInfo.filter_by_bundle_id(bundle_infos, bundle_name)
        self.assertIsNotNone(bundle_info)
        self.assertEqual(bundle_id, bundle_info.bundle_id)
        self.assertEqual('2', bundle_info.compatibility_Version)
        self.assertEqual(datetime.datetime(2017, 6, 29, 18, 39, 56), bundle_info.start_time)

        bad_bundle_id = 'ahoy'
        bad_bundle_info = BundleCoreInfo.filter_by_bundle_id(bundle_infos, bad_bundle_id)
        self.assertIsNone(bad_bundle_info)

    def test_bundle_core_diff(self):
        first = BundleCoreInfo('1', 'b_name', '12345', '789')
        second = BundleCoreInfo('2', 'b_name2', '12345', '789')
        third = BundleCoreInfo('3', 'b_name3', '12345', '789')
        fourth = BundleCoreInfo('4', 'b_name4', '12345', '789')
        this = (first, second, third)
        that = (first, second, fourth)
        other = (first, second, fourth)

        removed = BundleCoreInfo.diff(this, that)
        added = BundleCoreInfo.diff(that, this)
        same = BundleCoreInfo.diff(other, that)

        self.assertEqual({third}, removed)
        self.assertEqual({fourth}, added)
        self.assertEqual(0, len(same))
