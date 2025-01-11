import unittest
from unittest.mock import patch, mock_open
from src.Netease import NeteaseMusic, NeteasePlaylist, NeteaseSong

class TestNeteaseMusic(unittest.TestCase):

    @patch('src.Netease.login.LoginViaCookie')
    def test_login_success(self, mock_login):
        mock_login.return_value = {
            'code': 200,
            'result': {
                'content': {
                    'profile': {
                        'userId': 12345,
                        'nickname': 'testuser'
                    }
                }
            }
        }
        netease = NeteaseMusic()
        netease.login('src/Netease/music_id')
        self.assertEqual(netease.uid, 12345)
        self.assertEqual(netease.nickname, 'testuser')

    @patch('src.Netease.login.LoginViaCookie')
    def test_login_failure(self, mock_login):
        mock_login.return_value = {'code': 400}
        netease = NeteaseMusic()
        netease.login('xxxxxxx')
        self.assertEqual(netease.uid, 0)
        self.assertEqual(netease.nickname, '')

    @patch('src.Netease.login.LoginViaCookie')
    def test_login_with_file(self, mock_login):
        mock_login.return_value = {
            'code': 200,
            'result': {
                'content': {
                    'profile': {
                        'userId': 12345,
                        'nickname': 'testuser'
                    }
                }
            }
        }
        netease = NeteaseMusic()
        netease.login('src/Netease/music_id')
        self.assertEqual(netease.uid, 12345)
        self.assertEqual(netease.nickname, 'testuser')

    @patch('src.Netease.apis.user.GetUserPlaylists')
    def test_get_playlist(self, mock_get_playlists):
        mock_get_playlists.return_value = {
            'playlist': [
                {'name': 'Playlist1', 'id': 1, 'userId': 12345, 'createTime': 1609459200000},
                {'name': 'Playlist2', 'id': 2, 'userId': 67890, 'createTime': 1609459200000}
            ]
        }
        netease = NeteaseMusic()
        netease.uid = 12345
        netease.get_playlist()
        self.assertEqual(len(netease.created_playlists), 1)
        self.assertEqual(len(netease.subscribed_playlists), 1)

    @patch('src.Netease.apis.playlist.GetPlaylistInfo')
    def test_get_songs(self, mock_get_songs):
        mock_get_songs.return_value = {
            'playlist': {
                'tracks': [
                    {'id': 1, 'name': 'Song1', 'ar': [{'name': 'Artist1'}], 'al': {'name': 'Album1'}},
                    {'id': 2, 'name': 'Song2', 'ar': [{'name': 'Artist2'}], 'al': {'name': 'Album2'}}
                ]
            }
        }
        playlist = NeteasePlaylist(name='Playlist1', id=1, creator_id=12345, create_time=1609459200000)
        netease = NeteaseMusic()
        netease.get_songs(playlist)
        self.assertEqual(len(playlist.songs), 2)
        self.assertEqual(playlist.songs[0].name, 'Song1')
        self.assertEqual(playlist.songs[1].name, 'Song2')

if __name__ == '__main__':
    unittest.main()