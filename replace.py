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
from pathlib import Path

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

# スクリプト自身のディレクトリ
SCRIPT_DIR = Path(__file__).resolve().parent


# ─── ユーティリティ ────────────────────────────────────────────────

def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


def find_local_repos(base: Path) -> list[Path]:
    """base 以下を再帰的に走査し、.git ディレクトリを持つフォルダを返す。"""
    repos = []
    for root, dirs, _ in os.walk(base):
        root_path = Path(root)
        if ".git" in dirs:
            repos.append(root_path)
            dirs.clear()  # .git が見つかったらその下は探さない
    return sorted(repos)


# ─── UI ───────────────────────────────────────────────────────────

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


def select_repos_interactive(local_repos: list[Path]) -> list[Path]:
    """番号入力でローカルリポジトリを複数選択させる。"""
    console.print(Rule("[cyan]ローカルリポジトリの選択[/cyan]", style="dim"))
    console.print()
    console.print(f"  [dim]検索パス: {SCRIPT_DIR}[/dim]")
    console.print()

    table = Table(show_header=True, header_style="bold dim", box=None, padding=(0, 2))
    table.add_column("番号", style="cyan", width=6)
    table.add_column("パス", style="white")

    for i, repo in enumerate(local_repos, 1):
        try:
            display = repo.relative_to(SCRIPT_DIR)
        except ValueError:
            display = repo
        table.add_row(str(i), str(display))

    console.print(table)
    console.print()

    while True:
        raw = Prompt.ask(
            "  [bold]番号を選択[/bold] [dim](例: 1,3,5 または all ですべて)[/dim]"
        )
        raw = raw.strip().lower()

        if raw == "all":
            return local_repos

        selected = []
        valid = True
        for token in raw.split(","):
            token = token.strip()
            if not token.isdigit():
                console.print(f"  [red]無効な入力:[/red] '{token}'")
                valid = False
                break
            idx = int(token)
            if not (1 <= idx <= len(local_repos)):
                console.print(f"  [red]番号が範囲外です:[/red] {idx}")
                valid = False
                break
            repo = local_repos[idx - 1]
            if repo not in selected:
                selected.append(repo)

        if valid and selected:
            console.print()
            return selected


def get_inputs():
    console.print(Rule("[cyan]メールアドレスの設定[/cyan]", style="dim"))
    console.print()

    old_email = Prompt.ask("  [bold]置換前のメールアドレス[/bold]")
    new_email = Prompt.ask("  [bold]置換後のメールアドレス[/bold]")
    console.print()

    # ローカルリポジトリを検索
    local_repos = find_local_repos(SCRIPT_DIR)

    if local_repos:
        console.print(
            f"  [green]{len(local_repos)} 件[/green]のローカルリポジトリが見つかりました。"
        )
        console.print()

        mode = Prompt.ask(
            "  [bold]対象リポジトリの指定方法[/bold]",
            choices=["local", "url"],
            default="local",
            show_choices=True,
        )
        console.print()
    else:
        console.print("  [dim]ローカルリポジトリが見つかりませんでした。URLを入力してください。[/dim]")
        console.print()
        mode = "url"

    if mode == "local":
        selected_paths = select_repos_interactive(local_repos)
        # ローカルパスをそのまま返す（文字列として）
        repos = [str(p) for p in selected_paths]
        is_local = True
    else:
        repos_raw = Prompt.ask(
            "  [bold]対象リポジトリ URL[/bold] [dim](カンマ区切りで複数入力可)[/dim]"
        )
        repos = [r.strip() for r in repos_raw.split(",") if r.strip()]
        console.print()
        is_local = False

    return old_email, new_email, repos, is_local


def confirm_plan(old_email: str, new_email: str, repos: list[str], is_local: bool):
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", width=20)
    table.add_column(style="white")

    table.add_row("置換前", f"[red]{old_email}[/red]")
    table.add_row("置換後", f"[green]{new_email}[/green]")
    table.add_row("対象タイプ", "[cyan]ローカル[/cyan]" if is_local else "[blue]リモート URL[/blue]")
    table.add_row("リポジトリ数", str(len(repos)))

    for i, repo in enumerate(repos, 1):
        label = "  リポジトリ" if i == 1 else f"  リポジトリ {i}"
        # ローカルの場合は SCRIPT_DIR からの相対パスで表示
        if is_local:
            try:
                display = Path(repo).relative_to(SCRIPT_DIR)
            except ValueError:
                display = repo
            table.add_row(label, f"[cyan]{display}[/cyan]")
        else:
            table.add_row(label, f"[blue]{repo}[/blue]")

    console.print(
        Panel(table, title="[bold]実行内容の確認[/bold]", border_style="yellow", padding=(1, 2))
    )
    console.print()

    if not Confirm.ask("  [bold]上記の内容で処理を開始しますか？[/bold]", default=False):
        console.print("\n  [dim]キャンセルしました。[/dim]\n")
        sys.exit(0)
    console.print()


# ─── 処理 ─────────────────────────────────────────────────────────

def process_local_repo(repo_path: str, old_email: str, new_email: str):
    """すでにクローン済みのローカルリポジトリを直接書き換える。"""
    path = Path(repo_path)
    name = path.name

    console.print(Rule(f"[bold cyan]{name}[/bold cyan]", style="cyan"))
    console.print()

    # ─── 書き換え前ダブルチェック ───────────────────────────────
    console.print(f"  対象: [cyan]{path}[/cyan]")
    console.print(f"  書き換え: [red]{old_email}[/red] → [green]{new_email}[/green]")
    console.print()
    if not Confirm.ask("  [bold yellow]⚠ この操作はコミット履歴を破壊的に変更します。続行しますか？[/bold yellow]", default=False):
        console.print("  [dim]書き換えをスキップしました。[/dim]\n")
        return
    if not Confirm.ask("  [bold red]⚠ 本当に履歴を書き換えますか？（取り消せません）[/bold red]", default=False):
        console.print("  [dim]書き換えをスキップしました。[/dim]\n")
        return
    console.print()

    callback = (
        f'if email == b"{old_email}":\n'
        f'    return b"{new_email}"\n'
        f'return email\n'
    )

    orig_dir = Path.cwd()
    os.chdir(path)

    try:
        with Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[cyan]{task.description}[/cyan]"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("履歴を書き換え中...", total=None)
            run(["git", "filter-repo", "--force", "--email-callback", callback])

        console.print("  [green]✓[/green] メールアドレスの書き換え完了")
        console.print()

        # origin の確認
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True,
        )
        origin_url = result.stdout.strip() if result.returncode == 0 else None

        if origin_url:
            console.print(f"  origin: [dim]{origin_url}[/dim]")
            # ─── プッシュ前ダブルチェック ───────────────────────────
            if not Confirm.ask(f"  [bold]{origin_url}[/bold] へ強制プッシュしますか？", default=False):
                console.print("  [dim]プッシュをスキップしました。[/dim]")
            elif not Confirm.ask("  [bold red]⚠ 本当に強制プッシュしますか？リモートの履歴が上書きされます。[/bold red]", default=False):
                console.print("  [dim]プッシュをスキップしました。[/dim]")
            else:
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
                _delete_remote_tags(origin_url)
        else:
            console.print("  [dim]origin が設定されていないためプッシュをスキップします。[/dim]")

    finally:
        os.chdir(orig_dir)

    console.print()


def process_remote_repo(repo: str, old_email: str, new_email: str):
    """リモート URL からクローンして書き換え・プッシュする。"""
    name = repo.rstrip("/").split("/")[-1].replace(".git", "")

    console.print(Rule(f"[bold cyan]{name}[/bold cyan]", style="cyan"))
    console.print()

    # ─── 書き換え前ダブルチェック ───────────────────────────────
    console.print(f"  対象URL: [blue]{repo}[/blue]")
    console.print(f"  書き換え: [red]{old_email}[/red] → [green]{new_email}[/green]")
    console.print()
    if not Confirm.ask("  [bold yellow]⚠ この操作はコミット履歴を破壊的に変更します。続行しますか？[/bold yellow]", default=False):
        console.print("  [dim]書き換えをスキップしました。[/dim]\n")
        return
    if not Confirm.ask("  [bold red]⚠ 本当に履歴を書き換えますか？（取り消せません）[/bold red]", default=False):
        console.print("  [dim]書き換えをスキップしました。[/dim]\n")
        return
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

    try:
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

        # origin 再設定（filter-repo で消えるため）
        run(["git", "remote", "add", "origin", repo])
        console.print("  [green]✓[/green] origin を再設定")
        console.print()

        # ─── プッシュ前ダブルチェック ───────────────────────────
        if not Confirm.ask(f"  [bold]{repo}[/bold] へ強制プッシュしますか？", default=False):
            console.print("  [dim]プッシュをスキップしました。[/dim]")
        elif not Confirm.ask("  [bold red]⚠ 本当に強制プッシュしますか？リモートの履歴が上書きされます。[/bold red]", default=False):
            console.print("  [dim]プッシュをスキップしました。[/dim]")
        else:
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
            _delete_remote_tags(repo)
    finally:
        os.chdir("..")

    console.print()


def _delete_remote_tags(repo_url: str):
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


# ─── エントリポイント ──────────────────────────────────────────────

def main():
    banner()
    old_email, new_email, repos, is_local = get_inputs()
    confirm_plan(old_email, new_email, repos, is_local)

    success, failed = [], []

    for repo in repos:
        try:
            if is_local:
                process_local_repo(repo, old_email, new_email)
            else:
                process_remote_repo(repo, old_email, new_email)
            success.append(repo)
        except subprocess.CalledProcessError as e:
            console.print(f"\n  [red]✗ エラーが発生しました:[/red] {e}\n")
            failed.append(repo)
            # カレントディレクトリが変わっていたら元に戻す
            if not is_local:
                name = repo.rstrip("/").split("/")[-1].replace(".git", "")
                if os.path.basename(os.getcwd()) == name:
                    os.chdir("..")

    # サマリー
    console.print(Rule("[bold]処理結果[/bold]", style="dim"))
    console.print()
    if success:
        console.print(f"  [green]✓ 成功:[/green] {len(success)} 件")
        for r in success:
            try:
                display = Path(r).relative_to(SCRIPT_DIR) if is_local else r
            except ValueError:
                display = r
            console.print(f"    [dim]{display}[/dim]")
    if failed:
        console.print(f"  [red]✗ 失敗:[/red] {len(failed)} 件")
        for r in failed:
            try:
                display = Path(r).relative_to(SCRIPT_DIR) if is_local else r
            except ValueError:
                display = r
            console.print(f"    [dim]{display}[/dim]")
    console.print()


if __name__ == "__main__":
    main()
