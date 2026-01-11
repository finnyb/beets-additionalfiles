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
