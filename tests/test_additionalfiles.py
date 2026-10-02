"""Tests for the beets-additionalfiles plugin."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import unittest
import unittest.mock

import beets
import beets.library
import beets.util
import confuse

import beetsplug.additionalfiles

RSRC = os.path.join(os.path.dirname(__file__), 'rsrc')

log = logging.getLogger('beets')
log.propagate = True
log.setLevel(logging.DEBUG)


class BaseTestCase(unittest.TestCase):
    """Base testcase class that sets up example files."""

    PLUGIN_CONFIG = {
        'additionalfiles': {
            'patterns': {
                'log': ['*.log'],
                'cue': ['*.cue', '*/*.cue'],
                'artwork': ['scans/', 'Scans/', 'artwork/', 'Artwork/'],
            },
            'paths': {
                'artwork': '$albumpath/artwork',
                'log': '$albumpath/audio',
            },
        },
    }

    def _create_example_file(self, *path: str) -> None:
        """Create an empty file at the given path."""
        with open(os.path.join(*path), mode='w', encoding='utf-8'):
            pass

    def _create_artwork_files(self, *path: str) -> None:
        """Create artwork directory with sample files."""
        artwork_path = os.path.join(*path)
        os.mkdir(artwork_path)
        for filename in ('front.jpg', 'back.jpg'):
            self._create_example_file(artwork_path, filename)

    def setUp(self) -> None:
        """Set up example files and instantiate the plugin."""
        self.srcdir = tempfile.TemporaryDirectory(suffix='src')
        self.dstdir = tempfile.TemporaryDirectory(suffix='dst')

        os.makedirs(os.path.join(self.dstdir.name, 'single'))
        sourcedir = os.path.join(self.srcdir.name, 'single')
        os.makedirs(sourcedir)
        shutil.copy(
            os.path.join(RSRC, 'full.mp3'),
            os.path.join(sourcedir, 'file.mp3'),
        )
        for filename in ('file.cue', 'file.txt', 'file.log'):
            self._create_example_file(sourcedir, filename)
        self._create_artwork_files(sourcedir, 'scans')

        os.makedirs(os.path.join(self.dstdir.name, 'multiple'))
        sourcedir = os.path.join(self.srcdir.name, 'multiple')
        os.makedirs(os.path.join(sourcedir, 'CD1'))
        shutil.copy(
            os.path.join(RSRC, 'full.mp3'),
            os.path.join(sourcedir, 'CD1', 'file.mp3'),
        )
        os.makedirs(os.path.join(sourcedir, 'CD2'))
        shutil.copy(
            os.path.join(RSRC, 'full.mp3'),
            os.path.join(sourcedir, 'CD2', 'file.mp3'),
        )
        for filename in ('file.txt', 'file.log'):
            self._create_example_file(sourcedir, filename)
        for discdir in ('CD1', 'CD2'):
            self._create_example_file(sourcedir, discdir, 'file.cue')
        self._create_artwork_files(sourcedir, 'scans')

        config = confuse.RootView(sources=[
            confuse.ConfigSource.of(self.PLUGIN_CONFIG),
        ])

        with unittest.mock.patch(
            'beetsplug.additionalfiles.beets.plugins.beets.config',
            config,
        ):
            self.plugin = beetsplug.additionalfiles.AdditionalFilesPlugin('additionalfiles')

    def tearDown(self) -> None:
        """Remove the example files."""
        self.srcdir.cleanup()
        self.dstdir.cleanup()


class MatchPatternsTestCase(BaseTestCase):
    """Testcase that checks if all extra files are matched."""

    def test_match_pattern(self):
        """Test if extra files are matched in the media file's directory."""
        sourcedir = os.path.join(self.srcdir.name, 'single')
        files = {
            (beets.util.displayable_path(path), category)
            for path, category in self.plugin.match_patterns(source=sourcedir)
        }

        expected_cue = (os.path.join(sourcedir, 'file.cue'), 'cue')
        expected_log = (os.path.join(sourcedir, 'file.log'), 'log')

        self.assertIn(expected_cue, files)
        self.assertIn(expected_log, files)

        artwork_files = {f for f in files if f[1] == 'artwork'}
        self.assertGreaterEqual(len(artwork_files), 1)
        artwork_paths = [f[0] for f in artwork_files]
        self.assertTrue(
            any(path.lower() == os.path.join(sourcedir, 'scans/').lower()
                for path in artwork_paths),
            f"Expected scans/ directory, got {artwork_paths}"
        )


class MoveFilesTestCase(BaseTestCase):
    """Testcase that moves files."""

    def test_move_files_single(self):
        """Test if extra files are moved for single directory imports."""
        sourcedir = os.path.join(self.srcdir.name, 'single')
        destdir = os.path.join(self.dstdir.name, 'single')

        source = os.path.join(sourcedir, 'file.mp3')
        destination = os.path.join(destdir, 'moved_file.mp3')
        item = beets.library.Item.from_path(source)
        shutil.move(source, destination)
        self.plugin.on_item_moved(
            item, beets.util.bytestring_path(source),
            beets.util.bytestring_path(destination),
        )

        self.plugin.on_cli_exit(None)

        self.assertTrue(os.path.exists(os.path.join(sourcedir, 'file.txt')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'file.cue')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'file.log')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'audio.log')))

        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'artwork')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'scans')))

        self.assertFalse(os.path.exists(os.path.join(destdir, 'file.txt')))
        self.assertTrue(os.path.exists(os.path.join(destdir, 'file.cue')))
        self.assertFalse(os.path.exists(os.path.join(destdir, 'file.log')))
        self.assertTrue(os.path.exists(os.path.join(destdir, 'audio.log')))

        self.assertFalse(os.path.isdir(os.path.join(destdir, 'scans')))
        self.assertTrue(os.path.isdir(os.path.join(destdir, 'artwork')))
        self.assertEqual(set(os.listdir(os.path.join(destdir, 'artwork'))),
                         {'front.jpg', 'back.jpg'})

    def test_move_files_multiple(self):
        """Test if extra files are moved for multi-directory imports."""
        sourcedir = os.path.join(self.srcdir.name, 'multiple')
        destdir = os.path.join(self.dstdir.name, 'multiple')

        source = os.path.join(sourcedir, 'CD1', 'file.mp3')
        destination = os.path.join(destdir, '01 - moved_file.mp3')
        item = beets.library.Item.from_path(source)
        shutil.move(source, destination)
        self.plugin.on_item_moved(
            item, beets.util.bytestring_path(source),
            beets.util.bytestring_path(destination),
        )

        source = os.path.join(sourcedir, 'CD2', 'file.mp3')
        destination = os.path.join(destdir, '02 - moved_file.mp3')
        item = beets.library.Item.from_path(source)
        shutil.move(source, destination)
        self.plugin.on_item_moved(
            item, beets.util.bytestring_path(source),
            beets.util.bytestring_path(destination),
        )

        self.plugin.on_cli_exit(None)

        self.assertTrue(os.path.exists(os.path.join(sourcedir, 'file.txt')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'CD1', 'file.cue')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'CD2', 'file.cue')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'file.log')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'audio.log')))

        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'artwork')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'scans')))

        self.assertFalse(os.path.exists(os.path.join(destdir, 'file.txt')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'CD1_file.cue')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'CD2_file.cue')))
        self.assertFalse(os.path.exists(os.path.join(destdir, 'file.log')))
        self.assertTrue(os.path.exists(os.path.join(destdir, 'audio.log')))

        self.assertFalse(os.path.isdir(os.path.join(destdir, 'scans')))
        self.assertTrue(os.path.isdir(os.path.join(destdir, 'artwork')))
        self.assertEqual(set(os.listdir(os.path.join(destdir, 'artwork'))),
                         {'front.jpg', 'back.jpg'})


class CopyFilesTestCase(BaseTestCase):
    """Testcase that copies files."""

    def test_copy_files_single(self):
        """Test if extra files are copied for single directory imports."""
        sourcedir = os.path.join(self.srcdir.name, 'single')
        destdir = os.path.join(self.dstdir.name, 'single')

        source = os.path.join(sourcedir, 'file.mp3')
        destination = os.path.join(destdir, 'copied_file.mp3')
        item = beets.library.Item.from_path(source)
        shutil.copy(source, destination)
        self.plugin.on_item_copied(
            item, beets.util.bytestring_path(source),
            beets.util.bytestring_path(destination),
        )

        self.plugin.on_cli_exit(None)

        self.assertTrue(os.path.exists(os.path.join(sourcedir, 'file.txt')))
        self.assertTrue(os.path.exists(os.path.join(sourcedir, 'file.cue')))
        self.assertTrue(os.path.exists(os.path.join(sourcedir, 'file.log')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'audio.log')))

        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'artwork')))
        self.assertTrue(os.path.isdir(os.path.join(sourcedir, 'scans')))
        self.assertEqual(set(os.listdir(os.path.join(sourcedir, 'scans'))),
                         {'front.jpg', 'back.jpg'})

        self.assertFalse(os.path.exists(os.path.join(destdir, 'file.txt')))
        self.assertTrue(os.path.exists(os.path.join(destdir, 'file.cue')))
        self.assertFalse(os.path.exists(os.path.join(destdir, 'file.log')))
        self.assertTrue(os.path.exists(os.path.join(destdir, 'audio.log')))

        self.assertFalse(os.path.exists(os.path.join(destdir, 'scans')))
        self.assertTrue(os.path.isdir(os.path.join(destdir, 'artwork')))
        self.assertEqual(set(os.listdir(os.path.join(destdir, 'artwork'))),
                         {'front.jpg', 'back.jpg'})

    def test_copy_files_multiple(self):
        """Test if extra files are copied for multi-directory imports."""
        sourcedir = os.path.join(self.srcdir.name, 'multiple')
        destdir = os.path.join(self.dstdir.name, 'multiple')

        source = os.path.join(sourcedir, 'CD1', 'file.mp3')
        destination = os.path.join(destdir, '01 - copied_file.mp3')
        item = beets.library.Item.from_path(source)
        shutil.copy(source, destination)
        self.plugin.on_item_copied(
            item, beets.util.bytestring_path(source),
            beets.util.bytestring_path(destination),
        )

        source = os.path.join(sourcedir, 'CD2', 'file.mp3')
        destination = os.path.join(destdir, '02 - copied_file.mp3')
        item = beets.library.Item.from_path(source)
        shutil.copy(source, destination)
        self.plugin.on_item_copied(
            item, beets.util.bytestring_path(source),
            beets.util.bytestring_path(destination),
        )

        self.plugin.on_cli_exit(None)

        self.assertTrue(os.path.exists(os.path.join(sourcedir, 'file.txt')))
        self.assertTrue(os.path.exists(os.path.join(sourcedir, 'CD1', 'file.cue')))
        self.assertTrue(os.path.exists(os.path.join(sourcedir, 'CD2', 'file.cue')))
        self.assertTrue(os.path.exists(os.path.join(sourcedir, 'file.log')))
        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'audio.log')))

        self.assertFalse(os.path.exists(os.path.join(sourcedir, 'artwork')))
        self.assertTrue(os.path.isdir(os.path.join(sourcedir, 'scans')))
        self.assertEqual(set(os.listdir(os.path.join(sourcedir, 'scans'))),
                         {'front.jpg', 'back.jpg'})

        self.assertFalse(os.path.exists(os.path.join(destdir, 'file.txt')))
        self.assertTrue(os.path.exists(os.path.join(destdir, 'CD1_file.cue')))
        self.assertTrue(os.path.exists(os.path.join(destdir, 'CD2_file.cue')))
        self.assertFalse(os.path.exists(os.path.join(destdir, 'file.log')))
        self.assertTrue(os.path.exists(os.path.join(destdir, 'audio.log')))

        self.assertFalse(os.path.exists(os.path.join(destdir, 'scans')))
        self.assertTrue(os.path.isdir(os.path.join(destdir, 'artwork')))
        self.assertEqual(set(os.listdir(os.path.join(destdir, 'artwork'))),
                         {'front.jpg', 'back.jpg'})


class MultiAlbumTestCase(unittest.TestCase):
    """Testcase class that checks if multiple albums are grouped correctly."""

    PLUGIN_CONFIG = {
        'additionalfiles': {
            'patterns': {
                'log': ['*.log'],
            },
        },
    }

    def setUp(self) -> None:
        """Set up example files and instantiate the plugin."""
        self.srcdir = tempfile.TemporaryDirectory(suffix='src')
        self.dstdir = tempfile.TemporaryDirectory(suffix='dst')

        for album in ('album1', 'album2'):
            os.makedirs(os.path.join(self.dstdir.name, album))
            sourcedir = os.path.join(self.srcdir.name, album)
            os.makedirs(sourcedir)
            shutil.copy(
                os.path.join(RSRC, 'full.mp3'),
                os.path.join(sourcedir, 'track01.mp3'),
            )
            shutil.copy(
                os.path.join(RSRC, 'full.mp3'),
                os.path.join(sourcedir, 'track02.mp3'),
            )
            logfile = os.path.join(sourcedir, f'{album}.log')
            with open(logfile, mode='w', encoding='utf-8'):
                pass

        config = confuse.RootView(sources=[
            confuse.ConfigSource.of(self.PLUGIN_CONFIG),
        ])

        with unittest.mock.patch(
            'beetsplug.additionalfiles.beets.plugins.beets.config',
            config,
        ):
            self.plugin = beetsplug.additionalfiles.AdditionalFilesPlugin('additionalfiles')

    def tearDown(self) -> None:
        """Remove the example files."""
        self.srcdir.cleanup()
        self.dstdir.cleanup()

    def test_album_grouping(self):
        """Test if albums are grouped correctly."""
        for album in ('album1', 'album2'):
            sourcedir = os.path.join(self.srcdir.name, album)
            destdir = os.path.join(self.dstdir.name, album)

            for i in range(1, 3):
                source = os.path.join(sourcedir, f'track{i:02d}.mp3')
                destination = os.path.join(
                    destdir, f'{i:02d} - {album} - untitled.mp3',
                )
                item = beets.library.Item.from_path(source)
                item.album = album
                item.track = i
                item.tracktotal = 2
                shutil.copy(source, destination)
                self.plugin.on_item_copied(
                    item, beets.util.bytestring_path(source),
                    beets.util.bytestring_path(destination),
                )

        self.plugin.on_cli_exit(None)

        for album in ('album1', 'album2'):
            destdir = os.path.join(self.dstdir.name, album)
            for i in range(1, 3):
                destination = os.path.join(
                    destdir, f'{i:02d} - {album} - untitled.mp3',
                )
                self.assertTrue(os.path.exists(destination))
            self.assertTrue(os.path.exists(os.path.join(
                self.dstdir.name, album, f'{album}.log',
            )))


class ArtworkFilesTestCase(BaseTestCase):
    """Testcase that checks if artwork files are matched and moved."""

    PLUGIN_CONFIG = {
        'additionalfiles': {
            'patterns': {
                'artwork': ['cover*.jpg'],
            },
        },
    }

    def test_match_artwork_files(self):
        """Test if artwork files (including those with parentheses) are matched."""
        sourcedir = os.path.join(self.srcdir.name, 'single')
        filenames = ['cover.jpg', 'cover (1).jpg', 'cover (2).jpg']
        for filename in filenames:
            self._create_example_file(sourcedir, filename)

        files = {
            (os.path.basename(beets.util.displayable_path(path)), category)
            for path, category in self.plugin.match_patterns(source=sourcedir)
        }

        for filename in filenames:
            self.assertIn((filename, 'artwork'), files)

    def test_move_artwork_files(self):
        """Test if artwork files are moved correctly."""
        sourcedir = os.path.join(self.srcdir.name, 'single')
        destdir = os.path.join(self.dstdir.name, 'single')
        filenames = ['cover.jpg', 'cover (1).jpg', 'cover (2).jpg']
        for filename in filenames:
            self._create_example_file(sourcedir, filename)

        source = os.path.join(sourcedir, 'file.mp3')
        destination = os.path.join(destdir, 'moved_file.mp3')
        item = beets.library.Item.from_path(source)
        shutil.move(source, destination)
        self.plugin.on_item_moved(
            item, beets.util.bytestring_path(source),
            beets.util.bytestring_path(destination),
        )

        self.plugin.on_cli_exit(None)

        for filename in filenames:
            self.assertFalse(os.path.exists(os.path.join(sourcedir, filename)))
            # Files are moved to $albumpath/$filename by default in this test case
            self.assertTrue(os.path.exists(os.path.join(destdir, filename)))

    def test_copy_artwork_files(self):
        """Test if artwork files are copied correctly."""
        sourcedir = os.path.join(self.srcdir.name, 'single')
        destdir = os.path.join(self.dstdir.name, 'single')
        filenames = ['cover.jpg', 'cover (1).jpg', 'cover (2).jpg']
        for filename in filenames:
            self._create_example_file(sourcedir, filename)

        source = os.path.join(sourcedir, 'file.mp3')
        destination = os.path.join(destdir, 'copied_file.mp3')
        item = beets.library.Item.from_path(source)
        shutil.copy(source, destination)
        self.plugin.on_item_copied(
            item, beets.util.bytestring_path(source),
            beets.util.bytestring_path(destination),
        )

        self.plugin.on_cli_exit(None)

        for filename in filenames:
            self.assertTrue(os.path.exists(os.path.join(sourcedir, filename)))
            self.assertTrue(os.path.exists(os.path.join(destdir, filename)))


class SkipAndErrorTestCase(BaseTestCase):
    """Testcase for files that are skipped or fail to process."""

    PLUGIN_CONFIG = {
        'additionalfiles': {
            'patterns': {
                'all': ['*.*'],
            },
        },
    }

    def test_media_files_not_matched(self):
        """Test if media files handled by the beets importer are not matched."""
        sourcedir = os.path.join(self.srcdir.name, 'single')
        files = {
            os.path.basename(beets.util.displayable_path(path))
            for path, _ in self.plugin.match_patterns(source=sourcedir)
        }

        self.assertNotIn('file.mp3', files)
        self.assertEqual(files, {'file.cue', 'file.txt', 'file.log'})

    def test_missing_source_skipped(self):
        """Test if a source file that no longer exists is skipped with a warning."""
        source = os.path.join(self.srcdir.name, 'single', 'missing.txt')
        destination = os.path.join(self.dstdir.name, 'single', 'missing.txt')
        action = unittest.mock.Mock()

        with self.assertLogs('beets.additionalfiles', level='WARNING') as logs:
            self.plugin.process_items([(source, destination)], action=action)

        action.assert_not_called()
        self.assertFalse(os.path.exists(destination))
        self.assertIn('Skipping missing source file', logs.output[0])

    def test_failure_does_not_stop_processing(self):
        """Test if a failing file is logged and the remaining files are still processed."""
        sourcedir = os.path.join(self.srcdir.name, 'single')
        destdir = os.path.join(self.dstdir.name, 'single')
        files = [
            (os.path.join(sourcedir, name), os.path.join(destdir, name))
            for name in ('file.cue', 'file.log')
        ]
        action = unittest.mock.Mock(side_effect=[
            beets.util.FilesystemError(OSError('boom'), 'copy', files[0]),
            None,
        ])

        with self.assertLogs('beets.additionalfiles', level='WARNING') as logs:
            self.plugin.process_items(files, action=action)

        self.assertEqual(action.call_count, 2)
        self.assertEqual(len(logs.output), 1)
        self.assertIn('Failed to process file', logs.output[0])
        self.assertIn('file.cue', logs.output[0])
