from Apple import apm
from Netease import netease

from typing import Tuple, List, Optional
import json
import logging
from prettytable import PrettyTable
import asyncio
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn
)
from rich.console import Console
from rich.live import Live
from rich.layout import Layout

import traceback
import time

console = Console()

def get_choice(prompt: str, max_choice: int, allow_empty: bool = True):
    def is_choice_valid(choice: str, max_choice: int):
        if choice == "" and allow_empty:
            return True
        if choice == "" and not allow_empty:
            return False
        if not choice.isdigit():
            return False
        if int(choice) > max_choice:
            return False
        return True
    
    choice = input(prompt)
    while not is_choice_valid(choice, max_choice):
        print("无效选择")
        choice = input(prompt)
    
    if choice:
        return int(choice)

    return choice

def get_text_input(prompt: str, list_of_valid: list[str] = []):
    text = input(prompt)
    while not text or (list_of_valid and text not in list_of_valid):
        print("无效输入")
        text = input(prompt)
    return text


def print_song_list(song_list: list[apm.AppleSong]):
    # 创建表格显示
    table = PrettyTable()
    table.field_names = ["No.", "ID", "Name", "Artist", "Album"]
    for i, song in enumerate(song_list):
        table.add_row([i+1, song.id, song.name, song.artist, song.album])
    print(table)



# 从网易云音乐搜索歌曲并匹配到Apple Music
class Converter:
    def __init__(self, netease_music: netease.NeteaseMusic, apple_music: apm.AppleMusic):
        self.netease_music: netease.NeteaseMusic = netease_music
        self.apple_music: apm.AppleMusic = apple_music

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        # 文件日志处理器
        file_handler = logging.FileHandler('app.log')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # 控制台日志处理器
        stream_handler = logging.StreamHandler()
        stream_formatter = logging.Formatter('%(levelname)s - %(message)s')
        stream_handler.setFormatter(stream_formatter)
        self.logger.addHandler(stream_handler)

    async def both_login(self, netease_music_id_or_path: str, apple_music_id_or_path: str):
        await self.netease_music.login(netease_music_id_or_path)
        self.apple_music.login(apple_music_id_or_path)

    async def search_song_in_apm(self, from_song: netease.NeteaseSong) -> Tuple[bool, list[apm.AppleSong]]:
        """
        在 Apple Music 中搜索歌曲。
        
        参数:
            from_song (NeteaseSong): 要搜索的网易云音乐歌曲
            
        返回:
            Tuple[bool, list[AppleSong]]: (是否完全匹配, 匹配结果列表)
        """
        song_name = from_song.name
        song_artist = from_song.artists[0]
        song_album = from_song.album

        results = await self.apple_music.stupid_search(song_name, song_artist, song_album)

        # if results is []
        if not results:
            return False, []
        
        match_list = []

        for apm_song in results:
            # if name, album, artist, 2 out of 3 are the same, then we consider it as the same song
            match_count = 0
            if apm_song.name == song_name:
                match_count += 1
            if apm_song.artist == song_artist:
                match_count += 1
            if apm_song.album == song_album:
                match_count += 1

            if match_count >= 2:
                match_list.append(apm_song)
            
        if not match_list:
            return False, results
        else:
            return True, match_list
    

    async def convert_play_list(self, from_playlist: netease.NeteasePlaylist, 
                           skip: bool = False, 
                           progress_callback = None,
                           manual_selection_callback = None):
        """
        将网易云音乐播放列表转换为Apple Music播放列表。
        
        参数:
            from_playlist (NeteasePlaylist): 源网易云音乐播放列表
            skip (bool, optional): 是否跳过需要手动选择的歌曲。默认为False
            progress_callback: 进度回调函数，接收进度百分比和当前歌曲信息
            manual_selection_callback: 手动选择回调函数，接收原始歌曲和匹配列表
        """
        playlist_name, new_playlist = await self._setup_target_playlist()
        song_results = await self._process_playlist_conversion(from_playlist, skip, progress_callback, manual_selection_callback)
        await self._finalize_playlist(new_playlist, song_results)

    async def _setup_target_playlist(self) -> Tuple[str, apm.ApplePlaylist]:
        """
        处理目标Apple Music播放列表的创建或选择。
        
        返回:
            Tuple[str, ApplePlaylist]: 播放列表名称和播放列表对象
        """
        create_prompt = "是否创建新的播放列表？(Y/n): "
        choice = get_text_input(create_prompt, ["Y", "n", ""])
        
        if choice == "n":
            await self.apple_music.retrive_playlists()
            self.apple_music.display_playlists()
            choice = get_choice("请选择要添加到哪个播放列表: ", 
                              len(self.apple_music.playlists), 
                              allow_empty=False)
            new_playlist = self.apple_music.playlists[choice-1]
            return new_playlist.name, new_playlist
        
        new_playlist_name = get_text_input("请输入新播放列表的名称: ")
        # 记录创建前的播放列表数量
        await self.apple_music.retrive_playlists()
        original_playlist_count = len(self.apple_music.playlists)
        
        await self.apple_music.new_playlist(new_playlist_name)

        # 添加重试逻辑和超时保护
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            await self.apple_music.retrive_playlists()
            # 检查是否有新的播放列表被创建
            if len(self.apple_music.playlists) > original_playlist_count:
                # 遍历所有播放列表找到新创建的
                for playlist in self.apple_music.playlists:
                    if playlist.name == new_playlist_name:
                        self.logger.info(f"创建新播放列表: {new_playlist_name}, ID: {playlist.id}")
                        return new_playlist_name, playlist
            
            retry_count += 1
            await asyncio.sleep(2)  # 添加短暂延迟
        
        raise Exception(f"创建播放列表失败: {new_playlist_name}")

    async def _process_playlist_conversion(self, 
                                        from_playlist: netease.NeteasePlaylist, 
                                        skip: bool,
                                        progress_callback = None,
                                        manual_selection_callback = None) -> List[apm.AppleSong]:
        """
        处理播放列表转换，包括自动匹配和手动选择。
        
        参数:
            from_playlist (NeteasePlaylist): 要转换的源播放列表
            skip (bool): 是否跳过需要手动选择的歌曲
            progress_callback: 进度回调函数
            manual_selection_callback: 手动选择回调函数
            
        返回:
            List[AppleSong]: 匹配的Apple Music歌曲列表
        """
        search_results = await self._search_all_songs(from_playlist.songs, progress_callback)
        song_results, manual_matches = self._process_search_results(search_results, skip)
        
        if not skip and manual_matches and manual_selection_callback:
            for idx, original_song, match_list in manual_matches:
                song_info = {
                    "name": original_song.name,
                    "artist": original_song.artists[0],
                    "album": original_song.album
                }
                matches = [{
                    "id": song.id,
                    "name": song.name,
                    "artist": song.artist,
                    "album": song.album
                } for song in match_list]
                await manual_selection_callback(song_info, matches)
        
        return [song for song in song_results if song is not None]

    async def _search_all_songs(self, 
                              songs: List[netease.NeteaseSong],
                              progress_callback = None) -> List[Tuple[int, netease.NeteaseSong, bool, List[apm.AppleSong]]]:
        """
        异步搜索所有歌曲并显示进度。
        """
        results = []
        total = len(songs)
        
        for i, song in enumerate(songs):
            if progress_callback:
                progress = int((i / total) * 100)
                song_info = {
                    "name": song.name,
                    "artist": song.artists[0],
                    "album": song.album
                }
                await progress_callback(progress, song_info)
                
            success, match_list = await self.search_song_in_apm(song)
            results.append((i, song, success, match_list))

        if progress_callback:
            await progress_callback(100, {"name": "完成", "artist": "", "album": ""})

        return sorted(results, key=lambda x: x[0])

    def _process_search_results(self, 
                              search_results: List[Tuple[int, netease.NeteaseSong, bool, List[apm.AppleSong]]], 
                              skip: bool) -> Tuple[List[Optional[apm.AppleSong]], List[Tuple[int, netease.NeteaseSong, List[apm.AppleSong]]]]:
        """
        处理搜索结果，将自动匹配和需要手动选择的歌曲分开。
        
        参数:
            search_results (List[Tuple]): 歌曲搜索结果
            skip (bool): 是否跳过需要手动选择的歌曲
            
        返回:
            Tuple[List, List]: 自动匹配列表和需要手动选择的歌曲列表
        """
        song_results = [None] * len(search_results)
        songs_need_manual = []

        for idx, original_song, success, match_list in search_results:
            if success:
                self.logger.info(f"找到歌曲: {original_song.name}")
                song_results[idx] = match_list[0]
            elif not match_list:
                self.logger.warning(f"未找到匹配: {original_song.name}")
                if not skip:
                    songs_need_manual.append((idx, original_song, []))
            elif not skip:
                songs_need_manual.append((idx, original_song, match_list))

        return song_results, songs_need_manual

    async def _handle_manual_selection(self, 
                                     manual_matches: List[Tuple[int, netease.NeteaseSong, List[apm.AppleSong]]], 
                                     song_results: List[Optional[apm.AppleSong]]):
        """
        处理未匹配歌曲的手动选择过程。
        """
        self.logger.info(f"\n✨ 处理 {len(manual_matches)} 首需要手动选择的歌曲...")
        choice_prompt = "请选择要添加的歌曲 (回车跳过, 0 手动搜索): "
        
        # 创建一个布局来分别显示进度条和内容
        layout = Layout()
        layout.split_column(
            Layout(name="content"),  # 内容区域
            Layout(name="progress", size=3),  # 进度条区域
        )
        
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold yellow]🎸 {task.description}"),
            BarColumn(complete_style="yellow", finished_style="green"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        )
        
        manual_task = progress.add_task("手动选择中...", total=len(manual_matches))
        
        with Live(layout, refresh_per_second=10, vertical_overflow="visible") as live:
            for idx, original_song, match_list in manual_matches:
                # 更新进度条
                progress.update(manual_task, 
                              description=f"手动选择中... {original_song.name[:30]}")
                
                # 创建表格
                from rich.table import Table
                from rich.panel import Panel
                from rich.text import Text
                
                # 创建标题文本
                title = Text()
                title.append("🎵 正在处理: ", style="bold cyan")
                title.append(f"{original_song.name}\n", style="bold yellow")
                title.append("👤 艺术家: ", style="bold cyan")
                title.append(f"{', '.join(original_song.artists)}\n", style="bold yellow")
                title.append("💿 专辑: ", style="bold cyan")
                title.append(f"{original_song.album}", style="bold yellow")
                
                # 创建匹配结果表格
                table = Table(show_header=True, header_style="bold magenta", 
                            title=title, title_justify="left")
                table.add_column("序号", style="dim", width=4)
                table.add_column("歌曲ID", width=12)
                table.add_column("歌曲名称", width=30)
                table.add_column("艺术家", width=20)
                table.add_column("专辑", width=30)
                
                if match_list:
                    for i, song in enumerate(match_list, 1):
                        table.add_row(
                            str(i),
                            song.id,
                            song.name,
                            song.artist,
                            song.album
                        )
                    content = table
                else:
                    content = Panel(
                        Text("❌ 没有找到匹配的歌曲", style="bold red"),
                        title=title
                    )
                
                # 更新布局
                layout["content"].update(content)
                layout["progress"].update(progress)
                
                # 处理歌曲选择
                await self._process_single_manual_selection(idx, original_song, match_list, song_results, choice_prompt)
                progress.update(manual_task, advance=1)

    async def _process_single_manual_selection(self,
                                            idx: int,
                                            original_song: netease.NeteaseSong,
                                            match_list: List[apm.AppleSong],
                                            song_results: List[Optional[apm.AppleSong]],
                                            choice_prompt: str):
        """
        处理单首歌曲的手动选择过程。
        
        参数:
            idx (int): 在song_results中的索引
            original_song (NeteaseSong): 原网易云音乐歌曲
            match_list (List[AppleSong]): 潜在匹配列表
            song_results (List[Optional[AppleSong]]): 存储选择结果的列表
            choice_prompt (str): 用户输入提示信息
        """
        self.logger.info(f"处理中: {original_song.name} - {','.join(original_song.artists)} - {original_song.album}")
        
        if match_list:
            song_results[idx] = await self._handle_match_list_selection(match_list, choice_prompt)
        else:
            song_results[idx] = await self._handle_manual_search(choice_prompt)

    async def _finalize_playlist(self, playlist: apm.ApplePlaylist, songs: List[apm.AppleSong]):
        """
        完成播放列表创建，显示结果并添加歌曲。
        """
        self.logger.info(f"\n🎉 最终歌曲列表 ({len(songs)} 首):")
        print_song_list(songs)
        console.print("[bold green]✅ 正在添加歌曲到播放列表...[/bold green]")
        await self.apple_music.add_songs_to_playlist(playlist.id, songs)
        console.print("[bold green]✨ 播放列表创建完成！[/bold green]")

    async def _handle_match_list_selection(self, match_list: List[apm.AppleSong], choice_prompt: str) -> Optional[apm.AppleSong]:
        """
        处理有匹配列表时的歌曲选择。
        
        参数:
            match_list (List[AppleSong]): 匹配的歌曲列表
            choice_prompt (str): 选择提示
            
        返回:
            Optional[AppleSong]: 选择的歌曲，如果跳过则返回 None
        """
        print_song_list(match_list)
        choice = get_choice(choice_prompt, len(match_list))
        
        if choice == 0:  # 用户选择手动搜索
            return await self._handle_manual_search(choice_prompt)
        elif choice:  # 用户选择了一个匹配
            return match_list[choice - 1]
        else:  # 用户选择跳过
            return None

    async def _handle_manual_search(self, choice_prompt: str) -> Optional[apm.AppleSong]:
        """
        处理手动搜索歌曲的过程。
        
        参数:
            choice_prompt (str): 选择提示
            
        返回:
            Optional[AppleSong]: 选择的歌曲，如果跳过则返回 None
        """
        while True:
            keyword = input("请输入搜索关键词 (回车跳过): ")
            if not keyword:  # 用户选择跳过
                return None
                
            match_list = await self.apple_music.stupid_search(keyword, "", "")
            if not match_list:
                print("未找到匹配的歌曲，请尝试其他关键词")
                continue
                
            print_song_list(match_list)
            choice = get_choice(choice_prompt, len(match_list))
            
            if choice == 0:  # 继续搜索
                continue
            elif choice:  # 用户选择了一个匹配
                return match_list[choice - 1]
            else:  # 用户选择跳过
                return None

    async def _setup_target_playlist_web(self, 
                                   target_playlist_id: str = None,
                                   target_playlist_name: str = None) -> apm.ApplePlaylist:
        """
        获取或创建目标Apple Music播放列表。
        
        参数:
            target_playlist_id: str - 目标播放列表ID
            target_playlist_name: str - 新建播放列表的名称
            
        返回:
            ApplePlaylist: 目标播放列表对象
        """
        # 获取现有播放列表
        await self.apple_music.retrive_playlists()
        
        # 如果提供了目标播放列表ID，尝试查找现有播放列表
        if target_playlist_id:
            for playlist in self.apple_music.playlists:
                if playlist.id == target_playlist_id:
                    self.logger.info(f"找到目标播放列表: {playlist.name}, ID: {playlist.id}")
                    return playlist
            raise Exception(f"找不到目标播放列表: {target_playlist_id}")
        
        # 如果没有提供ID，创建新播放列表
        playlist_name = target_playlist_name or f"网易云导入_{int(time.time())}"
        self.logger.info(f"创建新播放列表: {playlist_name}")
        await self.apple_music.new_playlist(playlist_name)
        
        # 等待歌单创建完成
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            await self.apple_music.retrive_playlists()
            for playlist in self.apple_music.playlists:
                if playlist.name == playlist_name:
                    self.logger.info(f"创建新播放列表成功: {playlist_name}, ID: {playlist.id}")
                    return playlist
            retry_count += 1
            await asyncio.sleep(2)
        
        raise Exception(f"创建播放列表失败: {playlist_name}")

    async def convert_play_list_web(self, source_playlist: netease.NeteasePlaylist, 
                                    progress_callback=None, 
                                    completed_callback=None,
                                    manual_selection_callback=None, 
                                    manual_selection_queue=None, 
                                    target_playlist_id=None, 
                                    target_playlist_name=None, mode="append"):
        """
        网页版歌单转换方法
        progress_callback: 进度回调函数, 参数1： progress: int, 参数2： current_song: dict, 参数3： result: dict = None
        current_song: {"name": str, "artist": str, "album": str}
        
        manual_selection_callback: 手动选择回调函数, 参数1： song_info: dict, 参数2： matches: list
        song_info: {"name": str, "artist": str, "album": str}
        matches: list[apple_song]
        apple_song: {"name": str, "artist": str, "album": str}
        
        completed_callback: 完成回调函数, 参数1： success_songs: list, 参数2： skipped_songs: list, 参数3： failed_songs: list
        success_songs: list[success_match]
        skipped_songs: list[skipped_match]
        failed_songs: list[failed_match]
        success_match: {originalName: str, originalArtist: str, matchedName: str, matchedArtist: str, matchedAlbum: str}
        skipped_match: {name: str, artist: str, album: str}
        failed_match: {name: str, artist: str, album: str, reason: str}
        """
        try:
            # 获取播放列表中的歌曲
            await self.netease_music.get_songs(source_playlist)
            total_songs = len(source_playlist.songs)
            self.logger.info(f"找到播放列表: {source_playlist.name}, 包含 {total_songs} 首歌曲")
            
            # 发送初始进度状态
            if progress_callback:
                await progress_callback(
                    0,  # progress
                    {   # current_song
                        "name": source_playlist.name,
                        "artist": "",
                        "album": ""
                    },
                    {   # result
                        "type": "progress",
                        "message": f"开始转换播放列表: {source_playlist.name}, 共 {total_songs} 首歌曲"
                    }
                )

            self.logger.info("开始转换播放列表...")
            
            # 设置目标播放列表
            target_playlist = await self._setup_target_playlist_web(
                target_playlist_id=target_playlist_id,
                target_playlist_name=target_playlist_name
            )

            converted_count = 0
            skip_count = 0
            error_count = 0
            selected_songs = []
            
            success_songs = []
            skipped_songs = []
            failed_songs = []

            for song in source_playlist.songs:
                try:
                    # 更新当前处理的歌曲信息
                    if progress_callback:
                        await progress_callback(
                            int((converted_count / total_songs) * 100),
                            {
                                "name": song.name,
                                "artist": ", ".join(song.artists),
                                "album": song.album
                            },
                            {
                                "type": "progress",
                                "message": "正在搜索匹配歌曲..."
                            }
                        )

                    # 搜索歌曲并检查匹配度
                    success, matches = await self.search_song_in_apm(song)
                    
                    if success:  # 找到匹配度足够高的歌曲
                        self.logger.info(f"找到匹配歌曲: {song.name}")
                        selected_song = matches[0]  # 自动选择第一个匹配度高的歌曲
                        selected_songs.append(selected_song)
                        if progress_callback:
                            await progress_callback(
                                int((converted_count / total_songs) * 100),
                                {
                                    "name": song.name,
                                    "artist": ", ".join(song.artists),
                                    "album": song.album
                                },
                                {
                                    "type": "progress",
                                    "message": "找到匹配歌曲",
                                    "matched_song": {
                                        "name": selected_song.name,
                                        "artist": selected_song.artist,
                                        "album": selected_song.album
                                    }
                                }
                            )
                        converted_count += 1
                        success_songs.append({
                            "originalName": song.name,
                            "originalArtist": ", ".join(song.artists),
                            "matchedName": selected_song.name,
                            "matchedArtist": selected_song.artist,
                            "matchedAlbum": selected_song.album
                        })
                        continue

                    # 如果没有找到匹配度足够高的歌曲，但有搜索结果
                    if matches:
                        if manual_selection_callback:
                            song_info = {
                                "name": song.name,
                                "artist": ", ".join(song.artists),
                                "album": song.album
                            }
                            send_matches = [{
                                "id": m.id,
                                "name": m.name,
                                "artist": m.artist,
                                "album": m.album
                            } for m in matches]
                            await manual_selection_callback(song_info, send_matches)
                            
                            # 等待用户选择
                            selected_id = await manual_selection_queue.get()
                            
                            if selected_id is None:  # 用户选择跳过
                                if progress_callback:
                                    await progress_callback(
                                        int((converted_count / total_songs) * 100),
                                        {
                                            "name": song.name,
                                            "artist": ", ".join(song.artists),
                                            "album": song.album
                                        },
                                        {
                                            "type": "progress",
                                            "message": "用户跳过"
                                        }
                                    )
                                skip_count += 1
                                skipped_songs.append({
                                    "name": song.name,
                                    "artist": ", ".join(song.artists),
                                    "album": song.album
                                })
                                continue
                            
                            # 用户选择了一个匹配
                            selected_song = next((s for s in matches if s.id == selected_id), None)
                            if selected_song:
                                selected_songs.append(selected_song)
                                if progress_callback:
                                    await progress_callback(
                                        int((converted_count / total_songs) * 100),
                                        {
                                            "name": song.name,
                                            "artist": ", ".join(song.artists),
                                            "album": song.album
                                        },
                                        {
                                            "type": "progress",
                                            "message": "找到匹配歌曲",
                                            "matched_song": {
                                                "name": selected_song.name,
                                                "artist": selected_song.artist,
                                                "album": selected_song.album
                                            }
                                        }
                                    )
                                converted_count += 1
                                success_songs.append({
                                    "originalName": song.name,
                                    "originalArtist": ", ".join(song.artists),
                                    "matchedName": selected_song.name,
                                    "matchedArtist": selected_song.artist,
                                    "matchedAlbum": selected_song.album
                                })
                    else:
                        self.logger.warning(f"未找到匹配的歌曲: {song.name} - {', '.join(song.artists)}")
                        if progress_callback:
                            await progress_callback(
                                int((converted_count / total_songs) * 100),
                                {
                                    "name": song.name,
                                    "artist": ", ".join(song.artists),
                                    "album": song.album
                                },
                                {
                                    "type": "progress",
                                    "message": "未找到匹配歌曲"
                                }
                            )
                        skip_count += 1
                        skipped_songs.append({
                            "name": song.name,
                            "artist": ", ".join(song.artists),
                            "album": song.album
                        })
                    converted_count += 1

                except asyncio.TimeoutError:
                    self.logger.error(f"搜索超时: {song.name}")
                    if progress_callback:
                        await progress_callback(
                            int((converted_count / total_songs) * 100),
                            {
                                "name": song.name,
                                "artist": ", ".join(song.artists),
                                "album": song.album
                            },
                            {
                                "type": "progress",
                                "message": "搜索超时"
                            }
                        )
                    error_count += 1
                    failed_songs.append({
                        "name": song.name,
                        "artist": ", ".join(song.artists),
                        "album": song.album,
                        "reason": "搜索超时"
                    })
                    continue
                except Exception as e:
                    self.logger.error(f"搜索歌曲出错: {str(e)}\n{traceback.format_exc()}")
                    if progress_callback:
                        await progress_callback(
                            int((converted_count / total_songs) * 100),
                            {
                                "name": song.name,
                                "artist": ", ".join(song.artists),
                                "album": song.album
                            },
                            {
                                "type": "progress",
                                "message": f"处理失败: {str(e)}"
                            }
                        )
                    error_count += 1
                    failed_songs.append({
                        "name": song.name,
                        "artist": ", ".join(song.artists),
                        "album": song.album,
                        "reason": str(e)
                    })
                    continue

            # 批量添加歌曲到播放列表
            if selected_songs:
                try:
                    if mode == "override":
                        await self.apple_music.replace_songs_to_playlist(target_playlist, selected_songs)
                    else:  # append mode
                        await self.apple_music.add_songs_to_playlist(target_playlist.id, selected_songs)
                    
                    # 发送完成进度
                    if progress_callback:
                        await progress_callback(
                            100,
                            {
                                "name": "完成",
                                "artist": "",
                                "album": ""
                            },
                            {
                                "type": "progress",
                                "message": f"成功添加 {len(selected_songs)} 首歌曲到播放列表"
                            }
                        )
                    
                    # 最终完成消息
                    await completed_callback(
                        success_songs,
                        skipped_songs,
                        failed_songs
                    )
                    
                    return {
                        "status": "success",
                        "playlist_id": target_playlist.id,
                        "added_count": len(selected_songs)
                    }
                except Exception as e:
                    self.logger.error(f"添加歌曲到播放列表失败: {str(e)}")
                    if progress_callback:
                        await progress_callback(
                            100,
                            {
                                "name": "错误",
                                "artist": "",
                                "album": ""
                            },
                            {
                                "type": "progress",
                                "message": f"添加歌曲到播放列表失败: {str(e)}"
                            }
                        )
                    return {"error": f"添加歌曲到播放列表失败: {str(e)}"}
            else:
                if progress_callback:
                    await progress_callback(
                        100,
                        {
                            "name": "完成",
                            "artist": "",
                            "album": ""
                        },
                        {
                            "type": "progress",
                            "message": "没有找到任何匹配的歌曲"
                        }
                    )
                return {"error": "没有找到任何匹配的歌曲"}
        except Exception as e:
            self.logger.error(f"转换播放列表失败: {str(e)}\n{traceback.format_exc()}")
            if progress_callback:
                await progress_callback(
                    100,
                    {
                        "name": "错误",
                        "artist": "",
                        "album": ""
                    },
                    {
                        "type": "progress",
                        "message": f"转换播放列表失败: {str(e)}"
                    }
                )
            return {"error": f"转换播放列表失败: {str(e)}"}




if __name__ == '__main__':
    async def main():
        netease_music = None
        apple_music = None
        try:
            netease_music = netease.NeteaseMusic()
            await netease_music.login("/home/damaoooo/Downloads/Playlist-Converter/src/Netease/music_id")
            
            with open("/home/damaoooo/Downloads/Playlist-Converter/src/Apple/config.json", "r") as f:
                config = json.load(f)
            apple_music = apm.AppleMusic(user_token=config["user_token"], dev_token=config["jwt"])
            await apple_music.login()
            
            converter = Converter(netease_music=netease_music, apple_music=apple_music)

            await converter.netease_music.retrive_playlists()
            converter.netease_music.show_playlists(converter.netease_music.created_playlists)
            choice = get_choice("请选择要转换的播放列表: ", 
                              len(converter.netease_music.created_playlists))
            test_playlist = converter.netease_music.created_playlists[choice-1]
            await converter.netease_music.get_songs(test_playlist)
            await converter.convert_play_list(test_playlist)
        finally:
            # 确保关闭所有会话
            if netease_music is not None:
                try:
                    await netease_music.close()
                except AttributeError:
                    pass  # 如果没有 close 方法，就忽略
            
            if apple_music is not None:
                try:
                    await apple_music.close()
                except AttributeError:
                    pass  # 如果没有 close 方法，就忽略

    # 使用 try-finally 来确保即使发生异常也能正确清理
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")


