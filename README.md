# 208 Pressbox

Local high school sports for Eastern Idaho: schedules, scores, standings and rosters for 13 schools (football, soccer and basketball), plus score reports from fans, pick'em, player of the week voting, photos and playoff brackets, with places for booster-club donations and local business sponsors.

## What's in this folder

| File | What it is |
|---|---|
| `index.html` | The whole app. This is the page people open. |
| `manifest.json`, `icon-*.png`, `apple-touch-icon.png` | The name and icon used when someone adds the app to their phone's home screen. |
| `.nojekyll` | Tells GitHub to publish the files as they are. |
| `source/` | The pieces the app is built from. Nothing in here is needed to run the site. |

## How it is published

GitHub Pages serves this folder. Any change pushed to the `main` branch goes live within a minute or two.

## Scores update themselves

A scheduled job (`.github/workflows/update-scores.yml`) runs several times a day. It reads every team's MaxPreps schedule page, cross-checks each game against the other school's page, and republishes the app only when something changed.

- It never erases a score that is already in the app, and a page that fails to load changes nothing for that team.
- `source/overrides.json` holds corrections made by hand. They win over MaxPreps.
- `source/updater/last-run.txt` says what the last update changed. Anything the job could not reconcile shows up in the app's admin screen under "Needs a look."
- To run it right now: open the **Actions** tab on GitHub, choose **Update scores**, and click **Run workflow**.

Rosters and stat leaders are a snapshot (`source/static.json`) and do not update on their own.

## Changing things

- **Admin screen:** add `#admin` to the end of the site address to show the gear button, then sign in with the owner's Google account. Changes save to the shared database (Firebase project in `source/firebase.json`) and show for everyone. The Inbox tab holds reported scores, trusted-source applications and photos waiting for approval.
- **App look:** chosen in the admin screen (coach's chalkboard, scoreboard or the original).
- **Playoff brackets:** kept by hand in `source/brackets.json`.
- **Database rules:** pasted into the Firebase console; `source/e2e/test.py` checks them in a real browser.
- **Adding a team or sport:** edit `source/config.json`. Each team has one MaxPreps link; each sport lists the path that follows it.
- **Rebuilding by hand:** `python3 source/updater/update.py` does everything: pulls scores, rebuilds `index.html`.

## Where the data comes from

Schedules and scores come from each team's MaxPreps page. Rosters and stat leaders were read from MaxPreps on October 6, 2026. The Hillcrest freshman schedule and roster come from the team's own sheet. Nothing is made up: anything not posted shows as "not posted."
