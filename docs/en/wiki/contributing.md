# Contribute

Contributions should keep CodeMark local, bounded, understandable, and dependency-light. Read the repository [contribution guide](../../../CONTRIBUTING.md) and [security policy](../../../SECURITY.md).

## Development loop

```sh
python3 -m codemark --help
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/build_site.py --check
```

Use Python 3.10 or newer. Optional signing tests require the corresponding local tools; a skip is documented coverage, not a pass. Keep fixtures synthetic and private keys ephemeral.

When changing source handling, preserve existing byte round trips, protected prologues, exclusions, limits, transactional error handling, signature pinning, and report behavior. Add a regression test that exercises the affected contract.

## Documentation

English lives in `docs/en`; Brazilian Portuguese lives in `docs/pt-BR`. Update both when changing a user-visible contract. `README.md` and `README.pt-BR.md` are the two project entry points.

Website content is generated with Python's standard library into `website/public`. The source assets are local HTML/CSS/SVG; do not add JavaScript, trackers, web fonts, or remote asset dependencies. CSS motion must respect reduced-motion preferences.

## Release evidence

Use `website/data/release.json` for the website summary and link dated reports with exact scopes. Keep pending checks visible until executed. Preserve historical evidence and never label an agent review as an external audit.

Do not publish private task prompts, execution instructions, credentials, private histories, real keys, or unrelated user data. Release archives must contain only approved project material.

## License

CodeMark is GPL-3.0-or-later. Contributions must be compatible with that license. Preserve existing notices and describe the origin and license of any imported material.
