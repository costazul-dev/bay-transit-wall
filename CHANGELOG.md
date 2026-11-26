# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-25

### Added
- 511 SF Bay `StopMonitoring` polling for Muni lines 22, 14 and N, with departure
  countdowns drawn on a 128x64 HUB75 RGB LED matrix.
- Per-row `direction` filter for stop codes that serve both directions.
- RGBMatrixEmulator support for local development on macOS.
- `deploy/bay-transit-wall.service` systemd unit for Raspberry Pi deployment.
- MIT `LICENSE` and a License section in `README.md`.

### Changed
- Pinned runtime dependencies in `requirements.txt` and development dependencies in
  `requirements-dev.txt`; verified under Python 3.11 and 3.14.
- Replaced Pillow's deprecated `Image.getdata` with `Image.get_flattened_data` in
  `draw_image`, `recolor_icon` and the showcase tests ahead of its removal in Pillow 14.
