#!/usr/bin/env python3
"""
Figma Extended Client & CLI Utility for Antigravity Workstation.
Supports all Figma scopes: comments (read/write), dev resources (read/write),
variables (tokens), version history, and published components.
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
import time

FIGMA_API_BASE = "https://api.figma.com/v1"

def get_token():
    token = os.environ.get("FIGMA_API_KEY") or os.environ.get("FIGMA_TOKEN") or os.environ.get("FIGMA_ACCESS_TOKEN")
    if not token:
        # Check ~/.bashrc or config
        bashrc_path = os.path.expanduser("~/.bashrc")
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("export FIGMA_API_KEY="):
                        token = line.split("=", 1)[1].strip().strip("\"'")
                        break
    if not token:
        raise ValueError("FIGMA_API_KEY environment variable is required.")
    return token

def figma_request(endpoint, method="GET", payload=None, retries=3):
    token = get_token()
    url = f"{FIGMA_API_BASE}{endpoint}" if endpoint.startswith("/") else f"{FIGMA_API_BASE}/{endpoint}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    
    headers = {
        "X-Figma-Token": token,
        "User-Agent": "Antigravity-Figma-Client/1.0"
    }
    if data is not None:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {"status": 200, "message": "OK"}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", 2))
                time.sleep(retry_after)
                continue
            error_body = e.read().decode("utf-8", errors="replace")
            try:
                parsed_err = json.loads(error_body)
                return {"error": True, "status": e.code, "message": parsed_err.get("err") or parsed_err.get("message") or error_body}
            except Exception:
                return {"error": True, "status": e.code, "message": error_body}
        except Exception as e:
            return {"error": True, "message": str(e)}

    return {"error": True, "message": "Max retries exceeded"}

# Core operations
def get_me():
    return figma_request("/me")

def get_comments(file_key, as_md=True):
    query = "?as_md=true" if as_md else ""
    return figma_request(f"/files/{file_key}/comments{query}")

def post_comment(file_key, message, node_id=None, x=None, y=None, parent_id=None):
    payload = {"message": message}
    if parent_id:
        payload["comment_id"] = parent_id
    if node_id:
        payload["client_meta"] = {"node_id": node_id}
        if x is not None and y is not None:
            payload["client_meta"]["node_offset"] = {"x": float(x), "y": float(y)}
    elif x is not None and y is not None:
        payload["client_meta"] = {"x": float(x), "y": float(y)}
    
    return figma_request(f"/files/{file_key}/comments", method="POST", payload=payload)

def delete_comment(file_key, comment_id):
    return figma_request(f"/files/{file_key}/comments/{comment_id}", method="DELETE")

def get_dev_resources(file_key, node_ids=None):
    query = f"?node_ids={node_ids}" if node_ids else ""
    return figma_request(f"/files/{file_key}/dev_resources{query}")

def post_dev_resource(file_key, node_id, name, url):
    payload = {
        "dev_resources": [
            {
                "file_key": file_key,
                "node_id": node_id,
                "name": name,
                "url": url
            }
        ]
    }
    return figma_request("/dev_resources", method="POST", payload=payload)

def get_variables(file_key):
    return figma_request(f"/files/{file_key}/variables/local")

def get_versions(file_key):
    return figma_request(f"/files/{file_key}/versions")

def get_components(file_key):
    return figma_request(f"/files/{file_key}/components")

def main():
    parser = argparse.ArgumentParser(description="Figma Extended API CLI for Antigravity")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")

    # me
    subparsers.add_parser("me", help="Get current authenticated user info")

    # comments
    p_get_comments = subparsers.add_parser("comments", help="Get comments on a file")
    p_get_comments.add_argument("file_key", help="Figma file key")

    # post-comment
    p_post_comment = subparsers.add_parser("post-comment", help="Post a comment or reply")
    p_post_comment.add_argument("file_key", help="Figma file key")
    p_post_comment.add_argument("--message", "-m", required=True, help="Comment text")
    p_post_comment.add_argument("--node-id", "-n", help="Target node ID to pin comment to")
    p_post_comment.add_argument("--parent-id", "-p", help="Parent comment ID for threaded replies")

    # dev-resources
    p_get_dev = subparsers.add_parser("dev-resources", help="Get dev resources on a file")
    p_get_dev.add_argument("file_key", help="Figma file key")
    p_get_dev.add_argument("--node-ids", help="Comma-separated node IDs")

    # post-dev-resource
    p_post_dev = subparsers.add_parser("post-dev-resource", help="Attach dev resource to node")
    p_post_dev.add_argument("file_key", help="Figma file key")
    p_post_dev.add_argument("--node-id", "-n", required=True, help="Target node ID")
    p_post_dev.add_argument("--name", required=True, help="Resource label/title")
    p_post_dev.add_argument("--url", "-u", required=True, help="External resource URL (GitHub, Storybook, etc.)")

    # variables
    p_vars = subparsers.add_parser("variables", help="Get local variables & design tokens")
    p_vars.add_argument("file_key", help="Figma file key")

    # versions
    p_vers = subparsers.add_parser("versions", help="Get file version history")
    p_vers.add_argument("file_key", help="Figma file key")

    # components
    p_comps = subparsers.add_parser("components", help="Get published components")
    p_comps.add_argument("file_key", help="Figma file key")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "me":
            res = get_me()
        elif args.command == "comments":
            res = get_comments(args.file_key)
        elif args.command == "post-comment":
            res = post_comment(args.file_key, args.message, node_id=args.node_id, parent_id=args.parent_id)
        elif args.command == "dev-resources":
            res = get_dev_resources(args.file_key, node_ids=args.node_ids)
        elif args.command == "post-dev-resource":
            res = post_dev_resource(args.file_key, args.node_id, args.name, args.url)
        elif args.command == "variables":
            res = get_variables(args.file_key)
        elif args.command == "versions":
            res = get_versions(args.file_key)
        elif args.command == "components":
            res = get_components(args.file_key)
        else:
            parser.print_help()
            sys.exit(1)

        print(json.dumps(res, indent=2))
        if isinstance(res, dict) and res.get("error"):
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": True, "message": str(e)}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
