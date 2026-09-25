from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
import update_music
from build_site import render_music


class MusicTest(unittest.TestCase):
    def fixture(self):
        return json.loads((ROOT / 'tests/fixtures/apple-playlist.json').read_text())

    def html(self, data):
        return '<script id="serialized-server-data" type="application/json">' + json.dumps(data) + '</script>'

    def test_preserves_all_tracks_and_renders_in_reverse_order(self):
        data = self.fixture()
        tracks = data['data'][0]['data']['sections'][0]['items']
        original = copy.deepcopy(tracks[0])
        tracks.append(copy.deepcopy(original))
        for i in range(16):
            track = copy.deepcopy(original)
            track['tertiaryLinks'][0]['title'] = f'Album {i}'
            track['tertiaryLinks'][0]['segue']['destination']['contentDescriptor']['identifiers']['storeAdamID'] = str(i)
            tracks.append(track)
        albums = update_music.parse_playlist(self.html(data))['albums']
        expected = [track['tertiaryLinks'][0]['title'] for track in tracks]
        self.assertEqual([a['title'] for a in albums], expected)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'on-rotation.json').write_text(json.dumps({
                'playlist_url': update_music.PLAYLIST_URL, 'albums': albums,
            }))
            html, md = render_music(root)
            from html.parser import HTMLParser

            class Cards(HTMLParser):
                titles = []

                def handle_starttag(self, tag, attrs):
                    label = dict(attrs).get('aria-label')
                    if tag == 'a' and label:
                        self.titles.append(label.split(' — ')[0])

            cards = Cards()
            cards.feed(html)
            self.assertEqual(cards.titles, list(reversed(expected)))
            md_titles = [line.split('](')[0][3:] for line in md.splitlines() if line.startswith('- [')]
            self.assertEqual(md_titles, list(reversed(expected)))
        self.assertEqual(albums[0]['artist'], 'Canine')
        self.assertTrue(albums[0]['artwork'].endswith('/400x400bb.jpg'))

    def test_preserves_repeated_albums(self):
        data = self.fixture()
        tracks = data['data'][0]['data']['sections'][0]['items']
        tracks.append(copy.deepcopy(tracks[0]))
        albums = update_music.parse_playlist(self.html(data))['albums']
        self.assertEqual(len(albums), len(tracks))

    def test_failed_or_empty_response_preserves_snapshot(self):
        data = self.fixture()
        data['data'][0]['data']['sections'][0]['items'] = []
        for html in ['<html>Sign in</html>', self.html(data)]:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / 'on-rotation.json'
                path.write_text('previous snapshot')
                with patch.object(update_music, 'urlopen') as request:
                    request.return_value.__enter__.return_value.read.return_value = html.encode()
                    with self.assertRaises(ValueError):
                        update_music.refresh(root)
                self.assertEqual(path.read_text(), 'previous snapshot')

    def test_escapes_remote_text_and_rejects_bad_urls(self):
        data = update_music.parse_playlist(self.html(self.fixture()))
        data['albums'][0]['title'] = '<script>alert(1)</script> [link]'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'on-rotation.json'
            path.write_text(json.dumps(data))
            html, md = render_music(root)
            self.assertNotIn('<script>', html)
            self.assertIn('&lt;script&gt;', html)
            self.assertIn(r'\[link\]', md)
            data['albums'][0]['url'] = 'javascript:alert(1)'
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                render_music(root)
