"""ctypes API wrapper around the native libevp bridge."""

from __future__ import annotations

import ctypes
from ctypes import POINTER, Structure, c_char_p, c_int, c_uint32
from pathlib import Path
from typing import Optional

from ._loader import resolve_library_path


class EVP_FD(Structure):
    """Archive file descriptor structure from the native library."""


EVP_FD._fields_ = [
    ("file", c_char_p),
    ("data_offset", c_uint32),
    ("data_size", c_uint32),
    ("data_compressed_size", c_uint32),
    ("flags", c_uint32),
    ("hash", ctypes.c_uint8 * 16),
]


class EVP_Result(Structure):
    """Operation result returned by the native wrapper."""

    _fields_ = [
        ("status", c_int),
        ("message", ctypes.c_char * 1024),
    ]

    def is_ok(self) -> bool:
        return self.status == 3

    def is_failure(self) -> bool:
        return self.status == 2

    def get_message(self) -> str:
        return self.message.decode("utf-8", errors="ignore").rstrip("\x00")


class LibEVP:
    """High-level Python API for packing and unpacking .evp archives."""

    STATUS_OK = 3
    STATUS_CANCELLED = 1
    STATUS_FAILURE = 2
    STATUS_UNDEFINED = 0

    def __init__(self, lib_path: Optional[str] = None):
        resolved = resolve_library_path(lib_path)
        self._lib_path = resolved
        self.lib = ctypes.CDLL(str(resolved))
        self._setup_functions()
        self.init()

    @property
    def library_path(self) -> Path:
        return self._lib_path

    def _setup_functions(self) -> None:
        self.lib.evp_init.argtypes = []
        self.lib.evp_init.restype = None

        self.lib.evp_cleanup.argtypes = []
        self.lib.evp_cleanup.restype = None

        self.lib.evp_get_archive_fds.argtypes = [
            c_char_p,
            POINTER(POINTER(EVP_FD)),
            POINTER(c_int),
        ]
        self.lib.evp_get_archive_fds.restype = EVP_Result

        self.lib.evp_unpack.argtypes = [c_char_p, c_char_p]
        self.lib.evp_unpack.restype = EVP_Result

        self.lib.evp_pack.argtypes = [c_char_p, POINTER(c_char_p), c_int, c_char_p]
        self.lib.evp_pack.restype = EVP_Result

        self.lib.evp_free_fds.argtypes = [POINTER(EVP_FD), c_int]
        self.lib.evp_free_fds.restype = None

        self.lib.evp_get_file_info.argtypes = [
            c_int,
            c_char_p,
            c_int,
            POINTER(c_uint32),
            POINTER(c_uint32),
        ]
        self.lib.evp_get_file_info.restype = c_int

        self.lib.evp_get_file_count.argtypes = []
        self.lib.evp_get_file_count.restype = c_int

    def init(self) -> None:
        self.lib.evp_init()

    def cleanup(self) -> None:
        self.lib.evp_cleanup()

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass

    def get_archive_files(self, archive_path: str) -> list[dict]:
        archive_bytes = archive_path.encode("utf-8")
        fds_ptr = POINTER(EVP_FD)()
        count = c_int()

        result = self.lib.evp_get_archive_fds(
            archive_bytes,
            ctypes.byref(fds_ptr),
            ctypes.byref(count),
        )

        if result.is_failure():
            raise RuntimeError(f"Failed to read archive: {result.get_message()}")

        files = []
        if count.value > 0 and fds_ptr:
            for i in range(count.value):
                fd = fds_ptr[i]
                files.append(
                    {
                        "file": fd.file.decode("utf-8", errors="ignore"),
                        "data_offset": fd.data_offset,
                        "data_size": fd.data_size,
                        "data_compressed_size": fd.data_compressed_size,
                        "flags": fd.flags,
                        "hash": bytes(fd.hash),
                    }
                )
            self.lib.evp_free_fds(fds_ptr, count.value)

        return files

    def unpack(self, archive_path: str, output_dir: str, create_dir: bool = True) -> dict:
        if create_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)

        result = self.lib.evp_unpack(
            archive_path.encode("utf-8"),
            output_dir.encode("utf-8"),
        )

        if result.is_failure():
            raise RuntimeError(f"Failed to unpack archive: {result.get_message()}")

        return {"success": result.is_ok(), "message": result.get_message()}

    def pack(self, base_path: str, files: list[str], output_archive: str) -> dict:
        files_array = (c_char_p * len(files))()
        for i, rel_path in enumerate(files):
            files_array[i] = rel_path.encode("utf-8")

        result = self.lib.evp_pack(
            base_path.encode("utf-8"),
            files_array,
            len(files),
            output_archive.encode("utf-8"),
        )

        if result.is_failure():
            raise RuntimeError(f"Failed to pack archive: {result.get_message()}")

        return {"success": result.is_ok(), "message": result.get_message()}

    def get_file_count(self) -> int:
        return self.lib.evp_get_file_count()

    def get_file_info(self, index: int) -> Optional[dict]:
        filename_buffer = ctypes.create_string_buffer(512)
        data_size = c_uint32()
        compressed_size = c_uint32()

        result = self.lib.evp_get_file_info(
            index,
            filename_buffer,
            512,
            ctypes.byref(data_size),
            ctypes.byref(compressed_size),
        )

        if result != 0:
            return None

        return {
            "filename": filename_buffer.value.decode("utf-8", errors="ignore"),
            "data_size": data_size.value,
            "compressed_size": compressed_size.value,
        }
