import json
import requests
from colorama import Fore, init
from prettytable import PrettyTable
from typing import List

from .apm_utils import (
    contains_chinese,
    contains_japanese,
    contains_korean,
    AppleSong,
    ApplePlaylist,
    print_json
)

init()


class AppleMusic:
    def __init__(self, user_token, dev_token):
        self.user_token = user_token
        self.dev_token = dev_token
        self.header_with_user = {
            "authorization": f"Bearer {self.dev_token}",
            "Music-User-Token": self.user_token,
            'Origin': "https://music.apple.com",
            'Referer': "https://music.apple.com/",
        }

        self.header_without_user = {
            "authorization": f"Bearer {self.dev_token}",
            'Origin': "https://music.apple.com",
            'Referer': "https://music.apple.com/",
        }

        self.playlists: list[ApplePlaylist] = []

    def login(self):
        r = requests.get("https://api.music.apple.com/v1/me/library/playlists", headers=self.header_with_user)
        if r.status_code == 200:
            # Print Green Success
            print(Fore.GREEN + "Login Success" + Fore.RESET)
        else:
            # Print Red Failed
            print(Fore.RED + "Login Failed, Code:" + str(r.status_code) + Fore.RESET)

    def get_playlists(self):
        r = requests.get("https://api.music.apple.com/v1/me/library/playlists", headers=self.header_with_user)
        if r.status_code == 200:
            playlists = r.json()
            print_json(playlists)
            for playlist in playlists['data']:
                playlist_obj = ApplePlaylist(id=playlist['id'],
                                        name=playlist['attributes']['name'],
                                        create_time=playlist['attributes']['dateAdded'])
                self.playlists.append(playlist_obj)
        else:
            print(Fore.RED + "Failed to get playlists" + Fore.RESET)

    def display_playlists(self):
        # PrettyTable, No. Name, Create Time
        table = PrettyTable()
        table.field_names = ["No.", "ID", "Name", "Create Time"]
        for i, playlist in enumerate(self.playlists):
            table.add_row([i, playlist.id, playlist.name, playlist.create_time])
        print(table)

    def get_songs(self, playlist: ApplePlaylist):
        if playlist.songs:
            return playlist.songs

        r = requests.get(f"https://api.music.apple.com/v1/me/library/playlists/{playlist.id}/tracks", headers=self.header_with_user)
        if r.status_code == 200:
            songs = r.json()
            for song in songs['data']:
                song_obj = AppleSong(id=song['id'],
                                name=song['attributes']['name'],
                                artist=song['attributes']['artistName'],
                                album=song['attributes']['albumName'])
                playlist.songs.append(song_obj)
        else:
            print(Fore.RED + "Failed to get songs, Code:" + str(r.status_code) + Fore.RESET)
        return playlist.songs

    def display_songs(self, songs: list[AppleSong]):
        # in No., Name, Artist, Album
        table = PrettyTable()
        table.field_names = ["No.", "ID", "Name", "Artist", "Album"]
        for i, song in enumerate(songs):
            table.add_row([i, song.id, song.name, song.artist, song.album])

        print(table)


    def new_playlist(self, name: str, description: str = ""):
        new_playlist = {
            "attributes": {
                "name": name,
                "description": description
            }
        }

        r = requests.post("https://api.music.apple.com/v1/me/library/playlists", headers=self.header_with_user, json=new_playlist)
        if r.status_code == 201:
            print(Fore.GREEN + "New Playlist Created" + Fore.RESET)
        else:
            print(Fore.RED + "Failed to create playlist" + Fore.RESET)

    def delete_playlist(self, playlist: ApplePlaylist):
        r = requests.delete(f"https://amp-api.music.apple.com/v1/me/library/playlists/{playlist.id}", headers=self.header_with_user)
        if r.status_code == 204:
            print(Fore.GREEN + "Playlist Deleted" + Fore.RESET)
        else:
            print(Fore.RED + "Failed to delete playlist" + Fore.RESET)

    def replace_songs_to_playlist(self, playlist: ApplePlaylist, songs: list[AppleSong]):
        songs_body = [
            {
                "id": song.id,
                "type": "songs"
            }
            for song in songs
        ]
        new_track = {
            "data": songs_body
        }

        r = requests.put(f"https://amp-api.music.apple.com/v1/me/library/playlists/{playlist.id}/tracks", headers=self.header_with_user, json=new_track)
        if r.status_code == 204 or r.status_code == 200:
            print(Fore.GREEN + "Songs Added" + Fore.RESET)
        else:
            print(Fore.RED + "Failed to add songs" + Fore.RESET)

    def add_songs_to_playlist(self, playlist: ApplePlaylist, songs: list[AppleSong]):
        songs_body = [
            {
                "id": song.id,
                "type": "songs"
            }
            for song in songs
        ]
        new_track = {
            "data": songs_body
        }

        r = requests.post(f"https://amp-api.music.apple.com/v1/me/library/playlists/{playlist.id}/tracks", headers=self.header_with_user, json=new_track)
        if r.status_code == 201 or r.status_code == 200:
            print(Fore.GREEN + "Songs Added" + Fore.RESET)
        else:
            print(Fore.RED + "Failed to add songs" + Fore.RESET)

    def stupid_search(self, song_name: str, artist: str, album: str) -> List[AppleSong]:
        # check if song name is Chinese
        country_code = "us"
        if contains_chinese(song_name):
            country_code = "cn"
        elif contains_japanese(song_name):
            country_code = "jp"
        elif contains_korean(song_name):
            country_code = "kr"
        else:
            country_code = "us"

        search_url = f"https://amp-api.music.apple.com/v1/catalog/{country_code}/search?term={song_name}&types=songs&limit=25"
        r = requests.get(search_url, headers=self.header_without_user)
        songs = []
        if r.status_code == 200:
            search_result = r.json()
            for song in search_result['results']['songs']['data']:
                song_obj = AppleSong(id=song['id'],
                                name=song['attributes']['name'],
                                artist=song['attributes']['artistName'],
                                album=song['attributes']['albumName'])
                songs.append(song_obj)
        return songs

            
if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)

    jwt = config["jwt"]
    user_token = config["user_token"]

    apple = AppleMusic(user_token, jwt)

    songs = apple.stupid_search("初雪", "", "")
    apple.display_songs(songs)
