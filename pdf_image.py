import pyautogui
from pynput.keyboard import Controller, Key
from time import sleep
from PIL import ImageGrab, Image
from pathlib import Path
from os import walk


def capture(path: str, prefix: str, pages: int, nb_location: int = 1):
    Path(path).mkdir(parents=True, exist_ok=True)
    location = [
        pyautogui.locateOnScreen("../tmpagile/img.png"),
    ]
    for i in range(1, nb_location):
        location.append(pyautogui.locateOnScreen(f"../tmpagile/img_{i}.png"))

    # print(location)
    keyboard = Controller()
    sleep(2)
    # prefix = 'tmpagile/dor/dor_'
    # prefix = 'tmpagile/daily_scrum_for_hell_'
    # prefix = 'tmpagile/biais_cognitif_'
    # prefix = 'tmpagile/debriefing_kards_'
    for i in range(0, pages * len(location), len(location)):
        for nb, locate in enumerate(location):
            n = i + nb
            num = "0" + str(n) if n < 10 else str(n)
            pyautogui.screenshot(f"{path}/{prefix}{num}.png", region=locate)
        keyboard.press(Key.page_down)
        keyboard.release(Key.page_down)
        sleep(0.3)


def prepare(fp):
    im = ImageGrab.grabclipboard()
    im.save(fp=fp, format="PNG")


def landing(path: str):
    images = []
    images_path = []
    for filename in [file for file in next(walk(path))[2] if file.endswith(".png")]:
        img = Image.open(f"{path}/{filename}")
        img.verify()
        images.append(img)
        images_path.append(f"{path}/{filename}")
    print(images_path)
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new("RGB", (total_width, max_height))

    x_offset = 0
    # for im in images:
    for filename in images_path:
        im = Image.open(filename)
        # im.verify()
        # im = im.convert("RGB")
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]

    new_im.save(f"{path}/test.png")


def capt():
    capture(
        path="../tmpagile/dor",
        prefix="dor_",
        pages=25,
        nb_location=1,
    )


if __name__ == "__main__":
    # prepare("../tmpagile/img.png")
    # prepare("../tmpagile/img_1.png")
    # prepare("../tmpagile/img_2.png")
    capt()
    landing("../tmpagile/dor")
