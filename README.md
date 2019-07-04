skyway_gw_wrapper
====================
[![Build Status](https://travis-ci.org/kkpb/skyway_gw_wrapper.svg?branch=master)](https://travis-ci.org/kkpb/skyway_gw_wrapper)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

- `skyway-webrtc-gateway`, `GStreamer` のプロセス管理
  - 死活監視、再起動
- [SkyWay](https://webrtc.ecl.ntt.com/) の `peer`, `media` 等の管理

依存関係
---------
- Python 3.5 以上
- [skyway-webrtc-gateway](https://github.com/skyway/skyway-webrtc-gateway)
- [GStreamer 1.0](https://gstreamer.freedesktop.org/)

実行方法
---------
- [SkyWay](https://webrtc.ecl.ntt.com/) に登録して API-KEY を取得
- [skyway-webrtc-gateway](https://github.com/skyway/skyway-webrtc-gateway) からバイナリをダウンロード
- gateway のパスを指定して実行

```
    $ APIKEY=key DOMAIN=domain GATEWAY_PATH='./gateway_linux_arm' python3.5 skyway_gw_wrapper.py
```