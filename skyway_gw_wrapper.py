import os
import shlex
import subprocess
import threading
import json
import urllib.request
import time
import inspect
from logging import getLogger, StreamHandler, DEBUG

'''
SkyWayGatewayWrapper
  process management(keepalive, restart)
    gateway_linux_arm
    gst-launch-1.0
'''


logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


class SkyWayGatewayWrapper(object):
    def __init__(self, key, domain, path):
        if not os.path.exists(path):
            raise RuntimeError("%s is not found" % path)
        else:
            self.key = key
            self.domain = domain
            self.path = path
            self.gw_cmd = os.path.abspath(self.path)
            self.gst_cmd = None
            self.base_url = "http://127.0.0.1:8000/"
            self.peers = {}
            self.medias = {}
            self.media_id = None
            self.video_params = {}
            self.__gateway = "gateway"
            self.__gstreamer = "gstreamer"
            self.__threads = {self.__gateway: None, self.__gstreamer: None}
            self.__threads_stop_flag = {self.__gateway: False,
                                        self.__gstreamer: False}
            self.__subprocesses = {self.__gateway: None,
                                   self.__gstreamer: None}

    @property
    def gw_observer_thread(self):
        return self.__threads[self.__gateway]

    @gw_observer_thread.setter
    def gw_observer_thread(self, thread):
        logger.debug(inspect.currentframe().f_code.co_name)
        if self.gw_observer_thread:
            self.__threads_stop_flag[self.__gateway] = True
            self.gw_observer_thread.join()
        self.__threads[self.__gateway] = thread

    @property
    def gw_subprocess(self):
        return self.__subprocesses[self.__gateway]

    # reset peers and medias when restart gateway
    @gw_subprocess.setter
    def gw_subprocess(self, process):
        logger.debug(inspect.currentframe().f_code.co_name)
        if self.gst_observer_thread:
            self.gst_observer_thread = None
        if self.gw_subprocess:
            self.__threads_stop_flag[self.__gateway] = True
            self.gw_subprocess.wait()
        self.peers = {}
        self.medias = {}
        self.__subprocesses[self.__gateway] = process

    def _set_gw_subprocess(self, process):
        self.gw_subprocess = process

    @property
    def gst_observer_thread(self):
        return self.__threads[self.__gstreamer]

    @gst_observer_thread.setter
    def gst_observer_thread(self, thread):
        logger.debug(inspect.currentframe().f_code.co_name)
        if self.gst_observer_thread:
            self.__threads_stop_flag[self.__gstreamer] = True
            self.gst_observer_thread.join()
        self.__threads[self.__gstreamer] = thread

    @property
    def gst_subprocess(self):
        return self.__subprocesses[self.__gstreamer]

    @gst_subprocess.setter
    def gst_subprocess(self, process):
        logger.debug(inspect.currentframe().f_code.co_name)
        if self.gst_subprocess:
            self.__threads_stop_flag[self.__gstreamer] = True
            self.gst_subprocess.wait()
        self.__subprocesses[self.__gstreamer] = process

    def _set_gst_subprocess(self, process):
        self.gst_subprocess = process

    def __observer(self, key, setter, cmd):
        logger.debug(inspect.currentframe().f_code.co_name)
        while True:
            if self.__threads_stop_flag[key]:
                self.__subprocesses[key].terminate()
                self.__subprocesses[key].wait()
                self.__threads[key] = None
                self.__subprocesses[key] = None
                self.__threads_stop_flag[key] = False
                break

            status = self.__subprocesses[key].poll()
            if not status:
                time.sleep(1)
                continue
            elif status == 0:
                break
            else:
                setter(subprocess.Popen(args=shlex.split(cmd)))

    def __peer_events_observer(self, peer_id):
        logger.debug(inspect.currentframe().f_code.co_name)
        self.__threads_stop_flag[peer_id] = False

        url = self.base_url + "peers/%s/events?token=%s" % (peer_id, self.peers[peer_id])
        headers = {"accept": "application/json"}
        request = urllib.request.Request(url, headers=headers, method="GET")

        while True:
            if self.__threads_stop_flag[peer_id]:
                del self.__threads_stop_flag[peer_id]
                break
            try:
                with urllib.request.urlopen(request) as response:
                    json_response = json.loads(response.read().decode("utf8"))
                    event = json_response["event"]
                    if event == "OPEN":
                        continue
                    elif event == "CALL":
                        media_connection_id = json_response["call_params"]["media_connection_id"]
                        self.__make_answer(media_connection_id)
                        continue
                    else:
                        continue
            except urllib.error.HTTPError as error:
                logger.error(error)
                continue
            except urllib.error.URLError as error:
                logger.error(error)
                continue

    def __make_answer(self, media_connection_id):
        logger.debug(inspect.currentframe().f_code.co_name)
        url = self.base_url + "media/connections/%s/answer" % media_connection_id
        data = {"constraints": {"video": True, "videoReceiveEnabled": False,
                                "audio": False, "audioReceiveEnabled": False,
                                "video_params": {"band_width": int(self.video_params["bitrate"]),
                                                 "codec": self.video_params["codec"],
                                                 "media_id": self.media_id,
                                                 "payload_type": 96,
                                                 "sampling_rate": 90000}}}
        headers = {"accept": "application/json",
                   "Content-Type": "application/json"}
        _data = json.dumps(data).encode(),
        request = urllib.request.Request(url,
                                         data=json.dumps(data).encode(),
                                         headers=headers,
                                         method="POST")

        try:
            with urllib.request.urlopen(request) as response:
                json_response = json.loads(response.read().decode("utf8"))
                if json_response["params"]["video_id"] == self.media_id:
                    return
                else:
                    logger.error("video_id = %s, media_id = %s" % (json_response["params"]["video_id"], self.media_id))
        except urllib.error.HTTPError as error:
            logger.error(error)
        except urllib.error.URLError as error:
            logger.error(error)

    def start_gateway(self):
        logger.debug(inspect.currentframe().f_code.co_name)
        self.gw_subprocess = subprocess.Popen(args=shlex.split(self.gw_cmd))
        self.gw_observer_thread = threading.Thread(target=self.__observer,
                                                   args=(self.__gateway, self._set_gw_subprocess, self.gw_cmd))
        self.gw_observer_thread.start()

    def peer(self, peer_id=None):
        logger.debug(inspect.currentframe().f_code.co_name)
        url = self.base_url + "peers"
        data = {"key": self.key,
                "domain": self.domain}
        if peer_id:
            data["peer_id"] = peer_id
        headers = {"accept": "application/json",
                   "Content-Type": "application/json"}
        request = urllib.request.Request(url,
                                         data=json.dumps(data).encode(),
                                         headers=headers,
                                         method="POST")

        try:
            with urllib.request.urlopen(request) as response:
                json_response = json.loads(response.read().decode("utf8"))
                peer_id = json_response["params"]["peer_id"]
                self.peers[peer_id] = json_response["params"]["token"]

                self.__threads[peer_id] = threading.Thread(target=self.__peer_events_observer,
                                                           args=(peer_id,))
                self.__threads[peer_id].start()

                return peer_id
        except urllib.error.HTTPError as error:
            raise RuntimeError(error)
        except urllib.error.URLError as error:
            raise RuntimeError(error)

    def open_video(self):
        logger.debug(inspect.currentframe().f_code.co_name)
        data = {"is_video": True}
        return self.__media(data)

    def open_audio(self):
        logger.debug(inspect.currentframe().f_code.co_name)
        data = {"is_video": False}
        return self.__media(data)

    def __media(self, data):
        logger.debug(inspect.currentframe().f_code.co_name)
        url = self.base_url + "media"
        headers = {"accept": "application/json",
                   "Content-Type": "application/json"}
        request = urllib.request.Request(url,
                                         data=json.dumps(data).encode(),
                                         headers=headers,
                                         method="POST")

        try:
            with urllib.request.urlopen(request) as response:
                res = response.read().decode("utf8")
                json_response = json.loads(res)
                media_id = json_response["media_id"]
                port = json_response["port"]
                ip = json_response["ip_v4"]
                self.medias[media_id] = (ip, port)

                return media_id
        except urllib.error.HTTPError as error:
            raise RuntimeError(error)
        except urllib.error.URLError as error:
            raise RuntimeError(error)

    def start_streaming(self,
                        media_id,
                        width="1280",
                        height="720",
                        framerate="30",
                        bitrate="10000000",
                        codec="h264",
                        videoflip="none"):
        logger.debug(inspect.currentframe().f_code.co_name)
        ip, port = self.medias[media_id]

        self.video_params["width"] = width
        self.video_params["height"] = height
        self.video_params["framerate"] = framerate
        self.video_params["bitrate"] = bitrate
        self.video_params["videoflip"] = videoflip

        if codec == "h264":
            encoder = "omxh264enc target-bitrate=%s control-rate=variable" % bitrate
            rtp = "rtph264pay"
            self.video_params["codec"] = "H264"
        elif codec == "vp8":
            encoder = "vp8enc target-bitrate=%s" % bitrate
            rtp = "rptvp8pay"
            self.video_params["codec"] = "VP8"
        else:
            raise RuntimeError("unsupport codec")

        cmd = """\
gst-launch-1.0 v4l2src ! \
videoflip method=%s ! \
video/x-raw,width=%s,height=%s,framerate=%s/1,bitrate=%s ! \
%s ! %s ! \
multiudpsink clients=%s:%s""" % (videoflip, width, height, framerate, bitrate, encoder, rtp, ip, port)
        logger.debug(cmd)
        self.gst_cmd = cmd

        self.gst_subprocess = subprocess.Popen(args=shlex.split(self.gst_cmd))
        self.gst_observer_thread = threading.Thread(target=self.__observer,
                                                    args=(self.__gstreamer, self._set_gst_subprocess, self.gst_cmd))
        self.gst_observer_thread.start()


if __name__ == "__main__":
    key = os.environ['APIKEY']
    domain = os.environ['DOMAIN']
    path = os.environ['GATEWAY_PATH']
    gw_wrapper = SkyWayGatewayWrapper(key, domain, path)
    gw_wrapper.start_gateway()
    media_id = gw_wrapper.open_video()
    print(media_id)
    gw_wrapper.start_streaming(media_id)
    gw_wrapper.media_id = media_id
    peer_id = gw_wrapper.peer(peer_id="test")
    print(peer_id)
    gw_wrapper.gst_observer_thread.join()
    gw_wrapper.gw_observer_thread = None
    gw_wrapper.gst_observer_thread = None
