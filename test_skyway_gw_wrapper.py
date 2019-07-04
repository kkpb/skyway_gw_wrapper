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
        self.media_id = "media_id"
        self.port = 55555
        self.ip_v4 = "0.0.0.0"

    def tearDown(self):
        os.remove(self.path)

    def test_init_not_exist_file(self):
        '''
        存在しないファイルを指定したら RuntimeError を投げる
        '''
        with self.assertRaises(RuntimeError):
            skyway_gw_wrapper.SkyWayGatewayWrapper(self.key, self.domain, "./not_exist_file")

    @patch('skyway_gw_wrapper.shlex')
    def test_start_gateway(self, mock_shlex):
        '''
        指定したコマンドが実行される
        プロセスを管理するスレッドが起動する
        プロセスが異常終了しても再起動される
        '''
        mock_shlex.split.return_value = ['sleep', '5']

        gw_wrapper = skyway_gw_wrapper.SkyWayGatewayWrapper(self.key, self.domain, self.path)
        self.assertIsNone(gw_wrapper.gw_observer_thread)
        self.assertIsNone(gw_wrapper.gw_subprocess)

        gw_wrapper.start_gateway()
        self.assertIsNotNone(gw_wrapper.gw_observer_thread)
        self.assertTrue(gw_wrapper.gw_observer_thread.is_alive())
        self.assertIsNotNone(gw_wrapper.gw_subprocess)
        self.assertIsNone(gw_wrapper.gw_subprocess.poll())

        gw_wrapper.gw_subprocess.kill()
        self.assertIsNotNone(gw_wrapper.gw_observer_thread)
        self.assertTrue(gw_wrapper.gw_observer_thread.is_alive())
        self.assertIsNotNone(gw_wrapper.gw_subprocess)
        self.assertIsNone(gw_wrapper.gw_subprocess.poll())
        gw_wrapper.gw_observer_thread = None

    @patch('skyway_gw_wrapper.urllib.request.urlopen')
    def test_open_video(self, mock_urlopen):
        '''
        media のパラメータがセットされる
        '''
        s = '{"media_id": "%s", "port": %s, "ip_v4": "%s"}' % (self.media_id, self.port, self.ip_v4)

        mock = MagicMock()
        mock.getcode.return_value = 200
        mock.read.return_value = s.encode('utf8')
        mock.__enter__.return_value = mock
        mock_urlopen.return_value = mock

        gw_wrapper = skyway_gw_wrapper.SkyWayGatewayWrapper(self.key, self.domain, self.path)
        media_id = gw_wrapper.open_video()
        self.assertEqual(self.media_id, media_id)
        self.assertEqual((self.ip_v4, self.port), gw_wrapper.medias[media_id])

    @patch('skyway_gw_wrapper.shlex')
    @patch('skyway_gw_wrapper.urllib.request.urlopen')
    def test_start_streaming(self, mock_urlopen, mock_shlex):
        '''
        指定したコマンドが実行される
        プロセスを管理するスレッドが起動する
        プロセスが異常終了しても再起動される
        '''
        s = '{"media_id": "%s", "port": %s, "ip_v4": "%s"}' % (self.media_id, self.port, self.ip_v4)

        mock = MagicMock()
        mock.getcode.return_value = 200
        mock.read.return_value = s.encode('utf8')
        mock.__enter__.return_value = mock
        mock_urlopen.return_value = mock

        gw_wrapper = skyway_gw_wrapper.SkyWayGatewayWrapper(self.key, self.domain, self.path)
        media_id = gw_wrapper.open_video()

        mock_shlex.split.return_value = ['sleep', '5']

        gw_wrapper.start_streaming(media_id)
        self.assertIsNotNone(gw_wrapper.gst_observer_thread)
        self.assertTrue(gw_wrapper.gst_observer_thread.is_alive())
        self.assertIsNotNone(gw_wrapper.gst_subprocess)
        self.assertIsNone(gw_wrapper.gst_subprocess.poll())

        gw_wrapper.gst_subprocess.kill()
        self.assertIsNotNone(gw_wrapper.gst_observer_thread)
        self.assertTrue(gw_wrapper.gst_observer_thread.is_alive())
        self.assertIsNotNone(gw_wrapper.gst_subprocess)
        self.assertIsNone(gw_wrapper.gst_subprocess.poll())
        gw_wrapper.gst_observer_thread = None


if __name__ == "__main__":
    unittest.main()
