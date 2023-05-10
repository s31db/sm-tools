# https://stackoverflow.com/questions/55698762/how-to-copy-html-code-to-clipboard-using-python
"""Edit on Jan 02, 2020
@author: the_RR
Adapted for python 3.4+

Requires pywin32
original: http://code.activestate.com/recipes/474121/
    # HtmlClipboard
    # An interface to the "HTML Format" clipboard data format

    __author__ = "Phillip Piper (jppx1[at]bigfoot.com)"
    __date__ = "2006-02-21"
    __version__ = "0.1"
"""

import re
import time
import win32clipboard

# ---------------------------------------------------------------------------
#  Convenience functions to do the most common operation


def has_html():
    """
    Return True if there is a Html fragment in the clipboard..
    """
    cb = HtmlClipboard()
    return cb.has_html_format()


def get_html():
    """
    Return the Html fragment from the clipboard or None if there is no Html in the clipboard.
    """
    cb = HtmlClipboard()
    if cb.has_html_format():
        return cb.get_fragment()
    else:
        return None


def put_html(fragment, source=None):
    """
    Put the given fragment into the clipboard.
    Convenience function to do the most common operation
    """
    cb = HtmlClipboard()
    cb.put_fragment(fragment, source=source)


# ---------------------------------------------------------------------------

class HtmlClipboard:

    CF_HTML = None

    MARKER_BLOCK_OUTPUT = \
        "Version:1.0\r\n" \
        "StartHTML:%09d\r\n" \
        "EndHTML:%09d\r\n" \
        "StartFragment:%09d\r\n" \
        "EndFragment:%09d\r\n" \
        "StartSelection:%09d\r\n" \
        "EndSelection:%09d\r\n" \
        "SourceURL:%s\r\n"

    MARKER_BLOCK_EX = \
        "Version:(\S+)\s+" \
        "StartHTML:(\d+)\s+" \
        "EndHTML:(\d+)\s+" \
        "StartFragment:(\d+)\s+" \
        "EndFragment:(\d+)\s+" \
        "StartSelection:(\d+)\s+" \
        "EndSelection:(\d+)\s+" \
        "SourceURL:(\S+)"
    MARKER_BLOCK_EX_RE = re.compile(MARKER_BLOCK_EX)

    MARKER_BLOCK = \
        "Version:(\S+)\s+" \
        "StartHTML:(\d+)\s+" \
        "EndHTML:(\d+)\s+" \
        "StartFragment:(\d+)\s+" \
        "EndFragment:(\d+)\s+" \
        "SourceURL:(\S+)"
    MARKER_BLOCK_RE = re.compile(MARKER_BLOCK)

    DEFAULT_HTML_BODY = \
        "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">" \
        "<HTML><HEAD></HEAD><BODY><!--StartFragment-->%s<!--EndFragment--></BODY></HTML>"

    def __init__(self):
        self.html = None
        self.fragment = None
        self.prefix = None
        self.selection = None
        self.source = None
        self.htmlClipboardVersion = None

    def get_cf_html(self):
        """
        Return the FORMATID of the HTML format
        """
        if self.CF_HTML is None:
            self.CF_HTML = win32clipboard.RegisterClipboardFormat("HTML Format")

        return self.CF_HTML

    @staticmethod
    def available_formats():
        """
        Return a possibly empty list of formats available on the clipboard
        """
        formats = []
        try:
            win32clipboard.OpenClipboard(0)
            cf = win32clipboard.EnumClipboardFormats(0)
            while cf != 0:
                formats.append(cf)
                cf = win32clipboard.EnumClipboardFormats(cf)
        finally:
            win32clipboard.CloseClipboard()

        return formats

    def has_html_format(self) -> bool:
        """
        Return a boolean indicating if the clipboard has data in HTML format
        """
        return self.get_cf_html() in self.available_formats()

    def from_clipboard(self):
        """
        Read and decode the HTML from the clipboard
        """

        # implement fix from: http://teachthe.net/?p=1137

        cb_opened = False
        while not cb_opened:
            try:
                win32clipboard.OpenClipboard(0)
                src = win32clipboard.GetClipboardData(self.get_cf_html())
                src = src.decode("UTF-8")
                self.decode_clipboard_source(src)

                cb_opened = True

                win32clipboard.CloseClipboard()
            except Exception as err:
                # If access is denied, that means that the clipboard is in use.
                # Keep trying until it's available.
                if err.winerror == 5:  # Access Denied
                    # wait on clipboard because something else has it. we're waiting a
                    # random amount of time before we try again so we don't collide again
                    time.sleep(0.01)
                elif err.winerror == 1418:  # doesn't have board open
                    pass
                elif err.winerror == 0:  # open failure
                    pass
                else:
                    print('ERROR in Clipboard section of readcomments: %s' % err)

    def decode_clipboard_source(self, src):
        """
        Decode the given string to figure out the details of the HTML that's on the string
        """
        # Try the extended format first (which has an explicit selection)
        matches = self.MARKER_BLOCK_EX_RE.match(src)
        if matches:
            self.prefix = matches.group(0)
            self.htmlClipboardVersion = matches.group(1)
            self.html = src[int(matches.group(2)):int(matches.group(3))]
            self.fragment = src[int(matches.group(4)):int(matches.group(5))]
            self.selection = src[int(matches.group(6)):int(matches.group(7))]
            self.source = matches.group(8)
        else:
            # Failing that, try the version without a selection
            matches = self.MARKER_BLOCK_RE.match(src)
            if matches:
                self.prefix = matches.group(0)
                self.htmlClipboardVersion = matches.group(1)
                self.html = src[int(matches.group(2)):int(matches.group(3))]
                self.fragment = src[int(matches.group(4)):int(matches.group(5))]
                self.source = matches.group(6)
                self.selection = self.fragment

    def get_html(self, refresh=False):
        """
        Return the entire Html document
        """
        if not self.html or refresh:
            self.from_clipboard()
        return self.html

    def get_fragment(self, refresh=False):
        """
        Return the Html fragment. A fragment is well-formated HTML enclosing the selected text
        """
        if not self.fragment or refresh:
            self.from_clipboard()
        return self.fragment

    def get_selection(self, refresh=False):
        """
        Return the part of the HTML that was selected. It might not be well-formed.
        """
        if not self.selection or refresh:
            self.from_clipboard()
        return self.selection

    def get_source(self, refresh=False):
        """
        Return the URL of the source of this HTML
        """
        if not self.selection or refresh:
            self.from_clipboard()
        return self.source

    def put_fragment(self, fragment, selection=None, html=None, source=None):
        """
        Put the given well-formed fragment of Html into the clipboard.
        selection, if given, must be a literal string within fragment.
        html, if given, must be a well-formed Html document that textually
        contains fragment and its required markers.
        """
        if selection is None:
            selection = fragment
        if html is None:
            html = self.DEFAULT_HTML_BODY % fragment
        if source is None:
            source = "file://HtmlClipboard.py"

        fragment_start = html.index(fragment)
        fragment_end = fragment_start + len(fragment)
        selection_start = html.index(selection)
        selection_end = selection_start + len(selection)
        self.put_to_clipboard(html, fragment_start, fragment_end, selection_start, selection_end, source)

    def put_to_clipboard(self, html, fragment_start, fragment_end, selection_start, selection_end, source="None"):
        """
        Replace the Clipboard contents with the given html information.
        """
        try:
            win32clipboard.OpenClipboard(0)
            win32clipboard.EmptyClipboard()
            src = self.encode_clipboard_source(html, fragment_start, fragment_end, selection_start, selection_end,
                                               source)
            src = src.encode("UTF-8")
            # print(src)
            win32clipboard.SetClipboardData(self.get_cf_html(), src)
        finally:
            win32clipboard.CloseClipboard()

    def encode_clipboard_source(self, html, fragment_start, fragment_end, selection_start, selection_end, source):
        """
        Join all our bits of information into a string formatted as per the HTML format specs.
        """
        # How long is the prefix going to be?
        dummyPrefix = self.MARKER_BLOCK_OUTPUT % (0, 0, 0, 0, 0, 0, source)
        lenPrefix = len(dummyPrefix)

        prefix = self.MARKER_BLOCK_OUTPUT % (lenPrefix, len(html) + lenPrefix,
                                             fragment_start + lenPrefix, fragment_end + lenPrefix,
                                             selection_start + lenPrefix, selection_end + lenPrefix,
                                             source)
        return prefix + html


def dump_html():

    cb = HtmlClipboard()
    print("available_formats()=%s" % str(cb.available_formats()))
    print("has_html_format()=%s" % str(cb.has_html_format()))
    if cb.has_html_format():
        cb.from_clipboard()
        print("prefix=>>>%s<<<END" % cb.prefix)
        print("htmlClipboardVersion=>>>%s<<<END" % cb.htmlClipboardVersion)
        print("get_selection()=>>>%s<<<END" % cb.get_selection())
        print("get_fragment()=>>>%s<<<END" % cb.get_fragment())
        print("GetHtml()=>>>%s<<<END" % cb.get_html())
        print("get_source()=>>>%s<<<END" % cb.get_source())


def test_simple_get_put_html():
    data = "<p>Writing to the clipboard is <strong>easy</strong> with this code.</p>"
    put_html(data)
    assert get_html() == data
    # dump_html()
    