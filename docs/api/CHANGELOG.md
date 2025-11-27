# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fixed TypeError in hybrid quality analysis mode caused by unhashable TestFunctionInfo objects during deduplication
- Deduplication now uses (name, line_number, class_name) tuple for function identity instead of object hashing
- Integrated decorator pattern detection into uncertain case detection flow (was defined but not used)

### Changed
- Test expectations updated to align with actual similarity calculation thresholds
- UncertainCaseDetector now checks for unusual decorator patterns as part of medium-priority detection

## [1.0.0] - Initial Release

First version
