from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import asyncio
import sys
import os
import logging
import traceback
from pathlib import Path

# 设置日志
logger = logging.getLogger("api")
logger.setLevel(logging.DEBUG)

# 文件处理器
fh = logging.FileHandler('api.log')
fh.setLevel(logging.DEBUG)
fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(fh_formatter)
logger.addHandler(fh)

# 控制台处理器
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch_formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(ch_formatter)
logger.addHandler(ch)

# 不再需要手动添加路径，因为我们已经在 PYTHONPATH 中设置了
from Apple import apm
from Netease import netease
from converter import Converter
from .get_dev_token import get_dev_token

app = FastAPI()

# 修改静态文件路径
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent.parent / "static")), name="static")

# 存储活动的WebSocket连接
websocket_connections: Dict[str, WebSocket] = {}

class TokenInput(BaseModel):
    neteaseToken: str
    appleToken: str

class PlaylistConvert(BaseModel):
    playlist_id: str | int
    session_id: str
    playlist_name: str | None = None
    target_playlist_id: str | None = None
    target_playlist_name: str | None = None
    mode: str = "new"  # "new" or "override"

class ManualSearch(BaseModel):
    keyword: str
    session_id: str

class SongSelection(BaseModel):
    song_id: str
    session_id: str

# 存储用户会话信息
class UserSession:
    def __init__(self):
        self.netease_music: netease.NeteaseMusic = None
        self.apple_music: apm.AppleMusic = None
        self.converter: Converter = None
        self.current_playlist = None
        self.manual_selection_queue = asyncio.Queue()
        self.websocket = None

# 全局会话存储
sessions: Dict[str, UserSession] = {}

@app.get("/")
async def read_root():
    return FileResponse(str(Path(__file__).parent.parent / "static" / "index.html"))

@app.post("/api/login")
async def login(token_input: TokenInput):
    try:
        logger.info("开始处理登录请求")
        
        # 初始化网易云音乐客户端
        logger.debug("初始化网易云音乐客户端")
        netease_music = netease.NeteaseMusic()
        await netease_music.login(token_input.neteaseToken)
        
        # 初始化Apple Music客户端
        logger.debug("初始化Apple Music客户端")
        try:
            dev_token = get_dev_token()
        except Exception as e:
            logger.error(f"获取开发者令牌失败: {str(e)}")
            raise HTTPException(status_code=400, detail=f"获取Apple Music开发者令牌失败: {str(e)}")
            
        try:
            apple_music = apm.AppleMusic(user_token=token_input.appleToken, dev_token=dev_token)
            await apple_music.login()
        except Exception as e:
            logger.error(f"Apple Music登录失败: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Apple Music登录失败: {str(e)}")
        
        # 准备播放列表数据
        logger.debug("准备播放列表数据")
        playlists = [
            {
                "id": p.id,
                "name": p.name,
                "trackCount": len(p.songs) if hasattr(p, 'songs') else 0
            }
            for p in netease_music.created_playlists
        ]
        
        # 创建会话ID
        session_id = token_input.neteaseToken
        
        # 存储会话信息
        session = UserSession()
        session.netease_music = netease_music
        session.apple_music = apple_music
        session.converter = Converter(netease_music, apple_music)
        sessions[session_id] = session
        
        logger.info(f"登录成功，创建会话: {session_id[:8]}...")
        return {"session_id": session_id, "playlists": playlists}
    except Exception as e:
        error_msg = f"登录失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if session_id not in sessions:
        await websocket.close(code=1000)
        return
        
    session = sessions[session_id]
    session.websocket = websocket
    websocket_connections[session_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            # 处理WebSocket消息
    except WebSocketDisconnect:
        if session_id in websocket_connections:
            del websocket_connections[session_id]

async def send_progress(session_id: str, progress: int, current_song: dict, result: dict = None):
    if session_id in websocket_connections:
        websocket: WebSocket = websocket_connections[session_id]
        try:
            await websocket.send_json({
                "type": "progress",
                "progress": progress,
                "current_song": current_song,
                "result": result
            })
        except:
            pass

async def send_manual_selection(session_id: str, song_info: dict, matches: list):
    if session_id in websocket_connections:
        websocket: WebSocket = websocket_connections[session_id]
        try:
            await websocket.send_json({
                "type": "manual_selection",
                "song_info": song_info,
                "matches": matches
            })
        except:
            pass

async def send_completed(session_id: str, success_songs: list, skip_songs: list, failed_songs: list):
    if session_id in websocket_connections:
        websocket: WebSocket = websocket_connections[session_id]
        try:
            await websocket.send_json({
                "type": "completed",
                "successSongs": success_songs,
                "skippedSongs": skip_songs,
                "failedSongs": failed_songs
            })
        except:
            pass

@app.post("/api/convert_playlist")
async def convert_playlist(playlist_data: PlaylistConvert):
    if playlist_data.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session: UserSession = sessions[playlist_data.session_id]
    
    # 创建一个异步队列用于手动选择
    session.manual_selection_queue = asyncio.Queue()
    
    try:
        # 获取要转换的播放列表
        playlist = None
        for p in session.netease_music.created_playlists:
            if p.id == playlist_data.playlist_id:
                playlist = p
                break
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # 获取播放列表中的歌曲
        await session.netease_music.get_songs(playlist)
        
        # 开始转换
        result = await session.converter.convert_play_list_web(
            playlist,
            progress_callback=lambda p, s, r=None: send_progress(playlist_data.session_id, p, s, r),
            completed_callback=lambda success_count, skip_count, error_count: send_completed(playlist_data.session_id, success_count, skip_count, error_count),
            manual_selection_callback=lambda song_info, matches: send_manual_selection(playlist_data.session_id, song_info, matches),
            manual_selection_queue=session.manual_selection_queue,
            target_playlist_id=playlist_data.target_playlist_id,
            target_playlist_name=playlist_data.target_playlist_name,
            mode=playlist_data.mode
        )
        
        return {"status": "success", "result": result}
    except Exception as e:
        import traceback
        logger.error(f"转换播放列表失败: {str(e)}\n{traceback.format_exc()}")
        return {"error": str(e)}

@app.post("/api/select_song")
async def select_song(selection: SongSelection):
    if selection.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[selection.session_id]
    await session.manual_selection_queue.put(selection.song_id)
    return {"status": "success"}

@app.post("/api/skip_song")
async def skip_song(session_data: dict):
    if "session_id" not in session_data:
        raise HTTPException(status_code=400, detail="Missing session_id")
        
    session_id = session_data["session_id"]
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    await session.manual_selection_queue.put(None)
    return {"status": "success"}

@app.post("/api/manual_search")
async def manual_search(search_data: ManualSearch):
    if search_data.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[search_data.session_id]
    results = await session.apple_music.stupid_search(search_data.keyword, "", "")
    return {
        "matches": [
            {
                "id": song.id,
                "name": song.name,
                "artist": song.artist,
                "album": song.album
            }
            for song in results
        ]
    }

@app.get("/api/apple-playlists/{session_id}")
async def get_apple_playlists(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    await session.apple_music.retrive_playlists()
    
    return {
        "playlists": [
            {
                "id": p.id,
                "name": p.name
            }
            for p in session.apple_music.playlists
        ]
    }

@app.on_event("shutdown")
async def shutdown_event():
    # 清理所有会话
    for session in sessions.values():
        if session.netease_music:
            await session.netease_music.close()
        if session.apple_music:
            await session.apple_music.close() 