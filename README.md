

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

## Usage


1. Add a HTML comment like this one to your site

```html
<!-- POLAR type=issues org=polarsource repo=polar limit=10 sort=recently_updated -->
```

2. Use the `polarify` GitHub action to [convert](https://github.com/polarsource/actions/commit/5391b344ce3e0106e6dd24fb6c90fdc0e91d8c10) and [update](https://github.com/polarsource/actions/commit/f2c3d98b39b716c84437d4d39995c518c7861514) your website with real Polar data.

Add the following to your GitHub Actions workflow. ([Example](https://github.com/polarsource/actions/blob/main/.github/workflows/self_check_polarify.yaml))

```markdown
- name: Polarify
  uses: polarsource/actions/polarify@main
  with:
    # Update this glob pattern to match the files that you want to update
    path: "**/*.md"
```

Use the polarify in your website build pipeline, or run it regularly and auto-commit the updated data to your website with the [`stefanzweifel/git-auto-commit-action@v4`](https://github.com/stefanzweifel/git-auto-commit-action) action.

## Example

* [Example Action](https://github.com/polarsource/actions/blob/main/.github/workflows/self_check_polarify.yaml)
* [Example Blog Post](https://github.com/polarsource/actions/blob/main/polarify/demo.md?plain=1)

