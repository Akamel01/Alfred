# Mission Control — design prototype

A **static picture** of the four operator screens plus the live view. It exists so the
design can be reviewed on real devices and argued with. It is not Mission Control.

## What this is not

- **No database.** No connection string, no client, no query.
- **No credentials.** Nothing in the environment, nothing in the bundle.
- **No network calls.** Two Google Fonts stylesheets and nothing else; the CSP in
  `vercel.json` sets `default-src 'none'` and `form-action 'none'`, so the page cannot
  reach anything even if a future edit tried to.
- **No real data.** Every task id, hash, verdict, budget figure and agent statement is
  fabricated, and the banner at the top of the page says so.

ADR-0050 decision 4 is what permits deploying it, and it names the hazard directly: a
working Mission Control URL exists long before the authentication layer does, and a live
URL invites pointing it at a real database. **The startup assertion that refuses a
non-loopback bind stays in place.** [#68](https://github.com/Akamel01/Alfred/issues/68)
is what earns the right to remove it.

## Deploying

Vercel, from GitHub, with automatic deployment on push to `main`.

| Setting | Value |
|---|---|
| Framework preset | Other |
| Root Directory | `src/mission_control/prototype` |
| Build command | *(none — leave empty)* |
| Output directory | *(none — leave empty)* |
| Install command | *(none — leave empty)* |

`vercel.json` in this directory is read once Root Directory points here. It carries the
CSP and the security headers, plus `X-Robots-Tag: noindex` — a prototype that looks like
a real operator console should not be indexed.

There is no build step and no dependency. The deployment is one HTML file.

### Root Directory is the setting that matters, and its failure mode is loud

If Root Directory is left at the repository root, Vercel scans the whole tree, finds
`src/api/app.py`, decides the project is FastAPI, and fails the build:

```
Error: No FastAPI entrypoint found in default locations, but found potential entrypoints:
  src/api/__init__.py (variable: app)
  src/api/app.py (variable: app)
  tests/api/test_routes.py (variable: app)
  tools/serve_vault.py (variable: Handler)
```

That error is diagnostic: it lists files this deployment should never have been able to
see, so it says *Root Directory is unset* rather than anything about the prototype. Set it
to `src/mission_control/prototype` and the deployment sees three files — `index.html`,
`vercel.json`, `README.md` — and no Python at all.

**Deliberately not fixed from the repository.** A `vercel.json` at the repository root
would stop the framework detection, and it would also become the only config Vercel reads
— so the headers here would silently stop applying, and the two files would have to be
kept in sync by hand with nothing checking that they were. Trading a visible dashboard
setting for two configs that can drift apart, where the drift is *security headers going
missing*, is the worse deal. One setting, in one place, that fails loudly when wrong.

### Deployment Protection

Vercel's Deployment Protection is on by default and gates the URL behind an SSO redirect,
so only someone signed into the account can open it. That is the right default while
[#68](https://github.com/Akamel01/Alfred/issues/68) does not exist — it is doing the job
the loopback bind does locally. Turning it off makes the page public, which is safe for
*this* content and is a habit worth not forming on this particular URL.

## What it demonstrates

**Verdict state is form, not colour.** Grayscale is mandated, so `pass` is a solid fill,
`fail` is hatched under a heavy stroke, and `indeterminate` is a dashed hollow. Legible
on a printout and to an operator who cannot distinguish hue.

**Typeface encodes provenance.** Serif for human-authored words, mono for machine-recorded
data. You can tell who wrote a thing by its shape before you read a label.

**Provenance is structural.** Command-surface zones sit raised with a solid left edge;
read-model zones are recessed and unedged; runtime regions are dashed and carry a
`live · unverified` marker. Per ticket #52 D2, provenance is *which program served the
fact*, never a field the read model could write.

**S5 is drawn to look provisional on purpose** (ADR-0051 D5). It renders runtime state,
which owns nothing and is never evidence. The immutable per-attempt rendering lives on S4
and is drawn solid. If the two looked alike, the mutable one would be read with the trust
the immutable one earned.

**S5 has no actions, and the page says that is a gap** rather than a design choice —
watching a run overrun with no way to stop it is what the specification calls anxiety
rather than observability. Tracked as [#69](https://github.com/Akamel01/Alfred/issues/69).
