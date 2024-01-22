from dataclasses import dataclass
import html
import string
import sys
import urllib.request
import urllib.parse
import json
import random
import inspect
import os

POLAR_API_BASE = os.getenv("POLAR_API_BASE", "https://api.polar.sh")
POLAR_API_TOKEN = os.getenv("POLAR_API_TOKEN", None)


def polarify() -> None:
    args = sys.argv
    print(args)
    for path in sys.argv[1:]:
        print(f"Polarifying {path}")
        polarify_file(path)


def polarify_file(path: str) -> None:
    with open(path, "r+") as f:
        contents = f.read()

    if "<!-- POLAR" not in contents:
        return None

    next_start = 0
    while True:
        idx = contents.find("<!-- POLAR", next_start)

        if idx < 0:
            break

        end_of_start = contents.find("-->", idx + 1)

        comment = contents[idx : end_of_start + 3]

        next_start = end_of_start + 3

        args = parse_comment(comment)

        if "type" not in args:
            print(f"Invalid Polar comment, no type found in: {comment}")
            continue

        if "id" not in args:
            args["id"] = "".join(
                random.choice(string.ascii_lowercase) for i in range(8)
            )

        end_tag = f"<!-- POLAR-END id={args['id']} -->"

        existing_end = contents.find(end_tag, idx)
        append_from = existing_end + len(end_tag) if existing_end > 0 else next_start

        print("Expanding: ", comment)

        rendered = ""

        if args["type"] == "issues":
            rendered = polar_issues(
                org=args["org"],
                repo=args["repo"],
                limit=int(args["limit"]) if "limit" in args else 5,
                sort=args["sort"]
                if "sort" in args
                else "funding_goal_desc_and_most_positive_reactions",
                have_pledge=bool(args["have_pledge"])
                if "have_pledge" in args
                else None,
                have_badge=bool(args["have_badge"]) if "have_badge" in args else None,
            )

        elif args["type"] == "backers-avatars":
            rendered = polar_backers_avatars(org=args["org"])
        elif args["type"] == "ads":
            rendered = polar_ads(
                subscription_benefit_id=args["subscription_benefit_id"],
                height=int(args["height"]),
                width=int(args["width"]),
            )
        else:
            print(f"Invalid Polar comment, unexpected type in: {comment}")

        start_tag = render_start_tag(args)

        contents = (
            contents[0:idx]
            + start_tag
            + "\n"
            + rendered
            + "\n"
            + end_tag
            + contents[append_from:]
        )

        # adjust next start
        next_start = idx + len(start_tag) + 1 + len(rendered) + 1 + len(end_tag)

    # Write result
    with open(path, "w") as f:
        f.write(contents)


def render_start_tag(args: dict[str, str]) -> str:
    p: list[str] = []
    p += ["<!-- POLAR"]

    p += ["type=" + args["type"]]
    p += ["id=" + args["id"]]
    p += ["org=" + args["org"]] if "org" in args else []
    p += ["repo=" + args["repo"]] if "repo" in args else []
    p += [f"{k}={v}" for k, v in args.items() if k not in ["type", "id", "org", "repo"]]
    p += ["-->"]
    return " ".join(p)


@dataclass
class Organization:
    id: str
    name: str


def api_organization_lookup(org: str) -> Organization:
    params = {"platform": "github", "organization_name": org}
    contents = urllib.request.urlopen(
        f"{POLAR_API_BASE}/api/v1/organizations/lookup?{urllib.parse.urlencode(params)}"
    )
    data = json.load(contents)
    return Organization(**data)


@dataclass
class CurrencyAmount:
    currency: str
    amount: int

    @classmethod
    def init(cls, js: dict[str, any]):
        data = {}
        for k, v in js.items():
            if k in inspect.signature(cls).parameters:
                data[k] = v
        return cls(**data)


@dataclass
class Pledger:
    name: str
    github_username: str | None
    avatar_url: str

    @classmethod
    def init(cls, js: dict[str, any]):
        data = {}
        for k, v in js.items():
            if k in inspect.signature(cls).parameters:
                data[k] = v
        return cls(**data)


@dataclass
class Pledge:
    id: str
    amount: CurrencyAmount
    pledger: Pledger

    @classmethod
    def init(cls, jsonElement):
        data = {}
        for k, v in jsonElement.items():
            if k in inspect.signature(cls).parameters:
                if k == "amount":
                    data[k] = CurrencyAmount.init(v)
                elif k == "pledger":
                    data[k] = Pledger.init(v)
                else:
                    data[k] = v
        return cls(**data)


@dataclass
class ListPledges:
    items: list[Pledge]

    @classmethod
    def init(cls, jsonElement):
        data = {}
        for k, v in jsonElement.items():
            if k in inspect.signature(cls).parameters:
                if k == "items":
                    data[k] = list(map(Pledge.init, v))
                else:
                    data[k] = v
        return cls(**data)


def api_pledges_search(org: str) -> ListPledges:
    if not POLAR_API_TOKEN:
        print("POLAR_API_TOKEN is not set", file=sys.stderr)
        exit(1)

    params = {"platform": "github", "organization_name": org}
    request = urllib.request.Request(
        url=f"{POLAR_API_BASE}/api/v1/pledges/search?{urllib.parse.urlencode(params)}",
        headers={"Authorization": f"Bearer {POLAR_API_TOKEN}"},
    )
    contents = urllib.request.urlopen(request)
    data = json.load(contents)
    return ListPledges.init(data)


def polar_issues(
    org: str,
    repo: str | None,
    limit: int,
    sort: str,
    have_pledge: bool | None,
    have_badge: bool | None,
) -> str:
    params = {"platform": "github", "organization_name": org}
    if repo:
        params["repository_name"] = repo
    params["sort"] = sort

    if have_pledge is not None:
        params["have_pledge"] = have_pledge
    if have_badge is not None:
        params["have_badge"] = have_badge

    contents = urllib.request.urlopen(
        f"{POLAR_API_BASE}/api/v1/issues/search?{urllib.parse.urlencode(params)}"
    )
    data = json.load(contents)

    list_items = []

    for item in data["items"][0:limit]:
        org_name = item["repository"]["organization"]["name"]
        repo_name = item["repository"]["name"]
        issue_number = item["number"]
        issue_title = item["title"]
        txt = f"#{issue_number} {issue_title}"

        # With funding goal
        if (
            item["funding"]["funding_goal"]
            and item["funding"]["funding_goal"]["amount"] > 0
        ):
            funding_dollars = item["funding"]["pledges_sum"]["amount"] / 100
            goal_dollars = item["funding"]["funding_goal"]["amount"] / 100

            percent = funding_dollars / goal_dollars * 100

            txt += f" – 💰 {percent:.0f}% of ${goal_dollars}"

        # Pledges and no funding goal
        elif item["funding"]["pledges_sum"]["amount"] > 0:
            dollars = item["funding"]["pledges_sum"]["amount"] / 100
            txt += f" – 💰 ${dollars}"

        link = f"https://github.com/{org_name}/{repo_name}/issues/{issue_number}"
        output = f"* [{txt}]({link})"
        list_items.append(output)

    bullets = "\n".join(list_items)

    return "\n" + bullets + "\n"


def polar_backers_avatars(org: str) -> str:
    pledges = api_pledges_search(org)

    @dataclass
    class DedupPledger:
        name: str
        avatar_url: str
        github_username: str | None
        amount: int

    deduplicated: dict[str, DedupPledger] = {}

    for p in pledges.items:
        if not p.pledger.avatar_url:
            continue

        if p.pledger.avatar_url in deduplicated:
            existing = deduplicated.get(p.pledger.avatar_url)
            existing.amount = existing.amount + p.amount.amount
            deduplicated[p.pledger.avatar_url] = existing
        else:
            deduplicated[p.pledger.avatar_url] = DedupPledger(
                name=p.pledger.name,
                avatar_url=p.pledger.avatar_url,
                amount=p.amount.amount,
                github_username=p.pledger.github_username,
            )

    ls = deduplicated.values()
    sorted(ls, key=lambda x: x.amount)

    res = ""

    for p in ls:
        item = f'<img src="{p.avatar_url}" width=100 height=100 />'

        if p.github_username:
            item = f'<a href="https://github.com/{p.github_username}">{item}</a>'

        res += item + "\n"

    return res


def polar_ads(subscription_benefit_id: str, height: int, width: int) -> str:
    params = {"subscription_benefit_id": subscription_benefit_id}

    request = urllib.request.Request(
        f"{POLAR_API_BASE}/api/v1/advertisements/campaigns/search?{urllib.parse.urlencode(params)}",
        headers={"Authorization": f"Bearer {POLAR_API_TOKEN}"},
    )
    contents = urllib.request.urlopen(request)

    data = json.load(contents)

    ads = []

    for item in data["items"]:
        ad = f'<a href="{html.escape(item["link_url"])}">'
        ad += "<picture>"

        image_url = f'https://polar.sh/embed/ad?id={item["id"]}'
        if "image_url_dark" in item and item["image_url_dark"]:
            image_url_dark = f'https://polar.sh/embed/ad?id={item["id"]}&dark=1'
            ad += f'<source media="(prefers-color-scheme: dark)" srcset="{image_url_dark}">'
        ad += f'<img src="{image_url}" alt="{html.escape(item["text"])}" height="{height}" width="{width}" />'

        ad += "</picture>"
        ad += "</a>"

        ads.append(ad)

    return "\n" + "\n".join(ads) + "\n"


def parse_comment(comment: str) -> dict[str, str]:
    """
    Parses a str like "<!-- POLAR type=issues org=polarsource repo=polar limit=10 -->"
    into a dict: {"type":"issues", "org": "polarsource", ...}
    """

    kv: dict[str, str] = {}
    for word in comment.split(" "):
        if word in ["<!--", "POLAR", "-->"]:
            continue
        k, v = word.split("=")
        kv[k] = v
    return kv


if __name__ == "__main__":
    polarify()
