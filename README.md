# 208 Pressbox

Local high school sports for Eastern Idaho: schedules, scores, standings, rosters and stat leaders for 13 football teams (Varsity, JV and Freshman), with places for booster-club donations and local business sponsors.

## What's in this folder

| File | What it is |
|---|---|
| `index.html` | The whole app. This is the page people open. |
| `manifest.json`, `icon-*.png`, `apple-touch-icon.png` | The name and icon used when someone adds the app to their phone's home screen. |
| `.nojekyll` | Tells GitHub to publish the files as they are. |
| `source/` | The pieces the app is built from. Nothing in here is needed to run the site. |

## How it is published

GitHub Pages serves this folder. Any change pushed to the `main` branch goes live within a minute or two.

## Changing things

- **Admin screen:** add `#admin` to the end of the site address to show the gear button. For now, admin changes save only on the device that made them.
- **Rebuilding the app:** in `source/`, run `python3 data.py` (rebuilds the data and checks every record) and then `python3 build.py`, then copy `dist/index.html` to this folder.

## Where the data comes from

Schedules, scores, rosters and stat leaders were read from each team's MaxPreps page on October 6, 2026. The Hillcrest freshman schedule and roster come from the team's own sheet. Nothing is made up: anything not posted shows as "not posted."
