# git-email-replace

Git のコミット履歴に含まれるメールアドレスを一括置換するCLIツールです。

> AIを使用して作成した個人的な用途のツールです。

## 必要なもの

- Python 3.10+
- [git-filter-repo](https://github.com/newren/git-filter-repo)
- [rich](https://github.com/Textualize/rich)

```bash
pip install rich git-filter-repo
```

## 使い方

```bash
python replace.py
```

起動後、対話形式で以下を入力します。

1. 置換前のメールアドレス
2. 置換後のメールアドレス
3. 対象リポジトリの選択（ローカル検出 または URL入力）

スクリプトと同じフォルダ以下に `.git` ディレクトリがある場合は、番号を入力して選択できます。複数選択はカンマ区切り（例: `1,3`）、すべて選択は `all`。

## 注意

- `git filter-repo` によりコミット履歴が**書き換えられます**（破壊的な操作です）
- 共有リポジトリに使用する場合は、他のコントリビューターに事前に連絡してください
- 実行前にバックアップを取ることを推奨します

## ライセンス

[UNLICENSE](./UNLICENSE)

## Disclaimer

> [!CAUTION]
>
> - **Disclaimer of Warranty**: This software is provided "as-is" without warranty of any kind. The creator makes no warranties, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement of third-party intellectual property rights.
> - **Limitation of Liability**: In no event shall the creator be liable for any damages, losses, or issues (including direct or indirect) arising from the use of this software (including installation, customization, and publication), to the maximum extent permitted by law.
> - **AI Usage Disclosure**: Parts of this software (code and design) have been created with the assistance of Generative AI technologies. Therefore, the creator cannot fully guarantee that such content does not infringe upon the intellectual property rights of third parties.
> - **Legal Interpretation**: The creator is not a legal expert and cannot provide definitive legal interpretations of this agreement or OSS licenses. If you have any concerns, please consult a legal professional at your own responsibility.
> - **Self-Responsibility**: All actions related to the use of this software are to be performed at the user's own risk and discretion.
