# dlna-audio-stream-enforcer

This daemon constantly forces your DLNA audio player (e.g. Nakamichi MR-01) to play audio stream (e.g. from MPD)

## Icecast2 setup

Audio stream must have 24x7 uptime or DLNA receiver might hang. MPD only streams audio when actual music is playing.
To fix this, install icecast2 and add following to `/etc/icecast2/icecast.xml`

```xml
    <mount>
            <mount-name>/mpd.mp3</mount-name>
            <fallback-mount>/silence.mp3</fallback-mount>
            <fallback-override>1</fallback-override>
    </mount>
```

`silence.mp3` must be placed in `/usr/share/icecast2/web/silence.mp3`

## mpd setup

```
audio_output {
	type		"shout"
	encoding	"lame"			# optional
	name		"My Shout Stream"
	host		"localhost"
	port		"8000"
	mount		"/mpd.mp3"
	password	"hackme"
	bitrate		"320"
	format		"44100:16:2"
	protocol	"icecast2"		# optional
	user		"source"		# optional
}
```

## systemd setup

Place following to `/etc/systemd/system/dlna-bathroom.service`

```ini
[Unit]
Description=Bathroom DLNA

[Service]
ExecStart=/usr/bin/python3 /root/dlna-audio-stream-enforcer/dlna-audio-stream-enforcer.py 8001 192.168.0.10
Restart=always
StartLimitInterval=0
StartLimitBurst=0

[Install]
WantedBy=multi-user.target
```
