# CP53.2 Productized Entry Stabilization

## Background

Claude performed productized entry adaptation on the current branch. This checkpoint is not a rollback but a stabilization and cleanup pass.

## Current Entrypoints

- `/` — simple studio, for ordinary users and demos
- `/advanced` — full workspace, preserving CP43–CP50 capabilities
- `/showcase` — capability showcase, demonstrating rendering styles and export capabilities

## This Round: Preserved

- simple studio at `/`
- showcase at `/showcase`
- advanced/full workspace split at `/advanced`
- style-specific preview temp files
- `web/simple.js` independent of `web/app.js`
- `web/showcase.js` independent of `web/app.js`
- CP53.1 redirect safety (MAX_REDIRECTS=1, URL revalidation after redirect)
- CP53.1 URL validation (private IP block, scheme enforcement)

## This Round: Cleaned

- Removed `outputs/episode_audio/*.wav` from Git tracking
- Ensured `.gitignore` ignores `outputs/episode_audio/`
- Removed CP60 label from `src/server.py` comment
- Fixed TTS capability overclaim in `web/showcase.js` (changed "支持" → "实验能力")
- Added experimental deprecation label to `src/episode_tts.py`

## Current Stable Capabilities

- URL draft basket (`/advanced`)
- Source collections save/restore (`/advanced`)
- Source contract inspector (`/advanced`)
- Apply to planner (`/advanced`)
- Production workflow panel (`/advanced`)
- Publish package copy kit (`/advanced`)
- `publish_package.json` / `publish_package.md` local export (`/advanced`)
- Episode export history (`/advanced`)
- 9:16 preview
- MP4 export
- Source snapshot API (CP53)
- Simple studio entry (`/`)
- Showcase entry (`/showcase`)

## Current Experimental Capabilities

- TTS narration helper (`src/episode_tts.py`) — labeled experimental only, not part of stable surface
- TTS route (`/api/episode/tts-audio`) — present but not marketed as stable

## Still Not Done

- No auto-publishing to real platforms
- No database
- No multi-user SaaS
- TTS not labeled as stable capability
- No `outputs/` artifacts committed to Git
- No Remotion introduced
- No real platform upload APIs
- No continuation of TTS feature expansion

## Relationship to CP54

CP53.2 stabilizes the productized entry split.
CP54 is for Source Candidate Review UI.
