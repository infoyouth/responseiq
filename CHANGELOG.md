# CHANGELOG

<!-- version list -->

## v1.3.1 (2026-02-12)

### Bug Fixes

- **ci**: Inject PYPI_TOKEN env var into release workflow
  ([`06d5b86`](https://github.com/infoyouth/responseiq/commit/06d5b86264e7edc5d1d3393a8af52a1a48e0eec9))

- **ci**: Remove path filters to ensure release workflow runs on all main commits
  ([`8732d6f`](https://github.com/infoyouth/responseiq/commit/8732d6f7c1bc374078b429f7f9b7c4912374f056))

- **ci**: Update release committer identity to Youth Innovations
  ([`d1cb58b`](https://github.com/infoyouth/responseiq/commit/d1cb58b382dbbd08457cf19a059aec5ccb219979))


## v1.3.0 (2026-02-12)

### Chores

- Prep for beta launch with pypi config, optimized action, and new readme
  ([`c79e3da`](https://github.com/infoyouth/responseiq/commit/c79e3dade5d3393af7eab217a28bcb6abd3bb2af))

- Remove k8s deploy workflow
  ([`72acf28`](https://github.com/infoyouth/responseiq/commit/72acf28195c34d96e172322e8c8e951d85f7b9b4))

- **deps**: Bump cryptography in the uv group across 1 directory
  ([`b7efbb6`](https://github.com/infoyouth/responseiq/commit/b7efbb6228759ed34525c0e5dfde570b69bea051))

### Features

- **beta**: Prepare for launch with refined CLI, docs, and config
  ([`6d96977`](https://github.com/infoyouth/responseiq/commit/6d96977f0548bf7d95847bd91b6d2416ad2fcb00))


## v1.2.1 (2026-02-10)

### Bug Fixes

- **cli**: Support --action argument and register cli script
  ([`642afe7`](https://github.com/infoyouth/responseiq/commit/642afe75d4f94d60c4cd87f94f9fd0e4ee9d1a45))

### Build System

- Configure hatchling build system and packages
  ([`af76f8f`](https://github.com/infoyouth/responseiq/commit/af76f8f67ddf204b817d6ba88e75d114bdf0401d))


## v1.2.0 (2026-02-10)

### Features

- Implement PR automation logic and security fixes
  ([`6716dd8`](https://github.com/infoyouth/responseiq/commit/6716dd80c766a2d9faece7264fc8eeec79ebf4d4))

- **workflow**: Implement automated PR creation logic locally
  ([`93ee7ac`](https://github.com/infoyouth/responseiq/commit/93ee7ac7eec0e517b59c987c90abc7d5439ba839))


## v1.1.0 (2026-02-10)

### Bug Fixes

- **action**: Ensure uv uses /app environment and python path
  ([`1723eed`](https://github.com/infoyouth/responseiq/commit/1723eedb76f7b5a6526f55bf69b4e349c7bde361))

- **action**: Remove --no-project flag to enable dependency resolution from /app
  ([`a89113b`](https://github.com/infoyouth/responseiq/commit/a89113bec6ce62e8abbd57f268e245d24f5c0152))

- **action**: Set PYTHONPATH to /app to allow module discovery
  ([`7949f09`](https://github.com/infoyouth/responseiq/commit/7949f099de9077bc0f34ab37683e08d37dc57f39))

- **action**: Set uv project path to /app to resolve dependencies correctly
  ([`3dc7cdd`](https://github.com/infoyouth/responseiq/commit/3dc7cdd416db45bf12b78470f8fddcc1669f1e88))

- **ci**: Optimize workflow triggers and fix release output vars
  ([`9db932b`](https://github.com/infoyouth/responseiq/commit/9db932b5224fcf08d01161ac4ef9bca168ec04f3))

- **cli**: Correct key mismatch in issue record generation
  ([`8ca6478`](https://github.com/infoyouth/responseiq/commit/8ca64789d4ffcfe2a49dd3ab826e0ea5393450e6))

- **cli**: Force critical severity for panic keyword to ensure detection
  ([`73fc4f3`](https://github.com/infoyouth/responseiq/commit/73fc4f32152e61e978437f471eec75ca363d3145))

- **cli**: Resolve indentation error and linter warnings in CLI
  ([`be7f788`](https://github.com/infoyouth/responseiq/commit/be7f7885082ca1676059bb68a21287870aa07059))

### Chores

- **deps**: Bump protobuf in the uv group across 1 directory
  ([`bdd0716`](https://github.com/infoyouth/responseiq/commit/bdd0716bfec90b0c3be499077a8e5b88b3ded310))

### Code Style

- Fix linting, formatting and type checking errors
  ([`eb2b7b2`](https://github.com/infoyouth/responseiq/commit/eb2b7b206101ca4fd7781fe86f94a430011fe5b1))

### Features

- **action**: Add CLI entrypoint and GitHub Action definition
  ([`e26c020`](https://github.com/infoyouth/responseiq/commit/e26c020c065f526b07c176e393876bd02331bba3))

- **cli**: Add github step summary output and improve detection logic
  ([`69ce44c`](https://github.com/infoyouth/responseiq/commit/69ce44c07e293872bc7f4052aa4856e486c4ed57))

- **cli**: Ignore non-source extensions (.yml, .json, .md) to reduce false positives
  ([`e628d83`](https://github.com/infoyouth/responseiq/commit/e628d83faf7d44bc12fb001bc03fa1d3588c8c56))

- **remediation**: Implement static kubernetes memory patcher using ruamel.yaml
  ([`0a5d08d`](https://github.com/infoyouth/responseiq/commit/0a5d08d9edbaac6be2bf20b74bdf50e95f317175))


## v1.0.0 (2026-02-10)

- Initial Release
