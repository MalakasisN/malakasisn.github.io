# Personal Website Project

## Goal
Build a clean, professional personal website hosted on GitHub Pages (free domain: username.github.io). General professional use — not academic-style.

## Stack
- Plain HTML/CSS/JS (no build step, clean, easy to maintain on GitHub Pages)

## Content
- About / bio
- Projects
- CV / resume details

## Deployment
- GitHub Pages (free domain)

## Content editing
- All page content lives in `content.json`; `admin/build.py` generates the `.html` pages and `tcg-posts.js` from it. Never edit the generated files directly — change `content.json` and run `python3 admin/build.py`.
- `admin/app.py` is a local editor UI (edit → preview → publish) launched via `Edit Website.command`.
