# scripts/update_languages.py
"""
Fetch repository languages from GitHub API, compute percentages,
and replace the block between:
<!--LANGUAGE_SECTION_START-->
and
<!--LANGUAGE_SECTION_END-->
in README.md with a generated Markdown table.
"""

import os
import requests
import sys

GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")  # owner/repo (set automatically in Actions)
if not GITHUB_REPOSITORY:
    print("GITHUB_REPOSITORY not set (expected OWNER/REPO).", file=sys.stderr)
    sys.exit(1)

owner, repo = GITHUB_REPOSITORY.split("/")
token = os.environ.get("GITHUB_TOKEN")

api_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
headers = {"Accept": "application/vnd.github.v3+json"}
if token:
    headers["Authorization"] = f"token {token}"

resp = requests.get(api_url, headers=headers)
if resp.status_code != 200:
    print(f"Failed to fetch languages: {resp.status_code} {resp.text}", file=sys.stderr)
    sys.exit(1)

languages = resp.json()  # e.g. {"Python": 12345, "JavaScript": 6789}
total = sum(languages.values())
if total == 0:
    md = "No detectable languages."
else:
    sorted_langs = sorted(languages.items(), key=lambda kv: kv[1], reverse=True)
    lines = []
    lines.append("| Language | Bytes | Percent |")
    lines.append("|---|---:|---:|")
    for lang, bytes_count in sorted_langs:
        percent = bytes_count / total * 100
        lines.append(f"| {lang} | {bytes_count:,} | {percent:.1f}% |")
    md = "\n".join(lines)

start_marker = "<!--LANGUAGE_SECTION_START-->"
end_marker = "<!--LANGUAGE_SECTION_END-->"
readme_path = "README.md"

with open(readme_path, "r", encoding="utf-8") as f:
    content = f.read()

if start_marker in content and end_marker in content:
    pre, rest = content.split(start_marker, 1)
    _, post = rest.split(end_marker, 1)
    new_block = f"{start_marker}\n\n{md}\n\n{end_marker}"
    new_content = pre + new_block + post
else:
    # If markers missing, append at end
    new_block = f"\n\n{start_marker}\n\n{md}\n\n{end_marker}\n"
    new_content = content + new_block

if new_content != content:
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("README.md updated.")
else:
    print("README.md already up to date.")
