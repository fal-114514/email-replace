#!/usr/bin/env python3
"""
Git コミット履歴のメールアドレスを一括置換するツール。
依存: git, git-filter-repo, rich
  pip install rich
  pip install git-filter-repo
"""

import os
import subprocess
import sys

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.rule import Rule
except ImportError:
    print("エラー: rich がインストールされていません。")
    print("  pip install rich  を実行してください。")
    sys.exit(1)

console = Console()


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


def banner():
    console.print()
    console.print(
        Panel.fit(
            "[bold white]Git メールアドレス 一括置換ツール[/bold white]\n"
            "[dim]git filter-repo を使ってコミット履歴を書き換えます[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()


def get_inputs():
    console.print(Rule("[cyan]設定入力[/cyan]", style="dim"))
    console.print()

    old_email = Prompt.ask("  [bold]置換前のメールアドレス[/bold]")
    new_email = Prompt.ask("  [bold]置換後のメールアドレス[/bold]")
    console.print()
    repos_raw = Prompt.ask(
        "  [bold]対象リポジトリ URL[/bold] [dim](カンマ区切りで複数入力可)[/dim]"
    )
    repos = [r.strip() for r in repos_raw.split(",") if r.strip()]
    console.print()
    return old_email, new_email, repos


def confirm_plan(old_email: str, new_email: str, repos: list[str]):
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", width=18)
    table.add_column(style="white")

    table.add_row("置換前", f"[red]{old_email}[/red]")
    table.add_row("置換後", f"[green]{new_email}[/green]")
    table.add_row("リポジトリ数", str(len(repos)))

    for i, repo in enumerate(repos, 1):
        label = "  リポジトリ" if i == 1 else f"  リポジトリ {i}"
        table.add_row(label, f"[blue]{repo}[/blue]")

    console.print(
        Panel(table, title="[bold]実行内容の確認[/bold]", border_style="yellow", padding=(1, 2))
    )
    console.print()

    if not Confirm.ask("  [bold]上記の内容で処理を開始しますか？[/bold]", default=False):
        console.print("\n  [dim]キャンセルしました。[/dim]\n")
        sys.exit(0)
    console.print()


def process_repo(repo: str, old_email: str, new_email: str):
    name = repo.rstrip("/").split("/")[-1].replace(".git", "")

    console.print(Rule(f"[bold cyan]{name}[/bold cyan]", style="cyan"))
    console.print()

    # clone
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[cyan]{task.description}[/cyan]"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("クローン中...", total=None)
        run(["git", "clone", repo])

    console.print("  [green]✓[/green] クローン完了")

    os.chdir(name)

    # filter-repo
    callback = (
        f'if email == b"{old_email}":\n'
        f'    return b"{new_email}"\n'
        f'return email\n'
    )
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[cyan]{task.description}[/cyan]"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("履歴を書き換え中...", total=None)
        run(["git", "filter-repo", "--force", "--email-callback", callback])

    console.print("  [green]✓[/green] メールアドレスの書き換え完了")

    # origin 再設定
    run(["git", "remote", "add", "origin", repo])
    console.print("  [green]✓[/green] origin を再設定")
    console.print()

    # push 確認
    if Confirm.ask(f"  [bold]{repo}[/bold] へ強制プッシュしますか？", default=False):
        console.print()

        with Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[cyan]{task.description}[/cyan]"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("プッシュ中...", total=None)
            run(["git", "push", "--force", "--all"])

        console.print("  [green]✓[/green] 全ブランチのプッシュ完了")

        # リモートタグ削除
        result = run(
            ["git", "ls-remote", "--tags", "origin"],
            capture_output=True, text=True,
        )
        deleted = 0
        for line in result.stdout.splitlines():
            if "refs/tags/" in line and "^{}" not in line:
                tagname = line.split("refs/tags/")[-1]
                run(["git", "push", "origin", "--delete", tagname])
                deleted += 1

        if deleted:
            console.print(f"  [green]✓[/green] リモートタグ {deleted} 件を削除")
    else:
        console.print("  [dim]プッシュをスキップしました。[/dim]")

    console.print()
    os.chdir("..")


def main():
    banner()
    old_email, new_email, repos = get_inputs()
    confirm_plan(old_email, new_email, repos)

    success, failed = [], []

    for repo in repos:
        try:
            process_repo(repo, old_email, new_email)
            success.append(repo)
        except subprocess.CalledProcessError as e:
            console.print(f"\n  [red]✗ エラーが発生しました:[/red] {e}\n")
            failed.append(repo)
            name = repo.rstrip("/").split("/")[-1].replace(".git", "")
            if os.path.basename(os.getcwd()) == name:
                os.chdir("..")

    # サマリー
    console.print(Rule("[bold]処理結果[/bold]", style="dim"))
    console.print()
    if success:
        console.print(f"  [green]✓ 成功:[/green] {len(success)} 件")
        for r in success:
            console.print(f"    [dim]{r}[/dim]")
    if failed:
        console.print(f"  [red]✗ 失敗:[/red] {len(failed)} 件")
        for r in failed:
            console.print(f"    [dim]{r}[/dim]")
    console.print()


if __name__ == "__main__":
    main()
