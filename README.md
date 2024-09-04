# Polar GitHub Actions

<div align="center">

<a href="https://polar.sh">Website</a>
<span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
<a href="https:/docs.polar.sh">Documentation</a>


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

Integrate Polar into your GitHub Actions workflows easily thanks to our ready-to-use actions.

## `polarsource/actions/auth`

This action allows you to generate a temporary Polar API token for your workflow, **without the need to generate a long-lived personal access token**.

### 1. Link your repository on Polar

You'll need to link the repository running the workflow to your Polar organization, as described [here](https://docs.polar.sh/github/install).

### 2. Add the action to your workflow

Your workflow will need the `id-token` permission:

```yaml
permissions:
  id-token: write
```

You can then use the action like this:

```yaml
- uses: polarsource/actions/auth@v1
  id: polar
  with:
    scope: 'openid benefits:read products:read'
```

The only required parameter, `scope`, is a space-separated list of scopes you want to grant to the resulting token. The token is available as an output of the action. For example, you can use it like this:

```yaml
- name: 'Check Polar access'
  run: |
    resp=$(curl -XGET -H "Authorization: Bearer ${{ steps.polar.outputs.token }}" https://api.polar.sh/api/v1/oauth2/userinfo)
    echo $resp
```

> [!NOTE]
> The generated token is an [organization access token](/docs/api/authentication#user-vs-organization-access-tokens).

> [!TIP]
> **How does it work?**
>
> We use [GitHub OpenID Connect](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect) mechanism to authenticate the request truly comes for your repository's workflow. Since you've linked the repository on Polar, we can trust the action comes from you and deliver a short-lived token.

### Scenarios

**Tag an issue as `priority` if the author has access to a specific benefit**

```yaml
name: Priority Issues

on:
  issues:
    types: [opened]

permissions:
  id-token: write
  contents: read
  issues: write

env:
  POLAR_BENEFIT_ID: 00000000-0000-0000-0000-000000000000

jobs:
  check-priority:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: polarsource/actions/auth@v1
        id: polar
        with:
          scope: 'benefits:read'

      - name: 'Check if author has access to priority answers'
        id: check-benefit
        run: |
          resp=$(curl -XGET -H "Authorization: Bearer ${{ steps.polar.outputs.token }}" https://api.polar.sh/api/v1/benefits/${{ env.POLAR_BENEFIT_ID }}/grants?is_granted=true&github_user_id=${{ github.event.issue.user.id }})
          count=$(($(jq -r '.pagination | .total_count' <<< "${resp}")))
          echo "count=$(echo $count)" >> $GITHUB_OUTPUT

      - name: 'Add the priority label'
        if: steps.check-benefit.outputs.count > 0
        run: gh issue edit "$NUMBER" --add-label "$LABELS"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GH_REPO: ${{ github.repository }}
          NUMBER: ${{ github.event.issue.number }}
          LABELS: priority
```

## `polarsource/actions/ads`

This action allows you to automatically synchronize the ads created by your customers as part of an [Ad benefit](https://docs.polar.sh/benefits/ads) in a Markdown or HTML page.

### 1. Add the magic comment to your document

```html
<!-- POLAR type=ads benefit_id=00000000-0000-0000-0000-000000000000 width=100 height=100 -->
```

`benefit_id` is the ID of your ad benefit. You can find it in your dashboard, on the `Benefits` page.

### 2. Add the action to your workflow

```yaml
- name: Sync Polar ads
  uses: polarsource/actions/ads@main
  with:
    path: README.md
    token: ${{ secrets.POLAR_ACCESS_TOKEN }}
```

`path` is the path of the file you want to update. Glob patterns are supported. `token` is a valid Polar access token, which you can set in your repository secrets or generate using our [auth action](#polarsourceactionsauth).

### Scenarios

**Update ads in README.md on push and every day**

```yaml
name: Ads sync example

on:
  push:
    branches: ["main"]

  schedule:
    - cron: "0 7 * * *"

jobs:
  sync:
    runs-on: ubuntu-latest

    permissions:
      contents: write

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - uses: polarsource/actions/auth@v1
        id: polar
        with:
          scope: 'openid'

      - name: Sync Polar ads
        uses: polarsource/actions/ads@v1
        with:
          path: ads/demo.md
          token: ${{ steps.polar.outputs.token }}

      - uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: Update Polar ads
```

### Demo

<!-- POLAR type=ads benefit_id=c43080e5-c99f-43d2-b72c-e25ac374dd2b width=100 height=100 -->
