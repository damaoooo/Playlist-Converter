from datetime import datetime
from typing import List
import asyncio
from colorama import Fore, init
from prettytable import PrettyTable
from pyncm_async import apis
from pyncm_async.apis import login

from .netease_utils import NeteasePlaylist, NeteaseSong

# Initialize colorama
init()


class NeteaseMusic:
    def __init__(self):
        self.uid = 0
        self.nickname = ""

        self.created_playlists: List[NeteasePlaylist] = []
        self.subscribed_playlists: List[NeteasePlaylist] = []
        self._session = None
    
    async def login(self, music_id_or_path: str):
        """
        登录网易云音乐并获取所有歌单及其歌曲。
        
        参数:
            music_id_or_path: str - music_id或包含music_id的文件路径
        """
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
        res = await login.LoginViaCookie(MUSIC_U=music_u)
        if res['code'] == 200:
            print(Fore.GREEN + "Netease Music login success" + Fore.RESET)
            self.uid = res['result']['content']['profile']['userId']
            self.nickname = res['result']['content']['profile']['nickname']
            print(Fore.GREEN + f"uid: {self.uid}, nickname: {self.nickname}" + Fore.RESET)
            
            # 登录成功后获取歌单（歌曲会在retrive_playlists中获取）
            await self.retrive_playlists()
        else:
            print(Fore.RED + "Netease Music login failed" + Fore.RESET)
            raise Exception("登录失败")

    async def retrive_playlists(self):
        """获取用户的歌单列表及其中的歌曲"""
        playlists = await apis.user.GetUserPlaylists(self.uid, limit=1000)
        print(Fore.BLUE + "正在获取歌单及歌曲..." + Fore.RESET)
        
        # 先收集所有创建的歌单
        created_playlists = []
        for playlist in playlists['playlist']:
            playlist_obj: NeteasePlaylist = NeteasePlaylist(name=playlist['name'],
                                                id=playlist['id'],
                                                creator_id=playlist['userId'],
                                                create_time=playlist['createTime'])
            if playlist['userId'] == self.uid:
                created_playlists.append(playlist_obj)
                self.created_playlists.append(playlist_obj)
            else:
                self.subscribed_playlists.append(playlist_obj)
        
        # 并行获取所有创建的歌单中的歌曲
        if created_playlists:
            tasks = [self.get_songs(playlist) for playlist in created_playlists]
            await asyncio.gather(*tasks)
            
            # 打印结果
            for playlist in created_playlists:
                print(Fore.GREEN + f"已获取歌单 '{playlist.name}' 的 {len(playlist.songs)} 首歌曲" + Fore.RESET)

    async def get_songs(self, playlist: NeteasePlaylist):
        if playlist.songs:
            return
        
        songs = await apis.playlist.GetPlaylistInfo(playlist.id)
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

    async def close(self):
        """关闭并清理资源"""
        # 如果有其他需要清理的资源，也在这里处理
        pass


if __name__ == '__main__':
    import asyncio
    
    async def main():
        ncm = NeteaseMusic()
        await ncm.login("/home/damaoooo/Downloads/Playlist-Converter/src/Netease/music_id")
        await ncm.retrive_playlists()

    asyncio.run(main())