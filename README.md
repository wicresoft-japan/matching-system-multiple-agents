# 🔗 経歴 × 案件 双方向マッチングシステム

複数の経歴データ（人材）と複数の案件データ（プロジェクト）を双方向にマッチングするシステムです。

## 仕組み

スキルの共通度と経験年数に基づいてマッチングします。

```
スコア = |経歴のスキル ∩ 案件の必須スキル| / |案件の必須スキル|
```

- スコアが高いほどマッチ度が高い
- 経験年数が案件の最低要件を下回る場合はスコア 0（マッチしない）
- 経歴→案件、案件→経歴の両方向でランキング出力

## クイックスタート

### 1. 環境

```bash
pip install -r requirements.txt
```

### 2. CLI

```bash
# テーブル形式で表示
python -m src.cli --profiles data/profiles.json --projects data/projects.json

# JSON形式で出力
python -m src.cli --profiles data/profiles.json --projects data/projects.json --format json

# ファイルに保存
python -m src.cli --profiles data/profiles.json --projects data/projects.json --output result.json
```

### 3. Web UI

```bash
streamlit run src/ui.py
```

ブラウザで http://localhost:8501 を開きます。

- サンプルデータまたはJSONファイルのアップロード
- スコアフィルタ（スライダー）
- 経歴→案件 / 案件→経歴 のタブ切り替え
- 生データのテーブル表示

## データ形式

### 経歴 (Profile)

```json
{
  "id": "p1",
  "name": "田中太郎",
  "skills": ["Python", "AWS", "Docker"],
  "experience_years": 5
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| id | string | 一意のID |
| name | string | 氏名 |
| skills | string[] | 保有スキル一覧 |
| experience_years | int | 経験年数 |

### 案件 (Project)

```json
{
  "id": "prj1",
  "name": "クラウド移行案件",
  "required_skills": ["AWS", "Terraform", "Docker"],
  "min_experience_years": 3
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| id | string | 一意のID |
| name | string | 案件名 |
| required_skills | string[] | 必須スキル一覧 |
| min_experience_years | int | 最低経験年数 |

## テスト

```bash
python -m pytest tests/ -v
```

## プロジェクト構造

```
hijirii/
├── src/
│   ├── __init__.py       # パッケージ
│   ├── __main__.py       # python -m src エントリポイント
│   ├── models.py         # データモデル (Profile, Project, MatchResult)
│   ├── matcher.py        # マッチングエンジン
│   ├── cli.py            # CLI (argparse)
│   └── ui.py             # Web UI (Streamlit)
├── tests/
│   ├── conftest.py       # pytest設定
│   ├── test_matcher.py   # マッチングテスト (10件)
│   └── fixtures/
│       ├── profiles.json # テスト用経歴データ
│       └── projects.json # テスト用案件データ
├── data/                 # サンプルデータ
├── requirements.txt      # 依存パッケージ
└── README.md
```

## ライセンス

MIT
