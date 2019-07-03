import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import time
import skyway_gw_wrapper


class TestSkyWayGatewayWrapper(unittest.TestCase):
    '''
    test skyway_gw_wrapper.py
    '''

    def setUp(self):
        self.key = "key"
        self.domain = "domain"
        with tempfile.NamedTemporaryFile(delete=False, dir=os.path.curdir) as ntf:
            self.path = ntf.name

    def tearDown(self):
        os.remove(self.path)

    def test_init_not_exist_file(self):
        with self.assertRaises(RuntimeError):
            skyway_gw_wrapper.SkyWayGatewayWrapper(self.key, self.domain, "./not_exist_file")

    @patch('skyway_gw_wrapper.shlex')
    def test_start_gateway(self, mock_shlex):
        mock_shlex.split.return_value = ['sleep', '5']

        gw_wrapper = skyway_gw_wrapper.SkyWayGatewayWrapper(self.key, self.domain, self.path)
        self.assertIsNone(gw_wrapper.gw_observer_thread)
        self.assertIsNone(gw_wrapper.gw_subprocess)

        gw_wrapper.start_gateway()
        self.assertIsNotNone(gw_wrapper.gw_observer_thread)
        self.assertIsNotNone(gw_wrapper.gw_subprocess)
        gw_wrapper.gw_observer_thread = None


if __name__ == "__main__":
    unittest.main()
