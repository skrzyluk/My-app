import pytest
from unittest.mock import patch, MagicMock, call

from services.notification_service import NotificationService, _video_noun


class TestVideoNoun:
    def test_one_video(self):
        assert _video_noun(1) == "1 nowy film"

    def test_two_videos(self):
        assert "2 nowe filmy" == _video_noun(2)

    def test_four_videos(self):
        assert "4 nowe filmy" == _video_noun(4)

    def test_five_videos(self):
        assert "5 nowych filmów" == _video_noun(5)

    def test_twenty_one_videos(self):
        assert "21 nowych filmów" == _video_noun(21)


class TestShowNewVideos:
    @pytest.fixture
    def service(self):
        return NotificationService()

    @pytest.fixture
    def mock_winotify(self):
        mock_notif_cls = MagicMock()
        mock_notif = MagicMock()
        mock_notif_cls.return_value = mock_notif
        mock_audio = MagicMock()
        with patch.dict("sys.modules", {
            "winotify": MagicMock(Notification=mock_notif_cls, audio=mock_audio),
        }):
            yield mock_notif_cls, mock_notif, mock_audio

    def test_shows_notification_for_positive_count(self, service, mock_winotify):
        notif_cls, notif, _ = mock_winotify
        service.show_new_videos(3)
        notif_cls.assert_called_once()
        notif.show.assert_called_once()

    def test_notification_title(self, service, mock_winotify):
        notif_cls, _, _ = mock_winotify
        service.show_new_videos(2)
        _, kwargs = notif_cls.call_args
        assert kwargs["title"] == "YouTube Notifier"

    def test_notification_contains_count(self, service, mock_winotify):
        notif_cls, _, _ = mock_winotify
        service.show_new_videos(7)
        _, kwargs = notif_cls.call_args
        assert "7" in kwargs["msg"]

    def test_no_notification_for_zero(self, service, mock_winotify):
        notif_cls, notif, _ = mock_winotify
        service.show_new_videos(0)
        notif_cls.assert_not_called()
        notif.show.assert_not_called()

    def test_no_notification_for_negative(self, service, mock_winotify):
        notif_cls, notif, _ = mock_winotify
        service.show_new_videos(-1)
        notif_cls.assert_not_called()

    def test_app_id_set(self, service, mock_winotify):
        notif_cls, _, _ = mock_winotify
        service.show_new_videos(1)
        _, kwargs = notif_cls.call_args
        assert kwargs["app_id"] == "YouTube Notifier"

    def test_does_not_raise_when_winotify_unavailable(self, service):
        with patch.dict("sys.modules", {"winotify": None}):
            service.show_new_videos(5)  # must not raise
