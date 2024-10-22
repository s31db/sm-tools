import matplotlib.pyplot as plt
from base64 import b64encode
from io import BytesIO
from PIL import Image
from HtmlClipboard import put_html
from typing_extensions import Self
from helpers.clipboard import send_to_clipboard_image


class Chart:
    _title: str
    _path_export: str

    def __init__(self, *args: str, **kwargs: str | bool | int | dict | list) -> None:
        if args:
            self._title = args[0]
        for key, value in kwargs.items():
            setattr(self, "_" + key, value)

    def title(self, title: str) -> Self:
        self._title = title
        return self

    def copy_clipboard(self, data) -> Self:
        send_to_clipboard_image(data)
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

    def sequence(
        self,
        filenames: list[str],
        format_img: str = "gif",
        duration: int = 3,
        loop: int | None = 1,
    ) -> Self:
        for filename in filenames:
            img = Image.open(filename)
            img.verify()
        frames = [Image.open(filename) for filename in filenames]
        # set the first frame as last image
        frame_one = frames[-1]
        if loop is None:
            frame_one.save(
                f"{self._path_export}/{self._title}.{format_img}",
                format=format_img,
                save_all=True,
                append_images=frames,
                duration=duration,
            )
        else:
            frame_one.save(
                f"{self._path_export}/{self._title}.{format_img}",
                format=format_img,
                save_all=True,
                append_images=frames,
                duration=duration,
                loop=loop,
            )
        return self
