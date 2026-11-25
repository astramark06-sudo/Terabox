import tempfile
import unittest
from pathlib import Path
from terabox import validate_share_url, reserve_name, save_download


class TestDownloader(unittest.TestCase):
    def test_valid(self):
        url = "https://1024terabox.com/s/1Example_123"
        self.assertEqual(validate_share_url(url), url)
        self.assertEqual(validate_share_url("https://www.terabox.com/sharing/link?surl=abc"), "https://www.terabox.com/sharing/link?surl=abc")

    def test_invalid(self):
        for url in ("http://terabox.com/s/abc", "https://terabox.com.evil.test/s/a", "https://terabox.com@evil.test/s/a", "https://terabox.com:8443/s/a", "https://terabox.com/other", "https://user@terabox.com/s/a", "https://evil.terabox.com/s/a"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_share_url(url)

    def test_names(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            for name in ("../../x.txt", "CON.txt", "NUL", "bad\\file.txt", ""):
                target = reserve_name(folder, name)
                self.assertEqual(target.parent, folder)
                self.assertTrue(target.is_file())
            first = reserve_name(folder, "report.pdf")
            first.write_bytes(b"original")
            second = reserve_name(folder, "report.pdf")
            self.assertNotEqual(first, second)
            self.assertEqual(first.read_bytes(), b"original")

    def test_save_and_cleanup(self):
        class Download:
            suggested_filename = "file.txt"
            url = "https://example.test/file"
            def save_as(self, filename):
                Path(filename).write_bytes(b"hello")
        class Failure(Download):
            def save_as(self, filename):
                Path(filename).write_bytes(b"partial")
                raise OSError("failed")
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            saved = save_download(Download(), folder)
            self.assertEqual(saved.read_bytes(), b"hello")
            with self.assertRaises(OSError):
                save_download(Failure(), folder)
            self.assertEqual(list(folder.iterdir()), [saved])


if __name__ == "__main__":
    unittest.main()
