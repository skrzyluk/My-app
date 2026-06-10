from PyQt6.QtCore import QThread, QTimer, pyqtSignal

from services.video_provider import VideoProvider
from utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_INTERVAL_MS = 24 * 60 * 60 * 1000  # 24 h


class BackgroundWorker(QThread):
    """Periodically checks for new videos and emits new_videos_found(count)."""

    new_videos_found = pyqtSignal(int)

    def __init__(self, provider: VideoProvider, interval_ms: int = _DEFAULT_INTERVAL_MS):
        super().__init__()
        self._provider = provider
        self._interval_ms = interval_ms

    def run(self):
        timer = QTimer()
        timer.setInterval(self._interval_ms)
        timer.timeout.connect(self._check)
        timer.start()
        self._check()  # immediate first check
        self.exec()    # run thread's event loop until quit() is called

    def _check(self):
        try:
            count = self._provider.check_for_new_videos("today")
            logger.debug("Background check: %d new video(s) today.", count)
            if count > 0:
                self.new_videos_found.emit(count)
        except Exception:
            logger.exception("Background video check failed.")

    def stop(self):
        """Stop the periodic timer and shut down the thread."""
        self.quit()
        self.wait(3000)
