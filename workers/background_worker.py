from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal

from services.video_provider import VideoProvider
from utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_INTERVAL_MS = 24 * 60 * 60 * 1000  # 24 h
#: Hold off the first heavy API scan so the UI's thumbnails load first.
_INITIAL_DELAY_MS = 6000


class BackgroundWorker(QThread):
    """Periodically checks for new videos and emits new_videos_found(count)."""

    new_videos_found = pyqtSignal(int)

    def __init__(
        self,
        provider: VideoProvider,
        interval_ms: int = _DEFAULT_INTERVAL_MS,
        initial_delay_ms: int = _INITIAL_DELAY_MS,
    ):
        super().__init__()
        self._provider = provider
        self._interval_ms = interval_ms
        self._initial_delay_ms = initial_delay_ms

    def run(self):
        # Both timers must fire _check on THIS worker thread, never on the GUI
        # thread. Because the worker (a QObject) lives on the main thread, an
        # auto/queued connection would run the (blocking, ~minute-long) API scan
        # on the main thread and freeze the window. DirectConnection forces the
        # slot to execute in the emitting thread – this one.
        periodic = QTimer()
        periodic.setInterval(self._interval_ms)
        periodic.timeout.connect(self._check, Qt.ConnectionType.DirectConnection)
        periodic.start()

        # Delay the first scan so freshly-rendered tiles fetch their thumbnails
        # without competing with the worker's heavy API traffic.
        first = QTimer()
        first.setSingleShot(True)
        first.setInterval(self._initial_delay_ms)
        first.timeout.connect(self._check, Qt.ConnectionType.DirectConnection)
        first.start()

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
