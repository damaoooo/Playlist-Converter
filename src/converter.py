from Apple import apm
from Netease import netease

import json

if __name__ == '__main__':
    netease_music = netease.NeteaseMusic()
    netease_music.login("./Netease/music_id")
    netease_music.get_playlist()
    netease_music.show_playlists(netease_music.created_playlists)

    with open("./Apple/config.json", "r") as f:
        config = json.load(f)

    apple_music = apm.AppleMusic()