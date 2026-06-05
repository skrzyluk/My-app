"""Generate resources/icon.ico — YouTube-style red rounded square with white play triangle."""
import io
import struct
import sys
from pathlib import Path

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap, QPolygon
from PyQt6.QtWidgets import QApplication


def _render_frame(size: int) -> bytes:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    radius = max(size // 6, 2)
    p.setBrush(QColor(229, 57, 53))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRect(0, 0, size, size), radius, radius)

    tri = QPolygon([
        QPoint(int(size * 0.33), int(size * 0.22)),
        QPoint(int(size * 0.33), int(size * 0.78)),
        QPoint(int(size * 0.80), int(size * 0.50)),
    ])
    p.setBrush(QColor(255, 255, 255))
    p.drawPolygon(tri)
    p.end()

    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    pm.save(buf, "PNG")
    buf.close()
    return bytes(ba)


def build_ico(sizes: tuple[int, ...] = (16, 32, 48, 256)) -> bytes:
    images = [(s, _render_frame(s)) for s in sizes]
    n = len(images)
    header_size = 6 + n * 16

    offsets: list[int] = []
    cur = header_size
    for _, data in images:
        offsets.append(cur)
        cur += len(data)

    out = io.BytesIO()
    out.write(struct.pack("<HHH", 0, 1, n))
    for i, (sz, data) in enumerate(images):
        w = sz if sz < 256 else 0
        h = sz if sz < 256 else 0
        out.write(struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offsets[i]))
    for _, data in images:
        out.write(data)
    return out.getvalue()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    out_path = Path("resources/icon.ico")
    out_path.write_bytes(build_ico())
    print(f"Icon written: {out_path}  ({out_path.stat().st_size} bytes)")
