# Hosting the documentation

The documentation is a buildless static site. Its entry point is `docs/index.html`; German case studies are in `docs/beispiele.html`; standalone scene snapshots are in `docs/examples/`. No API keys, server process or Node.js build are required for hosting.

## GitHub Pages

This repository is configured to publish `main` → `/docs` at [the project site](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/).

For this repository, select **Settings → Pages → Build and deployment → Deploy from a branch**, then choose **main** and **/docs**, and save. The `docs/.nojekyll` file keeps the static files unchanged.

After GitHub reports a successful Pages deployment, the expected project-site address is:

`https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/`

Uploading the HTML source alone does not enable Pages. Check the repository's Pages status before sharing this address. A repository administrator may need to enable hosting if the connected GitHub application cannot change Pages settings.

## Local preview

From the repository root:

```bash
python -m http.server 8000
```

Open `http://localhost:8000/docs/`. This server only serves the already generated files; it does not calculate spatial queries or render models on the server. The browser handles those tasks.

## Regeneration

```bash
python -m unittest discover -s tests -v
python tools/build_examples.py
```

Commit the updated `docs/examples/` files after changing package code or case-study data. Each example embeds the local vector data required for that stage but still loads official imagery and 3D tiles online. Preserve all credits when copying scenes to another host.
