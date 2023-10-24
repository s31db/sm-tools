"""Simplify configparser on use parametrage.ini
https://docs.python.org/3/library/configparser.html
"""

from configparser import ConfigParser, SectionProxy
import os


def config(path: str | None = None) -> ConfigParser:
    if path is None:
        path = os.path.expanduser("~/config_sm_tools.ini")
    conf = ConfigParser()
    conf.read(path, encoding="utf-8")
    return conf


SectionProxy.__getattr__ = SectionProxy.__getitem__  # type: ignore
ConfigParser.__getattr__ = (  # type: ignore
    lambda self, key: ConfigParser.defaults(self).get(key)
    if key in ConfigParser.defaults(self)
    else ConfigParser.__getitem__(self, key)
)


def test_config():
    c = config("tests/test_resources/test_config.ini")
    assert c["PROJECT_1"]["path_project"] == "/PROJECT_1"
    tmp = "C:/tmp"
    assert c["PROJECT_1"]["path_tmp"] == tmp
    assert c.PROJECT_1["path_tmp"] == tmp
    assert c.PROJECT_1.path_tmp == tmp
    assert c["PROJECT_2"].path_tmp == tmp
    assert c.PROJECT_2.path_project == "/PROJECT_2"
