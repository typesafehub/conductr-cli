from conductr_cli import bundle_deploy
from unittest import TestCase


class TestGenerateHmac(TestCase):
    def test_success(self):
        result = bundle_deploy.generate_hmac_signature('secret', 'reactive-maps-backend-summary')
        self.assertEqual('2un791uBDf59/fHrIOWMqt0mhwEoH0yqkZXmz//4alQ=', result)
