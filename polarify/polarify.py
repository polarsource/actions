import string
import sys
import urllib.request
import urllib.parse
import json
import random


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

        if args["type"] == "issues":
            print("Expanding: ", comment)

            rendered = polar_issues(
                org=args["org"],
                repo=args["repo"],
                limit=int(args["limit"]) if "limit" in args else 5,
                sort=args["sort"]
                if "sort" in args
                else "funding_goal_desc_and_most_positive_reactions",
                have_pledge=bool(args["have_pledge"])
                if "have_pledge" in args
                else False,
                have_badge=bool(args["have_badge"]) if "have_badge" in args else False,
            )

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

        else:
            print(f"Invalid Polar comment, unexpected type in: {comment}")

    # Write result
    with open(path, "w") as f:
        f.write(contents)


def render_start_tag(args: dict[str, str]) -> str:
    p: list[str] = []
    p += ["<!-- POLAR"]
    p += ["type=" + args["type"]]
    p += ["id=" + args["id"]]
    p += ["org=" + args["org"]] if args["org"] else []
    p += ["repo=" + args["repo"]] if args["repo"] else []
    p += [f"{k}={v}" for k, v in args.items() if k not in ["type", "id", "org", "repo"]]
    p += ["-->"]
    return " ".join(p)


def polar_issues(
    org: str,
    repo: str | None,
    limit: int,
    sort: str,
    have_pledge: bool,
    have_badge: bool,
) -> str:
    params = {"platform": "github", "organization_name": org}
    if repo:
        params["repository_name"] = repo
    params["sort"] = sort
    params["have_pledge"] = have_pledge
    params["have_badge"] = have_badge

    contents = urllib.request.urlopen(
        f"https://api.polar.sh/api/v1/issues/search?{urllib.parse.urlencode(params)}"
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
