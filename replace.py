#!/usr/bin/env python3
"""
Gitリポジトリのコミット履歴に含まれるメールアドレスを
git filter-repo を使って一括置換するスクリプト。
"""

import subprocess
import os

# ===== 入力 =====
old_email = input("Enter old email: ").strip()
new_email = input("Enter new email: ").strip()
repos_input = input("Enter repo URLs (comma separated): ")
repos = [r.strip() for r in repos_input.split(",")]

# ===== 実行 =====
for repo in repos:
    if not repo:
        continue

    name = repo.rstrip("/").split("/")[-1].replace(".git", "")

    print("----------------------------------------")
    print(f"Processing {name}...")

    subprocess.run(["git", "clone", repo], check=True)
    os.chdir(name)

    callback = (
        f'if email == b"{old_email}":\n'
        f'    return b"{new_email}"\n'
        f'return email\n'
    )
    subprocess.run(
        ["git", "filter-repo", "--force", "--email-callback", callback],
        check=True,
    )

    # origin を再設定（filter-repo で消えるため）
    subprocess.run(["git", "remote", "add", "origin", repo], check=True)

    # push 前の確認
    print(f"Ready to push changes to {repo}")
    confirm = input("Do you want to push these changes? (y/N): ").strip().lower()

    if confirm == "y":
        print("Pushing...")
        # 全ブランチ強制 push
        subprocess.run(["git", "push", "--force", "--all"], check=True)

        # リモートタグ削除
        result = subprocess.run(
            ["git", "ls-remote", "--tags", "origin"],
            capture_output=True, text=True, check=True,
        )
        for line in result.stdout.splitlines():
            if "refs/tags/" in line:
                tagname = line.split("refs/tags/")[-1].split("^{}")[0]
                subprocess.run(
                    ["git", "push", "origin", "--delete", tagname], check=True
                )
    else:
        print("Push skipped.")

    os.chdir("..")
    # 作業ディレクトリの削除（必要に応じてコメントを外す）
    # shutil.rmtree(name)
