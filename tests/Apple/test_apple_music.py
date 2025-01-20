import unittest
from unittest.mock import patch, MagicMock
from src.Apple.apm import AppleMusic, ApplePlaylist, AppleSong

class TestAppleMusic(unittest.TestCase):

    @patch('src.Apple.apm.requests.get')
    def test_login_success(self, mock_get):
        mock_get.return_value.status_code = 200
        apple_music = AppleMusic("user_token", "dev_token")
        response = apple_music.login()
        self.assertIsNone(response)
        mock_get.assert_called_once_with("https://api.music.apple.com/v1/me/library/playlists", headers=apple_music.header_with_user)

    @patch('src.Apple.apm.requests.get')
    def test_login_failure(self, mock_get):
        mock_get.return_value.status_code = 401
        apple_music = AppleMusic("user_token", "dev_token")
        response = apple_music.login()
        self.assertIsNone(response)
        mock_get.assert_called_once_with("https://api.music.apple.com/v1/me/library/playlists", headers=apple_music.header_with_user)

    @patch('src.Apple.apm.requests.get')
    def test_get_playlists_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": []}
        apple_music = AppleMusic("user_token", "dev_token")
        response = apple_music.retrive_playlists()
        self.assertIsNone(response)
        mock_get.assert_called_once_with("https://api.music.apple.com/v1/me/library/playlists", headers=apple_music.header_with_user)

    @patch('src.Apple.apm.requests.get')
    def test_get_playlists_failure(self, mock_get):
        mock_get.return_value.status_code = 401
        apple_music = AppleMusic("user_token", "dev_token")
        response = apple_music.retrive_playlists()
        self.assertIsNone(response)
        mock_get.assert_called_once_with("https://api.music.apple.com/v1/me/library/playlists", headers=apple_music.header_with_user)

    @patch('src.Apple.apm.requests.post')
    def test_new_playlist_success(self, mock_post):
        mock_post.return_value.status_code = 201
        apple_music = AppleMusic("user_token", "dev_token")
        response = apple_music.new_playlist("Test Playlist", "Test Description")
        self.assertIsNone(response)
        mock_post.assert_called_once()

    @patch('src.Apple.apm.requests.post')
    def test_new_playlist_failure(self, mock_post):
        mock_post.return_value.status_code = 400
        apple_music = AppleMusic("user_token", "dev_token")
        response = apple_music.new_playlist("Test Playlist", "Test Description")
        self.assertIsNone(response)
        mock_post.assert_called_once()

    @patch('src.Apple.apm.requests.delete')
    def test_delete_playlist_success(self, mock_delete):
        mock_delete.return_value.status_code = 204
        apple_music = AppleMusic("user_token", "dev_token")
        playlist = ApplePlaylist(id="123", name="Test Playlist", create_time="2023-01-01")
        response = apple_music.delete_playlist(playlist)
        self.assertIsNone(response)
        mock_delete.assert_called_once_with("https://amp-api.music.apple.com/v1/me/library/playlists/123", headers=apple_music.header_with_user)

    @patch('src.Apple.apm.requests.delete')
    def test_delete_playlist_failure(self, mock_delete):
        mock_delete.return_value.status_code = 400
        apple_music = AppleMusic("user_token", "dev_token")
        playlist = ApplePlaylist(id="123", name="Test Playlist", create_time="2023-01-01")
        response = apple_music.delete_playlist(playlist)
        self.assertIsNone(response)
        mock_delete.assert_called_once_with("https://amp-api.music.apple.com/v1/me/library/playlists/123", headers=apple_music.header_with_user)

if __name__ == '__main__':
    unittest.main()
