# Solid black GitHub profile

The panel is one self-contained SVG. Its background stays black in both GitHub themes; GitHub's page padding outside the image still follows the viewer's theme.

## Quick installation

1. Upload `profile.svg` to the root of your `dryhour/dryhour` repository.
2. Replace the old image block in your README with the line in the included README.md. Preserve any other README content you want.

This immediately fixes the white gaps. The uploaded SVG is a snapshot until you set up refreshes.

## Keep the numbers updated

Copy `scripts/build_profile.py`, `assets/profile/`, and `.github/workflows/profile.yml` into the same repository, preserving their folders. The `.github` folder may be hidden in Finder; Command-Shift-Period shows hidden files.

The included workflow refreshes once daily, and can also be run under Actions → Refresh profile panel → Run workflow. It commits only the generated panel and card assets. It uses the built-in GitHub token; no personal access token or private-data access is required. Repository rules must allow this workflow to write to the default branch.

Card providers and GitHub's image cache may delay data. If a provider fails or returns an error card, the workflow fails and leaves the previous published panel intact. Scheduled runs are controlled by GitHub and may be delayed or disabled on inactive public repositories. The workflow is provided but has not been run in your repository.

You can also refresh manually with Python 3.12 or newer:

```sh
python scripts/build_profile.py
```

The view counter was omitted: fetching it from a scheduled job would count refresh requests rather than actual profile visits. The followers badge is retained. The heading is static, matching the original white font and text; stats retain their original Tokyo Night colors.

Public card providers: https://github.com/anuraghazra/github-readme-stats and https://github.com/DenverCoder1/github-readme-streak-stats and https://shields.io/.
