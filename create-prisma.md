# Prismaコード自動生成スクリプト基本設計書

## 1. はじめに

本ドキュメントは、Markdown形式で記述されたデータベースのテーブル定義書を読み込み、Prismaスキーマファイルを自動生成するPythonスクリプトの基本設計である。これにより、手動でのPrismaスキーマ作成に伴うエラーを削減し、開発効率を向上させることを目的とする。

生成するコードはPython 3.xとし、Pandas, re, json, os, ioをインポートすること。

## 2. 入出力ファイル

### 2.1. 入力ファイル

* **テーブル一覧ファイル (`tables/tables.md`)**:

  * プロジェクト内の全テーブルの概要をまとめたMarkdownファイル。

  * 複数のセクション（例: `## ユーザー管理`, `## 予約管理`）に分かれ、それぞれがMarkdownテーブル形式でテーブル情報を保持する。

  * 期待されるカラム: `テーブル論理名`, `テーブル物理名`, `概要`, `テーブル作成順序`, `備考`。

* **個別テーブル定義ファイル (`tables/{テーブル物理名}.md`)**:

  * 各テーブルの詳細な定義を記述したMarkdownファイルである。
  * `tables`ディレクトリ配下に配置される。
  * 各ファイルは以下の4つのセクションで構成される。
    * `1.テーブル概要`
    * `2.カラム定義`
    * `3.インデックス定義`
    * `4.外部キー定義`

* **設定ファイル (`scripts/config.json`)**:
  * 型マッピング、バリデーションルール、期待されるカラム名などを定義したJSONファイルである。
  * スクリプトの動作を柔軟に調整するために使用される。

### 2.2. 出力ファイル

* **Prismaスキーマメインファイル (`base.prisma`)**:
  * 生成されたPrismaスキーマ定義を格納するファイルである。
  * メインプロジェクト直下の`sandbox/prisma`ディレクトリに生成する。
  * 下記のヘッダ情報及びDB基本定義に続き、作成したPrismaスキーマテーブルモデルファイルのimport定義を記載する。

```prisma
datasource db {
  provider = "mysql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

@import ./models/Table1.prisma
@import ./models/Table2.prisma
@import ./models/Table3.prisma
// 以下、作成したモデルファイルのファイル名をすべて記載
```

* **Prismaスキーマテーブルモデルファイル (`TableName.prisma`)**:
  * テーブルごとに作成した、Model定義を記述したファイルである。
  * ファイル名はモデル名と同じである。
  * メインプロジェクト直下の`sandbox/prisma/model`ディレクトリに生成する。

Prismaスキーマメインファイル及びモデルファイルは、apiサブモジュール配下に配置され、`npx prisma-import`でマージ及びインポートされる前提である。

* **ログファイル (`logs/conversion_errors.log`)**:
  * スクリプト実行中に発生したエラーやデバッグ情報を記録するファイルである。
  * `logs`ディレクトリに生成される。

## 3. 処理概要

本スクリプトは、以下の主要なステップで構成される。

1. **設定ファイルの読み込み**: `config.json`から型マッピングとバリデーションルールを読み込む。
2. **テーブル一覧ファイルの解析**: `tables.md`を読み込み、記載されている全テーブルの概要情報を抽出する。
3. **個別テーブル定義ファイルの解析とバリデーション**: `tables.md`で参照されている各テーブル定義ファイル（`.md`）を個別に読み込み、その内容を解析し、定義されたルールに基づいてバリデーションを行いる。
4. **Prismaスキーマの生成**: 解析・バリデーションされたテーブル定義データに基づいて、Prismaスキーマのモデル定義文字列を生成する。
5. **Prismaスキーマファイルの出力**: 生成されたPrismaスキーマのモデル定義文字列を、テーブルごとに**sandbox/prisma/model/**ディレクトリ内の.prismaファイルとして書き込む。全テーブルの@import定義を追記したヘッダ情報とDB基本定義を、**sandbox/prisma/base.prisma**ファイルとして書き込む。

## 4. 各処理の詳細

### 4.1. MarkdownテーブルのDataFrame変換 (`get_markdown_table_to_df`関数)

* **目的**: Markdown形式のテーブルをPandas DataFrameに変換する。

* **処理内容**:
  * 指定されたセクションタイトル（例: `## ユーザー管理`）に基づいて、Markdownコンテンツから該当するテーブル部分を抽出する。
  * 抽出したMarkdownテーブル文字列を`io.StringIO`と`pandas.read_csv(sep='|')`を使用してDataFrameに変換する。
  * `read_csv`によって生成される余分なセパレータ行（`|---|---|`）を削除する。
  * DataFrameのカラム名から先頭・末尾の空白文字をすべてトリムする。
  * `Unnamed:`で始まる完全に空（NaNのみ）のカラムを特定し、削除する。
  * DataFrame内のすべての文字列型データ（セル内の値）から先頭・末尾の空白文字をすべてトリムする。

### 4.2. テーブル一覧ファイルの構成チェック (main関数内の`tables.md`処理)

* **目的**: `tables.md`ファイルの構造と内容が、期待される形式に準拠しているかを確認する。

* **処理内容**:
  * `tables.md`内のすべての`##`セクションを抽出し、各セクション配下のMarkdownテーブルを`get_markdown_table_to_df`関数でDataFrameに変換する。
  * 各セクションから抽出されたDataFrameが、`config.json`の`tables_overview_columns`で定義された期待されるカラム（`テーブル論理名`, `テーブル物理名`, `概要`, `テーブル作成順序`, `備考`）をすべて含んでいるかを確認する。不足しているカラムがあればNaNで追加し、カラムの順序を期待されるものに再配置する。
  * 抽出された全テーブルのDataFrameを結合し、最終的なテーブル一覧DataFrameを作成する。
  * `テーブル物理名`カラム内のMarkdownリンク（例: `[users](./users.md)`）から、物理名（`users`）と相対ファイルパス（`./users.md`）を抽出する。
  * `テーブル作成順序`カラムの値が一意であることを確認する。

### 4.3. テーブル定義個別ファイルの構成チェック (`validate_and_parse_table`関数)

* **目的**: 個別のテーブル定義ファイル（例: `users.md`）の構造と内容が、詳細な定義ルールに準拠しているかを確認する。

* **処理内容**:
  * ファイル名が`1.テーブル概要`で定義された`テーブル物理名`と一致するかを確認する。
  * `tables.md`で読み込んだ概要情報と、個別ファイル内の`1.テーブル概要`の内容（論理名、物理名、概要）が一致するかを検証し、整合性を保つ。
  * 各セクション（`1.テーブル概要`, `2.カラム定義`, `3.インデックス定義`, `4.外部キー定義`）を`get_markdown_table_to_df`関数でDataFrameに変換する。
  * 各セクションのDataFrameが、`config.json`で定義されたそれぞれの期待されるカラムをすべて含んでいるかを確認する。不足しているカラムがあればNaNで追加し、カラムの順序を期待されるものに再配置する。
  * バリデーションは、個別の指示がない限りはエラーとして検出する。

  * **`2.カラム定義`のバリデーション**:
    * `カラム論理名`が空でないことを確認する。
    * `カラム論理名`が同一テーブル内で重複していないこと確認する。
    * `カラム物理名`が空でないことを確認する。
    * `カラム物理名`が同一テーブル内で重複していないことを確認する。
    * `カラム物理名`がMySQLの予約語でないことを確認する。
    * `config.json`の`type_rules`に基づいて、`型(桁,精度)`の値が正規表現に一致するかを検証する。
    * 型が`CHAR`もしくは`VARCHAR`の場合、続く`()`から桁数を取得する。(例: VARCHAR(255) → type: VARCHAR, length: 255)
    * 型が`DECIMAL`の場合、続く`()`から桁数と精度を取得する。(例: DECIMAL(10,2) → type: DECIMAL, length: 10, precision: 2)
      * 精度＞桁数となっている場合はエラーとする。
    * `config.json`の`column_rules`に基づいて、`PK`, `FK`, `UNIQUE`, `NOTNULL`などの値が正規表現に一致するかを検証する。
    * 論理名「`ID`」の項目が物理名「`id`」であること、`PK`の設定がされていること、`NOTNULL`の設定が`NN`であることを確認する。
    * `FK`が設定されている項目が、論理名「`参照先テーブル論理名ID`」物理名「`参照先テーブル物理名id`」であること、`NOTNULL`の設定が`NN`であることを確認する。違反した場合はワーニングとする(将来の拡張で例外的なFK名を許容した場合の考慮)。
    * `NOTNULL`が`NN`であるカラムの`DEFAULT`値が`NULL`でないことを確認する。
    * 必須監査カラム（`registered_at`, `registered_by`, `updated_at`, `updated_by`, `is_deleted`）の存在と、その型、NOTNULL、DEFAULT値が`config.json`の仕様と一致するかを検証する。

  * **`3.インデックス定義`のバリデーション**:
    * `インデックス物理名`が空でないことを確認する。
    * `インデックス物理名`が全テーブル間で重複していないことを確認する。
    * `config.json`の`index_rules`に基づいて、物理名の形式、`UNIQUE`、`インデックスタイプ`、`ソート順`、`備考`が正規表現に一致するかを検証する。
    * `カラム物理名`で指定されたカラムが、`2.カラム定義`に実際に存在するかを確認する。
    * `2.カラム定義`で`UKn`の設定をした項目と、`FK`の設定をした項目にインデックス定義が付与されていることを確認する。
    * `B-tree`インデックスはソート順が必要であり、`Hash`インデックスはソート順が不要であることを確認する。

  * **`4.外部キー定義`のバリデーション**:
    * `外部キー物理名`が空でないことを確認する。
    * `外部キー物理名`が全テーブル間で重複していないことを確認する。
    * `config.json`の`fk_rules`に基づいて、物理名の形式、`ON DELETE`、`ON UPDATE`が正規表現に一致するかを検証する。
    * `参照元カラム物理名`が`2.カラム定義`に存在し、かつ`FK`としてマークされていることを確認する。
    * `2.カラム定義`で`FK`としてマークされているすべてのカラムが、`4.外部キー定義`に記載されていることを確認する。

### 4.4. Prismaスキーマ生成 (`convert_to_prisma_model`関数)

* **目的**: 解析されたテーブル定義データからPrismaスキーマのモデル定義文字列を生成する。

* **処理内容**:
  * `config.json`の`type_mappings`を使用して、MySQLのデータ型をPrismaのデータ型にマッピングする。
  * モデル名はテーブル物理名をCamelCase形式に変換したものとし、`@@map`でテーブル物理名と紐づける。
  * モデル名に対して、テーブル論理名をPrismaコメントで付与する。
  * カラム名は、カラム物理名をcamelCaseに変換したものとし、`@map`でカラム物理名と紐づける。
  * 各カラムに対して、`@id`, `@unique`, `?` (Null許容), `@default`, `@updatedAt`,`@db.VarChar(X)`(文字列型の場合の桁数定義)などのPrismaアノテーションを適用する。また、カラム論理名をPrismaコメントで付与する。
  * `PK`が設定されている項目が複数ある場合、複合主キー（`@@id([])`）を定義する。
  * 複数の項目に対して同じ`UKn`が設定されている場合、その項目群に対して複合ユニーク制約（`@@unique([])`）を定義する。
  * インデックス(`@@index([])`)を定義する。但し、`@unique`あるいは`@@unique([])`と同じ項目並びのインデックスは定義しない。
  * 外部キー定義に基づいて、`@relation`アノテーションを持つリレーションフィールドを生成する。
    * `name`属性は、外部キーの物理名を設定する。
    * `fields`属性は、外部キー項目のフィールド名を設定する。
    * `references`属性は、外部キー参照先項目の物理名を設定する。
    * `onDelete`属性は、`ON DELETE`から取得した内容を設定する。
    * `onUpdate`属性は、`ON UPDATE`から取得した内容を設定する。
  * リレーションフィールド名は外部キーの物理名から「`fk_`」を除去し、camelCase形式に変換した文字列とする。リレーションフィールド名が重複した場合はエラーとする。(例: `fk_reservations_to_users` → `reservationsToUsers`)
  * 逆リレーションフィールド（例: `User`モデルに`Reservation[]`）を自動的に追加する。
    * `name`属性は、対応するリレーションフィールドの外部キーの物理名を設定する。
  * 逆リレーションフィールドのフィールド名は、対応するリレーションフィールドのフィールド名をCamelCaseに変換し、接頭辞`rev`を付加する。(例: `fk_reservations_to_users` → `revReservationsToUsers`)

## 5. エラーハンドリングとログ出力

* **エラーハンドリング**: スクリプトの各段階で発生するファイルI/Oエラー、JSONパースエラー、データバリデーションエラーなどを`try-except`ブロックで捕捉する。

* **ログ出力**:
  * `log_info`関数を使用して、処理の経過をコンソールと`logs/conversion_info.log`ファイルの両方に出力する。これにより、処理の経過の確認を支援する。
  * `log_error`関数を使用して、発生したエラーメッセージをコンソールと`logs/conversion_errors.log`ファイルの両方に出力する。これにより、問題の迅速な特定とデバッグを支援する。

## 付録

`config.json`の記載内容を以下に示す。スクリプトの冒頭で読み込み、スクリプト内の定数として使用すること。

```json
{
  "type_mappings": {
    "CHAR": "String",
    "VARCHAR": "String",
    "INT": "Int",
    "TIMESTAMP": "DateTime",
    "TINYINT": "Boolean",
    "DECIMAL": "Decimal"
  },
  "validation_rules": {
    "tables_overview_columns": {
      "TABLE_NAME": "テーブル論理名",
      "TABLE_PHYSICAL_NAME": "テーブル物理名",
      "SUMMARY": "概要",
      "TABLE_SORT": "テーブル作成順序",
      "REMARK": "備考"
    },
    "table_overview_sections": {
      "OVERVIEW": "1.テーブル概要",
      "COLUMN_DEFINITION": "2.カラム定義",
      "INDEX_DEFINITION": "3.インデックス定義",
      "FK_DEFINITION": "4.外部キー定義"
    },
    "table_overview_section_columns": {
      "ITEM": "項目",
      "CONTENT": "内容",
      "REMARK": "備考"
    },
    "table_overview_section_rows": {
      "TABLE_NAME": "テーブル論理名",
      "TABLE_PHYSICAL_NAME": "テーブル物理名",
      "SUMMARY": "テーブル概要",
      "SYSTEM": "テーブル系統"
    },
    "column_definition_columns": {
      "COLUMN_NAME": "カラム論理名",
      "COLUMN_PHYSICAL_NAME": "カラム物理名",
      "TYPE": "型(桁,精度)",
      "PK": "PK",
      "FK": "FK",
      "UNIQUE": "UNIQUE",
      "NOTNULL": "NOTNULL",
      "DEFAULT": "DEFAULT",
      "REMARK": "備考"
    },
    "index_definition_columns": {
      "INDEX_NAME": "インデックス物理名",
      "COLUMN_PHYSICAL_NAME": "カラム物理名",
      "UNIQUE": "UNIQUE",
      "TYPE": "インデックスタイプ",
      "SORT": "ソート順",
      "REMARK": "備考"
    },
    "foreign_key_definition_columns": {
      "FK_NAME": "外部キー物理名",
      "SOURCE_COLUMN": "参照元カラム物理名",
      "DEST_TABLE": "参照先テーブル物理名",
      "DEST_COLUMN": "参照先カラム物理名",
      "ON_DELETE": "ON DELETE",
      "ON_UPDATE": "ON UPDATE",
      "REMARK": "備考"
    },
    "column_rules": {
      "PK": "^(PK|-)$",
      "FK": "^(FK|-)$",
      "UNIQUE": "^UK\\d{1,2}$|^-$",
      "NOTNULL": "^(NN|-)$",
      "PK_PHYSICAL_NAME": "^id$|^.+_id$",
      "NK_PHYSICAL_NAME": "^.+_no$",
      "NA_MARK": "-"
    },
    "index_rules": {
      "INDEX_NAME": "^idx_",
      "UNIQUE": "^(YES|NO)$",
      "TYPE": "^(B-tree|Hash)$",
      "SORT": "^(ASC|DESC|-)$",
      "REMARK": "^(?!-).+$"
    },
    "fk_rules": {
      "FK_NAME": "^fk_",
      "ON_DELETE": "^(Cascade|Restrict|NoAction|SetNull|SetDefault)$",
      "ON_UPDATE": "^(Cascade|Restrict|NoAction|SetNull|SetDefault)$"
    },
    "type_rules":{
      "CHAR": "^(CHAR\\(\\d+\\))$",
      "VARCHAR": "^(VARCHAR\\(\\d+\\))$",
      "INT": "^(INT)$",
      "TIMESTAMP": "^(TIMESTAMP)$",
      "TINYINT": "^(TINYINT)$",
      "DECIMAL": "$(DECIMAL\\(\\d+,\\s*\\d+\\))$"
    },
    "audit_columns": [
      {
        "name": "registered_at",
        "type_regex": "^(TIMESTAMP)$",
        "notnull": "NN",
        "default": "CURRENT_TIMESTAMP"
      },
      {
        "name": "registered_by",
        "type_regex": "^(VARCHAR\\(36\\))$",
        "notnull": "NN",
        "default": "-"
      },
      {
        "name": "updated_at",
        "type_regex": "^(TIMESTAMP)$",
        "notnull": "-",
        "default": "NULL"
      },
      {
        "name": "updated_by",
        "type_regex": "^(VARCHAR\\(36\\))$",
        "notnull": "-",
        "default": "NULL"
      },
      {
        "name": "is_deleted",
        "type_regex": "^TINYINT$",
        "notnull": "NN",
        "default": "0"
      }
    ]
  }
}
```
