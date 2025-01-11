from pyncm import apis
from pyncm.apis import login
import json
from colorama import Fore, init
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from prettytable import PrettyTable

# Initialize colorama
init()

def print_json(json_str: str):
    print(json.dumps(json_str, indent=4, ensure_ascii=False))
    # save to ./test.json
    with open("test.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(json_str, indent=4, ensure_ascii=False))

@dataclass
class Song:
    id: int
    name: str
    artists: list
    album: str

@dataclass
class PlayList:
    name: str
    id: int
    creator_id: int
    create_time: int
    songs: List[Song] = field(default_factory=list)

    def print_playlist(self):
        create_time_human_readable = datetime.fromtimestamp(self.create_time).strftime('%Y-%m-%d %H:%M:%S')
        print(f"ID: {self.id}, Name: {self.name}, Create Time: {create_time_human_readable}")

class User:
    def __init__(self):
        self.uid = 0
        self.nickname = ""

        self.created_playlists: List[PlayList] = []
        self.subscribed_playlists: List[PlayList] = []
    
    def login(self, music_u: str):
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
            playlist_obj: PlayList = PlayList(name=playlist['name'],
                                                id=playlist['id'],
                                                creator_id=playlist['userId'],
                                                create_time=playlist['createTime'])
            if playlist['userId'] == self.uid:
                self.created_playlists.append(playlist_obj)
            else:
                self.subscribed_playlists.append(playlist_obj)

    def get_songs(self, playlist: PlayList):
        if playlist.songs:
            return
        
        songs = apis.playlist.GetPlaylistInfo(playlist.id)
        for song in songs['playlist']['tracks']:
            song_obj = Song(id=song['id'],
                            name=song['name'],
                            artists=[artist['name'] for artist in song['ar']],
                            album=song['al']['name'])
            playlist.songs.append(song_obj)
    
    def show_songs(self, songs: List[Song]):
        table = PrettyTable()
        table.field_names = ["#", "ID", "Name", "Artists", "Album"]

        for index, song in enumerate(songs, start=1):
            table.add_row([index, song.id, song.name, ",".join(song.artists), song.album])
        
        print(table)

    def show_playlists(self, playlists: List[PlayList]):

        table = PrettyTable()
        table.field_names = ["#", "ID", "Name", "Create Time"]

        for index, playlist in enumerate(playlists, start=1):
            create_time_human_readable = datetime.fromtimestamp(playlist.create_time//1000).strftime('%Y-%m-%d %H:%M:%S')
            table.add_row([index, playlist.id, playlist.name, create_time_human_readable])

        print(table)

        
with open("./music_id", "r") as f:
    music_id = f.read().strip()

def login_page():
    # print("login method:")
    my_music_u = music_id
    user = User()
    user.login(my_music_u)
    user.get_playlist()
    user.show_playlists(user.created_playlists)
    user.get_songs(user.created_playlists[16])
    user.show_songs(user.created_playlists[16].songs)
    


if __name__ == "__main__":
    login_page()