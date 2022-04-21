# Accessing Documentation

Documentation is generated with Sphinx and uploaded to [Confluence](https://confluence.edu-sharing.net/confluence/display/OEDE/Technische+Dokumentation)

Go to `src` and install poetry dependencies.

Start poetry shell.

Go to `docs` and choose which build you want:

## Local

```bash
sphinx-build . build
```

Launch `index.html` in `build` directory

## For confluence

WIP: Currently not possible to automatically push to confluence.

```bash
./build_confluence.sh
```
