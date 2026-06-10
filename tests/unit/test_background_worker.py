import pytest
from unittest.mock import MagicMock

from workers.background_worker import BackgroundWorker


@pytest.fixture
def mock_provider():
    p = MagicMock()
    p.check_for_new_videos.return_value = 0
    return p


@pytest.fixture
def worker(mock_provider):
    return BackgroundWorker(mock_provider, interval_ms=60_000)


class TestCheck:
    def test_emits_signal_when_videos_found(self, qtbot, worker):
        worker._provider.check_for_new_videos.return_value = 5
        with qtbot.waitSignal(worker.new_videos_found, timeout=500) as blocker:
            worker._check()
        assert blocker.args == [5]

    def test_no_signal_when_zero_videos(self, qtbot, worker):
        worker._provider.check_for_new_videos.return_value = 0
        with qtbot.assertNotEmitted(worker.new_videos_found, wait=200):
            worker._check()

    def test_emits_signal_when_one_video(self, qtbot, worker):
        worker._provider.check_for_new_videos.return_value = 1
        with qtbot.waitSignal(worker.new_videos_found, timeout=500) as blocker:
            worker._check()
        assert blocker.args == [1]

    def test_does_not_raise_on_provider_exception(self, qtbot, worker):
        worker._provider.check_for_new_videos.side_effect = RuntimeError("API down")
        worker._check()  # must not raise

    def test_calls_provider_with_today_period(self, worker):
        worker._check()
        worker._provider.check_for_new_videos.assert_called_once_with("today")

    def test_no_signal_on_provider_exception(self, qtbot, worker):
        worker._provider.check_for_new_videos.side_effect = RuntimeError("fail")
        with qtbot.assertNotEmitted(worker.new_videos_found, wait=200):
            worker._check()


class TestInterval:
    def test_default_interval_is_24h(self, mock_provider):
        w = BackgroundWorker(mock_provider)
        assert w._interval_ms == 24 * 60 * 60 * 1000

    def test_custom_interval_stored(self, mock_provider):
        w = BackgroundWorker(mock_provider, interval_ms=5000)
        assert w._interval_ms == 5000


class TestStop:
    def test_stop_does_not_raise_when_not_running(self, worker):
        worker.stop()  # never started — must not raise

    def test_stop_quits_running_worker(self, qtbot, mock_provider):
        w = BackgroundWorker(mock_provider, interval_ms=999_999)
        mock_provider.check_for_new_videos.return_value = 0
        w.start()
        qtbot.waitUntil(lambda: w.isRunning(), timeout=1000)
        w.stop()
        assert not w.isRunning()
