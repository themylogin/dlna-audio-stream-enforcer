from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
from lxml import objectify
import os
import requests
import socket
import signal
import sys
import textwrap
import threading

logger = logging.getLogger(__name__)

MY_IP = "192.168.0.4"
MY_PORT = int(sys.argv[1])
MPD_URL = "http://192.168.0.4:8000/mpd.mp3"
CLIENT_URL = "http://%s:55426" % sys.argv[2]


class MpdProxy(BaseHTTPRequestHandler):
    def do_GET(self):
        self.wfile._sock.settimeout(10)

        for k, v in {
            "Content-Disposition": "inline;",
            "Content-Type": "audio/mpegurl",
            "Ext": "",
            "Connection": "close",
            "contentFeatures.dlna.org": "DLNA.ORG_OP=00;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000",
            "transferMode.dlna.org": "Streaming",
        }.items():
            self.send_header(k, v)
        self.flush_headers()

        try:
            stream = requests.get(MPD_URL, stream=True, timeout=5)
            for chunk in stream.iter_content(16384, False):
                self.wfile.write(chunk)
        except Exception:
            logger.error("Server error", exc_info=True)
            raise
        finally:
            os.kill(os.getpid(), signal.SIGTERM)


server = HTTPServer((MY_IP, MY_PORT), MpdProxy)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()

discovery = objectify.fromstring(requests.get(CLIENT_URL, timeout=5).content)
for service in discovery.device.serviceList.service:
    if str(service.serviceType).startswith("urn:schemas-upnp-org:service:AVTransport:"):
        avtransport_control_url = str(service.controlURL)
        break
else:
    raise Exception("Unable to find AVTransport control URL")

print(requests.post(
    CLIENT_URL + avtransport_control_url,
    headers={
        "Content-type": "text/xml; charset=utf-8",
        "SOAPAction": "\"urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI\""
    },
    data=textwrap.dedent("""\
        <?xml version="1.0" encoding="utf-8" standalone="yes"?>
        <s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
            <s:Body>
                <u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
                    <InstanceID>0</InstanceID>
                    <CurrentURI>http://""" + ("%s:%s" % (MY_IP, MY_PORT)) + """/stream.mp3</CurrentURI>
                    <CurrentURIMetaData>&lt;?xml version="1.0" encoding="utf-8"?&gt;
                        &lt;DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/" xmlns:sec="http://www.sec.co.kr/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"&gt;
                            &lt;item id="0" parentID="0" restricted="1"&gt;
                                &lt;upnp:class&gt;object.item.audioItem.musicTrack&lt;/upnp:class&gt;
                                &lt;dc:title&gt;&lt;/dc:title&gt;
                                &lt;dc:creator&gt;&lt;/dc:creator&gt;
                                &lt;upnp:artist&gt;&lt;/upnp:artist&gt;
                                &lt;upnp:albumArtURI&gt;/&lt;/upnp:albumArtURI&gt;
                                &lt;upnp:album&gt;&lt;/upnp:album&gt;
                                &lt;res protocolInfo="http-get:*:audio/mpegurl:DLNA.ORG_OP=00;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000"&gt;http://""" + ("%s:%s" % (MY_IP, MY_PORT)) + """/stream.mp3&lt;/res&gt;
                            &lt;/item&gt;
                        &lt;/DIDL-Lite&gt;
                    </CurrentURIMetaData>
                </u:SetAVTransportURI>
            </s:Body>
        </s:Envelope>
    """),
    timeout=10,
).content)

print(requests.post(
    CLIENT_URL + avtransport_control_url,
    headers={
        "Content-type": "text/xml; charset=utf-8",
        "SOAPAction": "\"urn:schemas-upnp-org:service:AVTransport:1#Play\""
    },
    data=textwrap.dedent("""\
        <?xml version="1.0" encoding="utf-8" standalone="yes"?>
        <s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
            <s:Body>
                <u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
                    <InstanceID>0</InstanceID>
                    <Speed>1</Speed>
                </u:Play>
            </s:Body>
        </s:Envelope>
    """),
    timeout=10,
).content)

server_thread.join()
