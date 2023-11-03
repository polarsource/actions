

# Polar GitHub Actions

<div align="center">
  
<a href="https://polar.sh">Website</a>
<span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
<a href="https://polar.sh/faq">FAQ</a>


<p align="center">
  <a href="https://github.com/polarsource/polar/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="Polar is released under the Apache 2.0 license." />
  </a>

  <a href="https://discord.gg/STfRufb32V">
    <img src="https://img.shields.io/badge/chat-on%20discord-7289DA.svg" alt="Discord Chat" />
  </a>

  <a href="https://twitter.com/intent/follow?screen_name=polar_sh">
    <img src="https://img.shields.io/twitter/follow/polar_sh.svg?label=Follow%20@polar_sh" alt="Follow @polar_sh" />
  </a>
</p>
</div>


The Polar GitHub Action integrates data from [Polar](https://polar.sh/) in statically generated markdown or HTML websites.

🧰 Render static HTML / Markdown from your dynamic Polar data  
🔄 Automatic updates via GitHub Actions (Pull Requests or direct push)  
  
Example use cases:
  
💡 Showcase backers by adding their avatars to your repositories README  
💡 Add links to top repositories that are in need of funding to your documentation website  

## Usage


1. Add a HTML comment like this one to your site

```html
<!-- POLAR type=issues org=polarsource repo=polar limit=10 sort=recently_updated -->
```

2. Use the `polarify` GitHub action to [convert](https://github.com/polarsource/actions/commit/5391b344ce3e0106e6dd24fb6c90fdc0e91d8c10) and [update](https://github.com/polarsource/actions/commit/f2c3d98b39b716c84437d4d39995c518c7861514) your website with real Polar data.

Add the following to your GitHub Actions workflow. ([Example](https://github.com/polarsource/actions/blob/main/.github/workflows/self_check_polarify.yaml))

```yaml
- name: Polarify
  uses: polarsource/actions/polarify@main
  with:
    # Update this glob pattern to match the files that you want to update
    path: "**/*.md"
```

Use the polarify in your website build pipeline, or run it regularly and auto-commit the updated data to your website with the [`stefanzweifel/git-auto-commit-action@v4`](https://github.com/stefanzweifel/git-auto-commit-action) action.

## "types"

* `issues` - [[example](./polarify/demo.md)]  - A list of links to the top issues in a org or repository. Options: `org`, `repo`, `limit` (optional), `sort` (optional), `have_pledge` (optional), `have_badge` (optional)
* `backers-avatars` - [[example](./polarify/demo-backers-avatars.md)] - Avatar images and links to GitHub profiles, sorted by backed amount. Options: `org`. Requires `POLAR_API_TOKEN`.

## GitHub Actions Examples

<details>
  <summary><strong>👉 Example with Pull Requests</strong></summary>


```yaml
name: Polarify

on:
  # Run after every push
  push:
    branches: ["main"]

  # Daily at 07:00
  schedule:
    - cron: "0 7 * * *"

jobs:
  polarify:
    name: "Polarify"
    timeout-minutes: 15
    runs-on: ubuntu-22.04

    permissions:
      # Give the default GITHUB_TOKEN write permission to commit and push the changed files back to the repository.
      contents: write
      # Depending on your use-case, you might need to check "Allow GitHub Actions to create and approve pull requests" in the repositories "Actions > General" settings.
      pull-requests: write

    steps:
      - name: Check out code
        uses: actions/checkout@v3

      - name: Polarify
        uses: polarsource/actions/polarify@main
        with:
          # Update this glob pattern to match the files that you want to update
          path: "**/*.md"
        # This is needed if you're accessing private data in the action (type=pledgers), if not, you can skip it!
        env:
          POLAR_API_TOKEN: ${{ secrets.POLAR_API_TOKEN }}

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          title: "Updated data from Polar"
          commit-message: "polar: updated data from Polar"
          body: "Automatic changes from Polar and the Polarify GitHub Action"
          branch: "polarify"
          delete-branch: true # delete the branch after merging
```

</details>

<details>
  <summary><strong>👉 Example with direct push to main</strong></summary>

```yaml
name: Polarify

on:
  # Run after every push
  push:
    branches: ["main"]

  # Daily at 07:00
  schedule:
    - cron: "0 7 * * *"

jobs:
  polarify:
    name: "Polarify"
    timeout-minutes: 15
    runs-on: ubuntu-22.04

    permissions:
      # Give the default GITHUB_TOKEN write permission to commit and push the changed files back to the repository.
      contents: write

    steps:
      - name: Check out code
        uses: actions/checkout@v3

      - name: Polarify
        uses: polarsource/actions/polarify@main
        with:
          # Update this glob pattern to match the files that you want to update
          path: "**/*.md"
        # This is needed if you're accessing private data in the action (type=pledgers), if not, you can skip it!
        env:
          POLAR_API_TOKEN: ${{ secrets.POLAR_API_TOKEN }}

      - uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: Update polar comments
```
</details>

## Example

* [Example Action](https://github.com/polarsource/actions/blob/main/.github/workflows/self_check_polarify.yaml)
* [Example Blog Post](https://github.com/polarsource/actions/blob/main/polarify/demo.md?plain=1)

