# https://stackoverflow.com/questions/34322132/copy-image-to-clipboard

import win32clipboard
from io import BytesIO
from PIL import Image


def send_data_to_clipboard(data, clip_type=win32clipboard.CF_DIB):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()


def send_to_clipboard_image(filepath):
    image = Image.open(filepath)
    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    send_data_to_clipboard(data)
