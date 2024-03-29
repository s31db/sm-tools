import matplotlib.pyplot as plt
import win32clipboard
from base64 import b64encode
from io import BytesIO
from PIL import Image
from HtmlClipboard import put_html
from typing import Self


def send_to_clipboard(clip_type: int, data: bytes) -> None:
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()


class Chart:
    _title: str

    def __init__(self, *args: str, **kwargs: str | bool) -> None:
        if args:
            self._title = args[0]
        for key, value in kwargs.items():
            setattr(self, "_" + key, value)

    def title(self, title: str) -> Self:
        self._title = title
        return self

    def copy_clipboard_img(self, filepath: str) -> Self:
        image = Image.open(filepath)
        output = BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        send_to_clipboard(win32clipboard.CF_DIB, data)
        return self

    def img64(self, format_img: str = "png") -> tuple[str, Self]:
        bytes_io_img = BytesIO()
        plt.savefig(bytes_io_img, format=format_img, dpi=90)
        bytes_io_img.seek(0)
        return b64encode(bytes_io_img.read()).decode("utf-8"), self

    def chart_html(self) -> str:
        i = self.img64()[0]
        return '<img src="data:image/png;base64,' + i + '" alt="" />'

    def copy_html(self, source: str = "S@M") -> Self:
        tab = self.chart_html()
        put_html(tab, source=source)
        return self

    def show(self) -> Self:
        plt.show()
        return self

    def save(self, filepath: str, format_img: str = "png", dpi: int = 90) -> Self:
        plt.savefig(filepath, format=format_img, dpi=dpi)
        return self
