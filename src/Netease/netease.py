from datetime import datetime
from typing import List

from colorama import Fore, init
from prettytable import PrettyTable
from pyncm import apis
from pyncm.apis import login

from .netease_utils import NeteasePlaylist, NeteaseSong

# Initialize colorama
init()


class NeteaseMusic:
    def __init__(self):
        self.uid = 0
        self.nickname = ""

        self.created_playlists: List[NeteasePlaylist] = []
        self.subscribed_playlists: List[NeteasePlaylist] = []
    
    def login(self, music_id_or_path: str):

        # if music_id_or_path is a path
        if music_id_or_path.endswith("music_id"):
            with open(music_id_or_path, "r") as f:
                music_id = f.read().strip()
        else:
            music_id = music_id_or_path

            with open("./music_id", "w") as f:
                # Save music_id to ./music_id
                f.write(music_id)

        music_u = music_id
        res = login.LoginViaCookie(MUSIC_U=music_u)
        if res['code'] == 200:
            print(Fore.GREEN + "login success" + Fore.RESET)
            self.uid = res['result']['content']['profile']['userId']
            self.nickname = res['result']['content']['profile']['nickname']
            print(Fore.GREEN + f"uid: {self.uid}, nickname: {self.nickname}" + Fore.RESET)
        else:
            print(Fore.RED + "login failed" + Fore.RESET)

    def get_playlist(self):
        playlists = apis.user.GetUserPlaylists(self.uid, limit=1000)
        for playlist in playlists['playlist']:
            playlist_obj: NeteasePlaylist = NeteasePlaylist(name=playlist['name'],
                                                id=playlist['id'],
                                                creator_id=playlist['userId'],
                                                create_time=playlist['createTime'])
            if playlist['userId'] == self.uid:
                self.created_playlists.append(playlist_obj)
            else:
                self.subscribed_playlists.append(playlist_obj)

    def get_songs(self, playlist: NeteasePlaylist):
        if playlist.songs:
            return
        
        songs = apis.playlist.GetPlaylistInfo(playlist.id)
        for song in songs['playlist']['tracks']:
            song_obj = NeteaseSong(id=song['id'],
                            name=song['name'],
                            artists=[artist['name'] for artist in song['ar']],
                            album=song['al']['name'])
            playlist.songs.append(song_obj)
    
    def show_songs(self, songs: List[NeteaseSong]):
        table = PrettyTable()
        table.field_names = ["#", "ID", "Name", "Artists", "Album"]

        for index, song in enumerate(songs, start=1):
            table.add_row([index, song.id, song.name, ",".join(song.artists), song.album])
        
        print(table)

    def show_playlists(self, playlists: List[NeteasePlaylist]):

        table = PrettyTable()
        table.field_names = ["#", "ID", "Name", "Create Time"]

        for index, playlist in enumerate(playlists, start=1):
            create_time_human_readable = datetime.fromtimestamp(playlist.create_time//1000).strftime('%Y-%m-%d %H:%M:%S')
            table.add_row([index, playlist.id, playlist.name, create_time_human_readable])

        print(table)

