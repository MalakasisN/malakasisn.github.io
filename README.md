# malakasisn.github.io

Personal website for [Nikos Malakasis](https://malakasisn.github.io), hosted on GitHub Pages.

## Editing the site

Double-click **`Edit Website.command`** (or run `python3 admin/app.py`). A local editor opens at
http://127.0.0.1:8787 with three steps:

1. **Edit** text, lists, blog posts and images in the form on the left.
2. **Save & preview** (⌘S) regenerates the pages and refreshes the live preview on the right.
3. **Publish…** commits and pushes to GitHub. The live site updates about a minute later.

**Discard changes…** restores everything to the last published version.

Images you upload are resized for the web automatically (max 1600 px). The profile photo is cropped
square and resized to 400 px. No extra software is needed beyond macOS and Python 3.

## How it works

- `content.json` holds all the site content. It is the single source of truth.
- `admin/build.py` renders the HTML pages and `tcg-posts.js` from it. **Do not edit the generated
  `.html` files or `tcg-posts.js` by hand; edit `content.json` (or use the editor) and rebuild** with
  `python3 admin/build.py`.
- `admin/app.py` is the local editor server (standard library only). `admin/ui.html` is its interface.
- `style.css`, `script.js` and `favicon.svg` are hand-written and not generated.

Pushing to `main` deploys automatically via GitHub Pages.
