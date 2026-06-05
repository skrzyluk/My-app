from utils.logger import get_logger

logger = get_logger(__name__)


def _video_noun(count: int) -> str:
    if count == 1:
        return "1 nowy film"
    if 2 <= count <= 4:
        return f"{count} nowe filmy"
    return f"{count} nowych filmów"


class NotificationService:
    APP_ID = "YouTube Notifier"

    def show_new_videos(self, count: int) -> None:
        """Show a Windows toast notification about new videos."""
        if count <= 0:
            return
        try:
            from winotify import Notification, audio
            notif = Notification(
                app_id=self.APP_ID,
                title="YouTube Notifier",
                msg=f"🎬 {_video_noun(count)} z Twoich subskrypcji!",
                duration="short",
            )
            notif.set_audio(audio.Default, loop=False)
            notif.show()
            logger.info("Toast notification shown (%d videos).", count)
        except Exception:
            logger.exception("Failed to show toast notification.")
