import json
import aiohttp
import asyncio
from colorama import Fore, init
from prettytable import PrettyTable
from typing import List
import time
import aiohttp.log
import logging

from .apm_utils import (
    contains_chinese,
    contains_japanese,
    contains_korean,
    AppleSong,
    ApplePlaylist,
    print_json
)

init()

logging.getLogger('aiohttp.client').setLevel(logging.DEBUG)


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
        self.session = aiohttp.ClientSession()
        self.storefront = None

    async def close(self):
        await self.session.close()

    async def login(self):
        async with self.session.get("https://api.music.apple.com/v1/me/library/playlists", headers=self.header_with_user) as r:
            if r.status == 200:
                print(Fore.GREEN + "Apple Music Login Success" + Fore.RESET)
                self.storefront = await self.get_user_storefront()
            else:
                print(Fore.RED + f"Apple Music Login Failed, Code: {r.status}" + Fore.RESET)

    async def retrive_playlists(self):
        async with self.session.get("https://api.music.apple.com/v1/me/library/playlists", headers=self.header_with_user) as r:
            if r.status == 200:
                playlists = await r.json()
                for playlist in playlists['data']:
                    playlist_obj = ApplePlaylist(id=playlist['id'],
                                                name=playlist['attributes']['name'],
                                                create_time=playlist['attributes']['dateAdded'])
                    if not any(p.id == playlist_obj.id for p in self.playlists):
                        self.playlists.append(playlist_obj)
            else:
                print(Fore.RED + "Failed to get playlists" + Fore.RESET)

    def display_playlists(self):
        table = PrettyTable()
        table.field_names = ["No.", "ID", "Name", "Create Time"]
        for i, playlist in enumerate(self.playlists):
            table.add_row([i+1, playlist.id, playlist.name, playlist.create_time])
        print(table)
        
    async def get_user_storefront(self):
        url = "https://api.music.apple.com/v1/me/storefront"
        async with self.session.get(url, headers=self.header_with_user) as r:
            if r.status == 200:
                storefront = await r.json()
                return storefront['data'][0]['id']
            else:
                print(Fore.RED + f"Failed to get user storefront, Code: {r.status}" + Fore.RESET)
                return None

    async def get_songs(self, playlist: ApplePlaylist):
        if playlist.songs:
            return playlist.songs

        async with self.session.get(f"https://api.music.apple.com/v1/me/library/playlists/{playlist.id}/tracks", headers=self.header_with_user) as r:
            if r.status == 200:
                songs = await r.json()
                for song in songs['data']:
                    song_obj = AppleSong(id=song['id'],
                                    name=song['attributes']['name'],
                                    artist=song['attributes']['artistName'],
                                    album=song['attributes']['albumName'])
                    playlist.songs.append(song_obj)
            else:
                print(Fore.RED + f"Failed to get songs, Code: {r.status}" + Fore.RESET)
        return playlist.songs

    def display_songs(self, songs: list[AppleSong]):
        table = PrettyTable()
        table.field_names = ["No.", "ID", "Name", "Artist", "Album"]
        for i, song in enumerate(songs):
            table.add_row([i, song.id, song.name, song.artist, song.album])
        print(table)

    async def new_playlist(self, name: str, description: str = ""):
        new_playlist = {
            "attributes": {
                "name": name,
                "description": description
            }
        }

        async with self.session.post("https://api.music.apple.com/v1/me/library/playlists", headers=self.header_with_user, json=new_playlist) as r:
            if r.status == 201:
                print(Fore.GREEN + "New Playlist Created" + Fore.RESET)
            else:
                print(Fore.RED + "Failed to create playlist" + Fore.RESET)

    async def delete_playlist(self, playlist: ApplePlaylist):
        async with self.session.delete(f"https://amp-api.music.apple.com/v1/me/library/playlists/{playlist.id}", headers=self.header_with_user) as r:
            if r.status == 204:
                print(Fore.GREEN + "Playlist Deleted" + Fore.RESET)
            else:
                print(Fore.RED + "Failed to delete playlist" + Fore.RESET)

    async def replace_songs_to_playlist(self, playlist: ApplePlaylist, songs: list[AppleSong]):
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

        async with self.session.put(f"https://amp-api.music.apple.com/v1/me/library/playlists/{playlist.id}/tracks", headers=self.header_with_user, json=new_track) as r:
            if r.status in [200, 204]:
                print(Fore.GREEN + "Songs Added" + Fore.RESET)
            else:
                print(Fore.RED + "Failed to add songs" + Fore.RESET)

    async def add_songs_to_playlist(self, playlist_id: str, songs: list[AppleSong]):
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
        print_json(new_track)

        async with self.session.post(f"https://api.music.apple.com/v1/me/library/playlists/{playlist_id}/tracks", 
                                   headers=self.header_with_user, 
                                   json=new_track) as r:
            response_text = await r.text()
            if r.status in [200, 201, 204]:
                print(Fore.GREEN + "Songs Added to Playlist:" + playlist_id + "status:" + str(r.status) + Fore.RESET)
            else:
                print(Fore.RED + f"Failed to add songs: {r.status}" + Fore.RESET)

        # 验证添加结果，带重试
        max_retries = 5
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            print(f"\n正在验证添加结果 (第 {attempt + 1} 次尝试)...")
            await asyncio.sleep(retry_delay)  # 等待API后端更新
            
            async with self.session.get(f"https://api.music.apple.com/v1/me/library/playlists/{playlist_id}/tracks", headers=self.header_with_user) as r:
                if r.status == 200:
                    response = await r.json()
                    # 检查新添加的歌曲是否在播放列表中
                    added_song_names = {song.name for song in songs}
                    playlist_song_names = {track['attributes']['name'] for track in response.get('data', [])}
                    
                    # 找出未成功添加的歌曲
                    failed_songs = [song for song in songs if song.name not in playlist_song_names]
                    
                    if not failed_songs:  # 所有歌曲都添加成功
                        print(Fore.GREEN + f"已成功验证所有歌曲添加到播放列表 {playlist_id}" + Fore.RESET)
                        return
                    
                    if attempt == max_retries - 1:  # 最后一次尝试
                        print(Fore.RED + f"以下歌曲未能成功添加到播放列表:" + Fore.RESET)
                        for song in failed_songs:
                            print(Fore.YELLOW + f"- {song.name} (ID: {song.id}) - 艺术家: {song.artist}" + Fore.RESET)
                else:
                    if attempt == max_retries - 1:  # 最后一次尝试
                        print(Fore.RED + f"验证添加结果失败: {r.status}" + Fore.RESET)

        print(Fore.RED + "达到最大重试次数，部分歌曲可能未成功添加" + Fore.RESET)

    async def stupid_search(self, song_name: str, artist: str, album: str) -> List[AppleSong]:
        country_code = self.storefront
        # if contains_chinese(song_name):
        #     country_code = "cn"
        # elif contains_japanese(song_name):
        #     country_code = "jp"
        # elif contains_korean(song_name):
        #     country_code = "kr"

        search_url = f"https://amp-api.music.apple.com/v1/catalog/{country_code}/search?term={song_name}&types=songs&limit=25"
        async with self.session.get(search_url, headers=self.header_without_user) as r:
            songs = []
            if r.status == 200:
                search_result = await r.json()
                if "songs" not in search_result['results']:
                    return songs
                for song in search_result['results']['songs']['data']:
                    song_obj = AppleSong(id=song['id'],
                                    name=song['attributes']['name'],
                                    artist=song['attributes']['artistName'],
                                    album=song['attributes']['albumName'])
                    songs.append(song_obj)
            return songs


async def main():
    with open("config.json", "r") as f:
        config = json.load(f)

    jwt = config["jwt"]
    user_token = config["user_token"]

    apple = AppleMusic(user_token, jwt)
    await apple.login()
    await apple.retrive_playlists()
    apple.display_playlists()

    songs = await apple.stupid_search("耳朵", "", "")
    apple.display_songs(songs)

    await apple.close()


if __name__ == "__main__":
    asyncio.run(main())
