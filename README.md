# pylibevp

Standalone repository for the Python package and native wrapper used to pack and unpack Talisman `.evp` archives.

## Features

- Python API for list, extract, and pack operations
- Installable CLI command: `pylibevp`
- Django-friendly integration
- Native library path auto-discovery with environment override
- Prebuilt release wheels with the native `.so` bundled
- C++ source backup in `dvsku_libevp/libevp` (origin: https://github.com/dvsku/libevp/)

## Project layout

- `src/pylibevp/api.py`: Python ctypes wrapper
- `src/pylibevp/cli.py`: command line interface
- `src/pylibevp/_loader.py`: native library path resolver
- `dvsku_libevp/libevp`: backup copy of upstream C++ project
- `pyproject.toml`: package metadata and build config

## Build native library

For releases, the wheel already ships with `libevp_wrapper.so` bundled inside the package.

If you are building locally, the package depends on `libevp_wrapper.so` generated from the C++ backup in `dvsku_libevp/libevp`.

```bash
cd dvsku_libevp/libevp
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j

c++ -std=c++20 -fPIC -shared libevp_wrapper.cpp build/source/libevp.a \
    -Iinclude -Ilibraries -I./source \
    -o ../../src/pylibevp/bin/libevp_wrapper.so
```

Expected output on Linux:

- static core library: `dvsku_libevp/libevp/build/source/libevp.a`
- Python wrapper: `src/pylibevp/bin/libevp_wrapper.so`

## Install for local development

From this folder (`pylibevp`):

```bash
pip install -e .
```

This works when `src/pylibevp/bin/libevp_wrapper.so` already exists.

## Install from release

After CI publishes a GitHub Release, download the wheel and install it directly:

```bash
pip install pylibevp-<version>-py3-none-any.whl
```

Or install from the release asset URL if you prefer a one-liner with `pip`.

```bash
pip install https://github.com/<owner>/<repo>/releases/download/v<version>/pylibevp-<version>-py3-none-any.whl
```

## Configure native library path

Option A (recommended): set environment variable

```bash
export PYLIBEVP_LIB_PATH="/absolute/path/to/libevp_wrapper.so"
```

Option B: pass explicit path in code

```python
from pylibevp import LibEVP

ev = LibEVP(lib_path="/absolute/path/to/libevp_wrapper.so")
```

## CLI examples

```bash
pylibevp list data.evp
pylibevp extract data.evp -o output/
pylibevp pack -b output -f "*" -o repacked.evp
pylibevp info data.evp
```

## Django example

```python
# app/services/evp_service.py
from pylibevp import LibEVP


def extract_archive(archive_path: str, destination: str) -> dict:
    evp = LibEVP()  # PYLIBEVP_LIB_PATH must be set in environment
    return evp.unpack(archive_path, destination)
```

In production, set `PYLIBEVP_LIB_PATH` in your environment or process manager.

## Release flow

- Push a tag like `v0.1.0`
- GitHub Actions builds `libevp_wrapper.so`
- GitHub Actions builds the wheel and sdist
- The release assets include the wheel, source tarball, and the compiled `.so`
- End users install the wheel with `pip` and do not compile anything manually

## Repository boundary

This repository is only the library side. The GUI lives in a separate repository and depends on the release published here.
