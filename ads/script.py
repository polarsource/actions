# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "polar-sdk",
# ]
# ///

import html
import string
import random
import argparse
import os
import io
from polar_sdk import Polar
from polar_sdk.models import AdvertisementsListResponse


def sync_file(file: io.TextIOWrapper, client: Polar) -> None:
    print("Syncing file: ", file.name)
    contents = file.read()

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

        if args["type"] == "ads":
            benefit_id = args.get("subscription_benefit_id") or args.get("benefit_id")
            if benefit_id is None:
                print(f"Invalid Polar comment, missing benefit_id in: {comment}")
                continue
            rendered = polar_ads(
                client,
                benefit_id=benefit_id,
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
    file.seek(0)
    file.write(contents)


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


def polar_ads(client: Polar, benefit_id: str, height: int, width: int) -> str:
    ads = []
    res: AdvertisementsListResponse | None = client.advertisements.list(
        benefit_id=benefit_id
    )
    while True:
        if res is not None:
            for item in res.result.items:
                ad = f'<a href="{html.escape(item.link_url)}">'
                ad += "<picture>"

                image_url = f"https://polar.sh/embed/ad?id={item.id}"
                if item.image_url_dark is not None:
                    image_url_dark = f"https://polar.sh/embed/ad?id={item.id}&dark=1"
                    ad += f'<source media="(prefers-color-scheme: dark)" srcset="{image_url_dark}">'
                ad += f'<img src="{image_url}" alt="{html.escape(item.text)}" height="{height}" width="{width}" />'

                ad += "</picture>"
                ad += "</a>"

                ads.append(ad)

            res = res.next()
            if res is None:
                break

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
    parser = argparse.ArgumentParser(description="Polarify CLI Tool")
    parser.add_argument(
        "files",
        type=argparse.FileType("r+", encoding="utf-8"),
        nargs="+",
        help="Paths to the files to synchronize",
    )


    env_token = os.environ.get("POLAR_API_TOKEN")
    parser.add_argument(
        "--token",
        default=env_token,
        required=env_token is None,
        help="Polar API access token",
    )

    args = parser.parse_args()

    client = Polar(args.token)
    for file in args.files:
        sync_file(file, client)
