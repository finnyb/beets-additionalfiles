"""beets-additionalfiles plugin for beets."""

from __future__ import annotations

import glob
import itertools
import os
import shutil
import traceback
from typing import TYPE_CHECKING, Any, ClassVar

import beets.dbcore.db
import beets.library
import beets.plugins
import beets.ui
import beets.util.functemplate
import mediafile

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


class FormattedAdditionalFileMapping(beets.dbcore.db.FormattedMapping):
    """Formatted Mapping that allows path separators for certain keys."""

    def __getitem__(self, key: str) -> str:
        """Get the formatted version of model[key] as a string.

        Args:
            key: The key to retrieve from the model

        Returns:
            The formatted value as a string
        """
        if key == 'albumpath':
            value = self.model._type(key).format(self.model.get(key))
            if isinstance(value, bytes):
                value = value.decode('utf-8', 'ignore')
            return value
        return super().__getitem__(key)


class AdditionalFileModel(beets.dbcore.db.Model):
    """Model for a FormattedAdditionalFileMapping instance."""

    _fields: ClassVar[dict[str, Any]] = {
        'artist': beets.dbcore.types.STRING,
        'albumartist': beets.dbcore.types.STRING,
        'album': beets.dbcore.types.STRING,
        'albumpath': beets.dbcore.types.STRING,
        'filename': beets.dbcore.types.STRING,
    }

    @classmethod
    def _getters(cls) -> dict[str, Any]:
        """Return a mapping from field names to getter functions.

        Returns:
            Empty dict as no custom getters are needed
        """
        return {}


class AdditionalFilesPlugin(beets.plugins.BeetsPlugin):
    """Plugin main class."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize a new plugin instance."""
        super().__init__(*args, **kwargs)
        self.config.add({
            'patterns': {},
            'paths': {},
        })

        self._moved_items: set[tuple[Any, Any, Any]] = set()
        self._copied_items: set[tuple[Any, Any, Any]] = set()
        self._scanned_paths: set[str] = set()
        self.path_formats = beets.ui.get_path_formats(self.config['paths'])

        self.register_listener('item_moved', self.on_item_moved)
        self.register_listener('item_copied', self.on_item_copied)
        self.register_listener('cli_exit', self.on_cli_exit)

    def on_item_moved(self, item: Any, source: Any, destination: Any) -> None:
        """Run this listener function on item_moved events.

        Args:
            item: The beets item that was moved
            source: Source path of the item
            destination: Destination path of the item
        """
        self._moved_items.add((item, source, destination))

    def on_item_copied(self, item: Any, source: Any, destination: Any) -> None:
        """Run this listener function on item_copied events.

        Args:
            item: The beets item that was copied
            source: Source path of the item
            destination: Destination path of the item
        """
        self._copied_items.add((item, source, destination))

    def on_cli_exit(self, lib: Any) -> None:
        """Run this listener function when the CLI exits.

        Args:
            lib: The beets library instance
        """
        files = self.gather_files(self._copied_items)
        self.process_items(files, action=self._copy_file)

        files = self.gather_files(self._moved_items)
        self.process_items(files, action=self._move_file)

    def _copy_file(self, path: Any, dest: Any) -> None:
        """Copy path to dest.

        Args:
            path: Source path to copy from
            dest: Destination path to copy to

        Raises:
            beets.util.FilesystemError: If the copy operation fails
        """
        self._log.info(f'Copying additional file: {path} -> {dest}')
        if os.path.isdir(path):
            if os.path.exists(dest):
                raise beets.util.FilesystemError(
                    'file exists',
                    'copy',
                    (path, dest),
                )

            sourcepath = beets.util.displayable_path(path)
            destpath = beets.util.displayable_path(dest)
            try:
                shutil.copytree(sourcepath, destpath)
            except (OSError, IOError) as exc:
                raise beets.util.FilesystemError(
                    exc,
                    'copy',
                    (path, dest),
                    traceback.format_exc(),
                ) from exc
        else:
            beets.util.copy(path, dest)

    def _move_file(self, path: Any, dest: Any) -> None:
        """Move path to dest.

        Args:
            path: Source path to move from
            dest: Destination path to move to
        """
        self._log.info(f'Moving additional file: {path} -> {dest}')
        sourcepath = beets.util.displayable_path(path)
        destpath = beets.util.displayable_path(dest)
        shutil.move(sourcepath, destpath)

    def process_items(
        self,
        files: Iterable[tuple[Any, Any]],
        action: Any,
    ) -> None:
        """Process files with the given action.

        Args:
            files: Iterable of (source, destination) tuples
            action: Callable to process each file (either _copy_file or _move_file)
        """
        for source, destination in files:
            if not os.path.exists(source):
                self._log.warning(f'Skipping missing source file: {source}')
                continue

            if os.path.exists(destination):
                self._log.warning(
                    f'Skipping already present destination file: {destination}',
                )
                continue

            sourcepath = beets.util.bytestring_path(source)
            destpath = beets.util.bytestring_path(destination)
            destpath = beets.util.unique_path(destpath)
            beets.util.mkdirall(destpath)

            try:
                action(sourcepath, destpath)
            except beets.util.FilesystemError:
                self._log.warning(
                    f'Failed to process file: {source} -> {destpath}',
                )

    def gather_files(
        self,
        itemops: Iterable[tuple[Any, Any, Any]],
    ) -> Generator[tuple[Any, Any], None, None]:
        """Generate a sequence of (path, destpath) tuples.

        Args:
            itemops: Iterable of (item, source, destination) tuples

        Yields:
            Tuples of (source_path, destination_path) for additional files
        """
        def group(itemop: tuple[Any, Any, Any]) -> tuple[str, str]:
            item = itemop[0]
            return (item.albumartist or item.artist, item.album)

        sorted_itemops = sorted(itemops, key=group)
        for _, itemopgroup in itertools.groupby(sorted_itemops, key=group):
            items, sources, destinations = zip(*itemopgroup)
            item = items[0]

            sourcedirs = {os.path.dirname(f) for f in sources}
            destdirs = {os.path.dirname(f) for f in destinations}

            source = os.path.commonpath(sourcedirs)
            destination = os.path.commonpath(destdirs)
            self._log.debug(
                f'{source} -> {destination} ({item.album} by {item.albumartist}, {len(items)} tracks)',
            )

            meta = {
                'artist': item.artist or 'None',
                'albumartist': item.albumartist or 'None',
                'album': item.album or 'None',
                'albumpath': beets.util.displayable_path(destination),
            }

            for path, category in self.match_patterns(
                source,
                skip=self._scanned_paths,
            ):
                path = beets.util.bytestring_path(path)
                relpath = os.path.normpath(os.path.relpath(path, start=source))
                destpath = self.get_destination(relpath, category, meta.copy())
                yield path, destpath

    def match_patterns(
        self,
        source: Any,
        skip: set[str] | None = None,
    ) -> Generator[tuple[str, str], None, None]:
        """Find all files matched by the patterns.

        Args:
            source: Source directory to search for matching files
            skip: Set of paths that have already been scanned (optional)

        Yields:
            Tuples of (path, category) for matched files
        """
        if skip is None:
            skip = set()

        source_path = beets.util.displayable_path(source)

        if source_path in skip:
            return

        for category, patterns in self.config['patterns'].get(dict).items():
            for pattern in patterns:
                globpath = os.path.join(glob.escape(source_path), pattern)
                for path in glob.iglob(globpath):
                    # Skip special dot directories
                    if os.path.basename(path) in ('.', '..'):
                        continue

                    # Skip files handled by the beets media importer
                    ext = os.path.splitext(path)[1]
                    if len(ext) > 1 and ext[1:] in mediafile.TYPES:
                        continue

                    yield (path, category)

        skip.add(source_path)

    def get_destination(
        self,
        path: Any,
        category: str,
        meta: dict[str, str],
    ) -> str:
        """Get the destination path for a source file's relative path.

        Args:
            path: Relative path of the source file
            category: Category name for the file type
            meta: Metadata dictionary with album information

        Returns:
            Destination path for the file
        """
        pathsep = beets.config['path_sep_replace'].get(str)
        strpath = beets.util.displayable_path(path)
        old_basename, fileext = os.path.splitext(os.path.basename(strpath))
        old_filename, _ = os.path.splitext(pathsep.join(strpath.split(os.sep)))

        mapping = FormattedAdditionalFileMapping(
            AdditionalFileModel(
                basename=old_basename,
                filename=old_filename,
                **meta,
            ),
            for_path=True,
        )

        for query, path_format in self.path_formats:
            if query == category:
                break
        else:
            # No query matched; use original filename
            path_format = beets.util.functemplate.Template(
                '$albumpath/$filename',
            )

        funcs = beets.library.models.DefaultTemplateFunctions().functions()
        filepath = path_format.substitute(mapping, funcs) + fileext

        # Sanitize filename
        filename = beets.util.sanitize_path(os.path.basename(filepath))
        dirname = os.path.dirname(filepath)
        filepath = os.path.join(dirname, filename)

        return filepath
