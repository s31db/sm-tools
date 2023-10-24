import pyautogui
from pynput.keyboard import Controller, Key
from time import sleep


def capture(prefix: str, pages: int):
    location = [
        pyautogui.locateOnScreen("tmpagile/img.png"),
        pyautogui.locateOnScreen("tmpagile/img_1.png"),
        pyautogui.locateOnScreen("tmpagile/img_2.png"),
    ]

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
            pyautogui.screenshot(prefix + num + ".png", region=locate)
        keyboard.press(Key.page_down)
        keyboard.release(Key.page_down)
        sleep(0.3)


if __name__ == "__main__":
    capture(prefix="tmpagile/dor/dor_", pages=25)
