import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pytest


_ARCHIVE_PREFIX = None
_ARCHIVE_SOURCES = None


def pytest_addoption(parser):
    parser.addoption(
        "--log-archive-prefix",
        action="store",
        dest="log_archive_prefix",
        default=None,
        help="write <prefix>.zip and <prefix>.tar.zst with collected log artifacts",
    )
    parser.addoption(
        "--log-archive-source",
        action="append",
        dest="log_archive_sources",
        default=[],
        help="path to include in archives (repeatable); defaults to discovered log paths",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    global _ARCHIVE_PREFIX, _ARCHIVE_SOURCES
    _ARCHIVE_PREFIX = config.getoption("log_archive_prefix")
    _ARCHIVE_SOURCES = config.getoption("log_archive_sources")


def _collect_default_sources(config):
    candidates = []
    for option in ("log_html", "log_summary", "log_file", "lg_log"):
        value = config.getoption(option, default=None)
        if value:
            candidates.append(Path(value))

    if not candidates:
        return []

    directories = [path if path.is_dir() else path.parent for path in candidates]
    common_root = Path(directories[0])
    for directory in directories[1:]:
        common_root = Path(os.path.commonpath([str(common_root), str(directory)]))

    return [common_root]


def _resolve_sources(config):
    if _ARCHIVE_SOURCES:
        return [Path(source) for source in _ARCHIVE_SOURCES]
    return _collect_default_sources(config)


def _iter_files(path):
    if path.is_file():
        yield path
        return
    for file_path in sorted(path.rglob("*")):
        if file_path.is_file():
            yield file_path


def _create_zip_temp(sources):
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sources:
            source = source.resolve()
            base = source.parent
            for file_path in _iter_files(source):
                archive.write(file_path, file_path.relative_to(base))
    return temp_path


def _create_tar_zst_temp(sources):
    if shutil.which("tar") is None:
        raise RuntimeError("tar binary is required to create .tar.zst archives")

    with tempfile.NamedTemporaryFile(suffix=".tar.zst", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    command = ["tar", "--zstd", "-cf", str(temp_path)]
    for source in sources:
        source = source.resolve()
        command.extend(["-C", str(source.parent), source.name])

    subprocess.run(command, check=True)
    return temp_path


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    del exitstatus
    if not _ARCHIVE_PREFIX:
        return

    sources = _resolve_sources(session.config)
    if not sources:
        raise pytest.UsageError(
            "no archive sources found; use --log-archive-source to specify what to archive"
        )

    missing_sources = [str(path) for path in sources if not path.exists()]
    if missing_sources:
        raise pytest.UsageError(
            f"archive sources do not exist: {', '.join(missing_sources)}"
        )

    prefix = Path(_ARCHIVE_PREFIX)
    zip_path = prefix.with_suffix(".zip")
    tar_path = prefix.with_suffix(".tar.zst")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    tar_path.parent.mkdir(parents=True, exist_ok=True)
    zip_path.unlink(missing_ok=True)
    tar_path.unlink(missing_ok=True)

    try:
        temp_zip = _create_zip_temp(sources)
        temp_tar = _create_tar_zst_temp(sources)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("failed to create .tar.zst archive") from exc

    temp_zip.replace(zip_path)
    temp_tar.replace(tar_path)
