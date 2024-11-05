# Changelog

All notable changes to this project will be documented in this file.

This changelog should be updated with every pull request with some information about what has been changed. These changes can be added under a temporary title 'pre-release'.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each release can have sections: "Added", "Changed", "Deprecated", "Removed", "Fixed" and "Security".

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
- Fix infinite loop for collection of 0 images ([237491a](https://github.com/gbelouze/geefetch/commit/237491af7b4f742be7db2dc2d445cb83a670c837) )
