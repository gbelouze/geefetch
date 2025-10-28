# Changelog

All notable changes to this project will be documented in this file.

This changelog should be updated with every pull request with some information about what has been changed. These changes can be added under a temporary title 'pre-release'.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each release can have sections: "Added", "Changed", "Deprecated", "Removed", "Fixed" and "Security".

## [0.6.0](https://github.com/gbelouze/geefetch/compare/v0.6.0...v0.5.3) (2025-10-23)

### Added

- Option to provide several GEE project ids for almost linear speed up [922d335](https://github.com/gbelouze/geefetch/commit/922d33518f1a9d6a2d4cf6f79317125261002900)
- Citation for `geefetch` in README [6a2685a](https://github.com/gbelouze/geefetch/commit/6a2685a3b762d7fcfb1931b2dc3e267baa98838b)

### Fixed

- Change typing of max_tile_size to float [218eb3f](https://github.com/gbelouze/geefetch/commit/218eb3fe2180df47127f1f2b24052bc63a65dab1)
- Don't check custom satellites cleanliness [e3ef4cd](https://github.com/gbelouze/geefetch/commit/e3ef4cd0867a683a68c9e9c0bde5770d0b3ed2b2)

### Changed

- Config must provide `gee_project_ids` instead of `gee_project_id` [922d335](https://github.com/gbelouze/geefetch/commit/922d33518f1a9d6a2d4cf6f79317125261002900)
- GEDI is less agressively filtered [a770420](https://github.com/gbelouze/geefetch/commit/a77042096442efc80b94d42c490318343c7146a5)
- Change Sentinel-2 normalization range [6a2685a](https://github.com/gbelouze/geefetch/commit/6a2685a3b762d7fcfb1931b2dc3e267baa98838b)

## [0.5.3](https://github.com/gbelouze/geefetch/compare/v0.5.3...v0.5.2) (2025-10-10)

### Added

- Generic `resample_reproject_clip` method to ensure that operations done in correct order (according to GEE docs) [c4c37626](https://github.com/gbelouze/geefetch/commit/c4c3762623901dd1fa4f32fe3e5d99e4b2dc4b98)
- Choose to apply refined lee filter to PALSAR-2 images [ac50c1e3](https://github.com/gbelouze/geefetch/commit/ac50c1e324a4f30d423895d87d963f365b4ad093)
- Allow choice of resampling method for downloaded images [7c3da39f](https://github.com/gbelouze/geefetch/commit/7c3da39f5504baa2535bc8936dab33f767ade193)
- Add Sentinel-1 speckle filtering and terrain flattening for s1 images based on [gee_s1_processing](https://github.com/LSCE-forest/gee_s1_processing) [9a2cc37](https://github.com/gbelouze/geefetch/commit/9a2cc3782e4016c6e609ec68b17a1ad986d3db5b)

### Changed

- `before_composite` and `after_composite` logic to ensure that operations are done in power scale for Palsar-2 and Sentinel-1 [e4e418b4](https://github.com/gbelouze/geefetch/commit/e4e418b489f34bfb5fa61055cf4827a32f0f8ae2)
- By default, all satellite data will be resampled using bilinear interpolation (previously it was nearest neighbour) [7c3da39f](https://github.com/gbelouze/geefetch/commit/7c3da39f5504baa2535bc8936dab33f767ade193)

### Fixed

- Download 'all' downloads all satellites listed in config file instead of all geefetch-supported satellites
- Allow user to download just VH or HV Sentinel-1 bands
- Don't create vrt files with partially downloaded tifs
- Improve error logging (avoid silent failures)
- `geedim v2.0.0` causes breaking changes with the `PatchedBaseImage` class. The `pyproject.toml` has been adjusted to request versions `<2.0.0`

## [0.5.2](https://github.com/gbelouze/geefetch/compare/v0.5.2...v0.5.1) (2025-04-15)

### Added

- Option to download satellites from unsupported ImageCollection, with minimal processing [d61bca3](https://github.com/gbelouze/geefetch/commit/d61bca35122914923166551433dd9bb960b0e8cf)

### Changed

- Per-band Sentinel-2 range [3355e57](https://github.com/gbelouze/geefetch/commit/3355e57b2fd627fc93ee735480cad264c47fe350)
- Don't scale bands if the range of value fits within the dtype-representable range [ac2321e](https://github.com/gbelouze/geefetch/commit/ac2321ed7bfad78ea9ddb40fd589b903d8b4af5a)
- Remove the necessity to write `satellite: {}` in the config [803c13e](https://github.com/gbelouze/geefetch/commit/803c13e9d59adde54ffab52abeebe573dd6d9a58)
- Migrated the docs to `mkdocs` [607050c](https://github.com/gbelouze/geefetch/commit/607050ca244cdd3865de967e67d2d20d6fb56d47)

### Fixed

- Issue where the AOI would be split into tiles with duplicates [168fc75](https://github.com/gbelouze/geefetch/commit/168fc75df057c7e1decd273c9209fac7ec5bc5c9)
- Issue where vector tiles that are split because they are too heavy are downloaded in the wrong CRS [cc00bbc](https://github.com/gbelouze/geefetch/commit/cc00bbca03a9837a19b221f84ac5df0634534ed8)

## [0.5.1](https://github.com/gbelouze/geefetch/compare/v0.5.1...v0.5.0) (2025-02-26)

### Added

- Support for [NASADEM](https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001) [0d814d5](https://github.com/gbelouze/geefetch/commit/0d814d5b6c99578441356ef6e92ef6b15f055b96)
- Accept multiple countries to filter the AOI [8e26b05](https://github.com/gbelouze/geefetch/commit/8e26b057059fca2a7e670eb1a873c19932baa0e9)
- `AS_BANDS` option for Sentinel-1 orbit, to mosaic ascending and descending bands as different bands [72b396b](https://github.com/gbelouze/geefetch/commit/72b396b22f84051839b3a584d59b8ff1e95e5fd5)

### Changed

- Removed legacy code `geefetch.coords` [302b24e](https://github.com/gbelouze/geefetch/commit/302b24ee1ed95e60d1ccb977d068b8b2ec6d2278)

## [0.5.0](https://github.com/gbelouze/geefetch/compare/v0.5.0...v0.4.2) (2025-02-13)

### Added

- Set up Github actions for formatting, tracking CHANGELOG and testing `geefetch` installation [15652c1](https://github.com/gbelouze/geefetch/commit/15652c1c6bb4ac4415cd23c76437510824addb9c)
- Tests for band selection [ecab767](https://github.com/gbelouze/geefetch/commit/ecab767270f446c11e72a73d79fe68f2db1791dc)
- Tests for vector band selection [45de5ce](https://github.com/gbelouze/geefetch/commit/45de5ce0b7781950a3750795b25f7c56c7cd0a4e)

### Changed

- Downloads are made atomic by first downloading `abc.tif` to `abc.tmp.tif` [d79873f](https://github.com/gbelouze/geefetch/commit/d79873fe5932d7f291673f6da2c3cd55950bfa4e)
- Already existing downloads are not skipped over if they are corrupted [569c563](https://github.com/gbelouze/geefetch/commit/569c563692d4d6880122ace47f5e81c0af36885a)

### Fixed

- Forward the selected bands specified in the config to the downloader [f4a838c](https://github.com/gbelouze/geefetch/commit/f4a838ced47994ead899e8b5e8bd8104ea5e24c7)

## [0.4.2](https://github.com/gbelouze/geefetch/compare/v0.4.2...v0.4.1) (2024-12-09)

### Fixed

- Use the latest `ee.Authenticate` API [fdf1086](https://github.com/gbelouze/geefetch/commit/fdf1086d48aaa71f41f368385c5ab08fc93b40d9)

### Changed

- Updated `geobbox` version dependency to `0.1.0`
- Don't fail on missing `GEDI` data [3ba99d1](https://github.com/gbelouze/geefetch/commit/3ba99d176136db50437ba0f68697b1872305dfb7)

## [0.4.1](https://github.com/gbelouze/geefetch/compare/v0.4.1...v0.4.0) (2024-11-20)

### Added

- Option to specify orbit direction for Palsar-2 data
- Option to specify orbit direction for Sentinel-1 data [2b025b7](https://github.com/gbelouze/geefetch/commit/2b025b74474be5803895b9cb4d8497f587128923)
- Add a `__main__.py` file to call the CLI with `python -m geefetch` [3c9b0c7](https://github.com/gbelouze/geefetch/commit/3c9b0c74833353dd8e048b59dd244f57ef89034b)
- Add tests in `tests/` using pytest [2c12ebc](https://github.com/gbelouze/geefetch/commit/2c12ebc261617f864e7f8a996fd0725d2d46c731)
- Add tests for timeseries download [5e6928a](https://github.com/gbelouze/geefetch/commit/5e6928a49e61a580985e4180b258874e5e9324d4)
- Add option to configure downloaded bands [3c2e600](https://github.com/gbelouze/geefetch/commit/3c2e600da02aa98be5ebc0b4c4630d2708cd7f70)
- Add rules for linting with `ruff` and `pydoclint` [1b2ac36](https://github.com/gbelouze/geefetch/commit/1b2ac36bac64aa0c1dedb8beaa087559cd52d9fe)
- Add geefetch version number in saved configs [1cac992](https://github.com/gbelouze/geefetch/commit/1cac992559fcd6f27ca7f1cd29f594421bc11b29)

### Changed

- Use PALSAR-2 ScanSAR level 2.2 instead of yearly mosaic [c5a79b1](https://github.com/gbelouze/geefetch/commit/c5a79b10f00e6b7706bf439b5016c2b8fbee39e8)
- Remove the use of `known_hash` for the country borders data [6ce3b6e](https://github.com/gbelouze/geefetch/commit/6ce3b6ee0049e6d5d3cf75f3f6164f82ff886d28)

### Fixed

- Fix `geefetch` attempting to download collection after it was already split-downloaded [b9f5bb1](https://github.com/gbelouze/geefetch/commit/b9f5bb12d4caaf073bd69e50e36e48809966f3ad)
- Fix timeseries download for Palsar-2. [e777289c](https://github.com/gbelouze/geefetch/commit/e777289cc22f1d7551533abc2675e2747d51a8bd)

## [0.4.0](https://github.com/gbelouze/geefetch/compare/v0.4.0...v0.3.2) (2024-11-05)

### Added

- Improve docs and homepage with logo [cf2861b](https://github.com/gbelouze/geefetch/commit/cf2861b6b5b71d0b33db2588045d147377a8dfa0)

### Changed

- Use `geobbox.GeoBoundingBox` instead of `geefetch.coords.BoundingBox` [e3c63ee](https://github.com/gbelouze/geefetch/commit/e3c63eef981bf3e79a7786f8bbf31dd53f5626b7)

## [0.3.2](https://github.com/gbelouze/geefetch/compare/v0.3.2...v0.3.1) (2024-10-31)

### Added

- Add Palsar-2 yearly mosaic support [d867821](https://github.com/gbelouze/geefetch/commit/d867821e0b6379044e59d08538289ff0cd922974)
- Add Landsat-8 support [cb198e0](https://github.com/gbelouze/geefetch/commit/cb198e09e729cf367933c3bedad6653e5693712f)
- Fuzzy search the country name [a613af4](https://github.com/gbelouze/geefetch/commit/a613af46bf87df1951bd3496638a041160f46143)
- Improve GEDI and Sentinel-1 filters [8fd1a5e](https://github.com/gbelouze/geefetch/commit/8fd1a5ebc8d231c3a05e1d8f160936ffadd1b302)

### Fixed

- Make sure index of downloaded collection is unique [4cb5247](https://github.com/gbelouze/geefetch/commit/4cb5247c1d7fc3406b5dc7259fe46b85853b1ed3)
- Split collection when download fails [14b696e](https://github.com/gbelouze/geefetch/commit/14b696e4e0d175d44e4065617a41ad139ec805bf)
- Fix type checking [069f157](https://github.com/gbelouze/geefetch/commit/069f1574a0e1508594555f058645b7072adb5158)

## [0.3.1](https://github.com/gbelouze/geefetch/compare/v0.3.1...v0.3.0) (2024-09-05)

### Changed

- Less strict numpy requirements ([7ffe26f](https://github.com/gbelouze/geefetch/commit/7ffe26f8ca7fd74a97805d9fc49d1a84cdf98f2a))

## [0.3.0](https://github.com/gbelouze/geefetch/compare/v0.3.0...v0.2.2) (2024-09-05)

### Removed

- Remove `geefetch process` CLI ([07261a2](https://github.com/gbelouze/geefetch/commit/07261a2e74134af7d8be1ef6606f03a3c5479436))
- Remove unused `DownloadableGEE` ([5074c06](https://github.com/gbelouze/geefetch/commit/5074c0622a5a5e3c2658dd1c28a6ade312c54ee4))

### Fixed

- Add environment.yml file ([a4d236c](https://github.com/gbelouze/geefetch/commit/a4d236c8b9a72e7f7b44c36303de684b1a45da0a))
- Add version minoration to dependencies ([3c9b8e9](https://github.com/gbelouze/geefetch/commit/3c9b8e9fa703b3cf56d36bf5be2a5d0d0e4bd976))
- Typecheck codebase ([ec9fcdd](https://github.com/gbelouze/geefetch/commit/ec9fcdd3a7bdd347192b7fbfabc32f96cd44b75b))
- Fix geopandas.dataset removed in v1.0.0 ([a0276cc](https://github.com/gbelouze/geefetch/commit/ec9fcdd3a7bdd347192b7fbfabc32f96cd44b75b))

## [0.2.2](https://github.com/gbelouze/geefetch/compare/v0.2.2...v0.2.1) (2024-09-03)

### Fixed

- Fix BoundingBox.unbuffer ([221e30f](https://github.com/gbelouze/geefetch/commit/221e30fd66d09783503ccb7b758ce526c10984db) )

## [0.2.1](https://github.com/gbelouze/geefetch/compare/v0.2.1...0.2.0) (2024-09-03)

### Added

- Use geedim in parallel ([f1767b2](https://github.com/gbelouze/geefetch/commit/f1767b2bc98fbccc6008f4dfe6d73b8029999d79) )
- Add CRS choice option for shapely bbox conversion ([a43fcb8](https://github.com/gbelouze/geefetch/commit/a43fcb81d24dd0010421ae0144a55368b7332764) )
- Add support for .parquet files ([c87f884](https://github.com/gbelouze/geefetch/commit/c87f88469568f6f34a5445ea09408597be138e29) )
- Add bbox unbuffering ([eb9f506](https://github.com/gbelouze/geefetch/commit/eb9f506fbd82bb713d37969bb2dddb4568f0e507) )

### Fixed

- Don't cache .tif meta data ([3f47f83](https://github.com/gbelouze/geefetch/commit/3f47f8368f2ac0393f5fc436259d9b4f8b598b2c) )
- Fix geojson merging ([aef8e6d](https://github.com/gbelouze/geefetch/commit/aef8e6dfc3f0cf855015d7b263fa42f11cf02c83) )
- Fix config.s1 used for other satellites ([2333368](https://github.com/gbelouze/geefetch/commit/2333368d570689684e27f4d7fe9acaa0fb892a4f) )
- Fix NamedTemporaryFile for Windows ([08c69cd](https://github.com/gbelouze/geefetch/commit/08c69cd0fa8238686a1ee81c02d686e370a71e64) )
- Fix infinite loop for collection of 0 images ([2t37491a](https://github.com/gbelouze/geefetch/commit/237491af7b4f742be7db2dc2d445cb83a670c837) )
