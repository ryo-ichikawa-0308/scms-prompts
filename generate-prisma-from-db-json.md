# DB設計書をPrismaコードに変換する

本プロンプトは、JSON形式で記述されたデータベースのテーブル定義書を読み込み、Prismaスキーマファイルを自動生成する手順書である。手動でのPrismaスキーマ作成に伴うエラーを削減し、開発効率を向上させることを目的とする。

## 前提

- テーブル一覧及びテーブル個別定義書が「JSON入力構造」セクションのとおり正しく変換されており、データベース設計書として正しくレビューされている。
- テーブル物理名、カラム物理名はsnake_caseで記載されており、PascalCase、camelCaseへの読み替えが可能である。
- テーブル一覧に記載されているテーブルは、テーブル個別定義書が必ず存在する。存在しない場合、当該テーブルは設計未了とみなし、[WARN]としてログ出力せよ。
- テーブル一覧に記載されていないテーブルがテーブル個別定義書に記載されている場合、[ERROR]としてログ出力せよ。
- 配列の要素に対するチェック指示において、配列インデックスが省略されている場合、当該配列のすべての要素を対象とした指示であると解釈せよ。
- RDBMSはMySQLを前提とする。MySQL以外のRDBMSを前提とした表記が発見された場合、変換自体は実施し、[WARN]としてログ出力せよ。

## JSON入力構造

入力は、下記の構造を持つJSONデータである。

```JSON
{
    "tableList": {
        "{サブセクション名}": [
            {
              "no": "...",
              "logicalName": "...",
              "physicalName": "...",
              "path": "...",
              "description": "...",
              "dependencyLevel": "...", /* テーブル作成順序のキー */
              "note": "..."
            }
        ]
    },
    "tables": [
        {
          "summary": { /* テーブル概要のキー */
              "logicalName": "...",
              "physicalName": "...",
              "description": "...",
              "category": "..."
            },
            "columns": [ ... ],
            "indexes": [ ... ],
            "foreignKeys": [ ... ]
        }
    ]
}
```

## 出力

- **schema.prisma** DB設計書に基づいて作成したPrismaコード。本スクリプトの成果物である。
- **generate.log** 処理の進捗や状態を記録したログファイル。開発者はログファイルを分析し、変換過程の妥当性を評価する。

## Prismaコード生成手順

### 1. ドキュメント間整合性チェック

テーブル定義書、テーブル個別定義書を読み込み、下記の簡易チェックを行う。詳細な整合性確認はレビュー過程で行われている前提のため、変換に直接寄与する整合性のみ確認する。

#### テーブル一覧(tableList)のチェック

- `tableList`がJSON記法で記載されていること。
- `tableList`の要素が、業務コンテキストに基づいた1つ以上のサブセクションで構成されていること。
  - サブセクションが存在しない場合はエラーとしてログ出力し、生成処理を中止してログのみ出力せよ。
- 各サブセクションは、下記のキーを持つJSONオブジェクトであること。
  - `no`
  - `logicalName`
    - `tables.summary.logicalName`に存在しないテーブル名を記載している場合は警告としてログ出力せよ。
  - `physicalName`
    - `tableList`内で一意であること。
    - `tables.summary.physicalName`に存在しないテーブル名を記載している場合は警告としてログ出力せよ。
  - `description`
  - `dependencyLevel`
  - `note`

#### テーブル個別定義書(tables)のチェック

- 要素が1件以上存在する配列であること。
  - 要素が0件の場合はエラーとしてログ出力し、生成処理を中止してログのみ出力せよ。
- テーブル個別定義書がJSON記法で記載されていること。
- テーブル論理名がテーブル一覧に記載されていること。
- テーブル物理名がテーブル一覧に記載されていること。対応するテーブル論理名に正しく紐づいていること。
- テーブル個別定義書に下記のセクションが存在すること。
  - テーブル概要
  - カラム定義
  - インデックス定義
    - インデックス物理名がシステム全体で一意とみなせること。
  - 外部キー定義
    - 外部キー物理名がシステム全体で一意とみなせること。
    - 参照先テーブル及びカラムがテーブル個別定義書に存在すること。
      - テーブル個別定義書に存在しないテーブルを記載している場合は警告としてログ出力せよ。
      - テーブル個別定義書に存在するテーブルを記載しており、かつ存在しないカラムを参照している場合はエラーとしてログ出力せよ。

### 2. テーブル一覧(tableList)の読み込み

- `tableList`を読み込み、`tableList.{SUBSECTION_NAME}.logicalName`と`tableList.{SUBSECTION_NAME}.physicalName`を取得する。
- `physicalName`をPascalCaseに変換し、これをモデル物理名とする。(例: `user_services` → `UserServices`)
- `physicalName`そのものを、モデルの`@@map`属性として設定する。(例: `user_services` → `@@map("user_services")`)
- `logicalName`をPrismaコメントに変換し、これをPrismaモデルのモデルコメントにする。(例: `ユーザー` → `/// ユーザー`)

### 3. テーブル個別定義書(tables)の読み込み

#### 1. テーブル概要(tables.summary)読み飛ばし

`tables.summary`は、`tableList`と`tables`の整合性チェックにのみ利用し、変換に直接寄与しないセクションのため、読み飛ばす。

#### 2. カラム定義読み込み

`tables.columns`の各項目の設定値から、Prismaモデルのフィールド定義を設定する。

- `columns.logicalName`の設定値をPrismaコメントに変換し、Prismaカラムのカラムコメントにする。(例: ユーザー名 → /// ユーザー名)
- `columns.physicalName`の設定値をもとに、下記の通りPrismaモデルのフィールドを定義する。
  - `columns.physicalName`の設定値をcamelCaseに変換し、これをPrismaカラム物理名とする。(例: user_name → userName)
  - `columns.physicalName`の設定値そのものをカラムの`@map`属性として設定する。(例: user_name → @map("user_name"))
- `columns.typeAndSize` カラムの型、桁数、精度を示す。下記の変換表に従い、にPrisma型定義に変換する。

| 型              | Prisma Type  | 属性指定                                                                    | 備考                                                                                               |
| --------------- | ------------ | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `VARCHAR(N)`    | **String**   | `N`を桁数として抽出し、`@db.VarChar(N)`の属性指定を付加する。               |                                                                                                    |
| `CHAR(N)`       | **String**   | `N`を桁数として抽出し、`@db.Char(N)`の属性指定を付加する。                  |                                                                                                    |
| `MEDIUMTEXT`    | **String**   | `@db.MediumText`の属性指定を付加する。                                      | MySQLのMEDIUMTEXT明示。                                                                            |
| `TEXT`          | **String**   | `@db.Text`の属性指定を付加する。                                            | MySQLのTEXT明示。                                                                                  |
| `INTEGER`       | **Int**      | `@db.Intの`の属性指定を付加する。                                           | MySQLのINT明示。                                                                                   |
| `SMALLINT`      | **Int**      | `@db.SmallIntの`の属性指定を付加する。                                      | MySQLのSMALLINT明示。                                                                              |
| `MEDIUMINT`     | **Int**      | `@db.MediumInt`の属性指定を付加する。                                       | MySQLのMEDIUMINT明示。                                                                             |
| `TINYINT`       | **Int**      | `@db.TinyInt`の属性指定を付加する。                                         | 桁数指定がないTINYINTは数値として扱う。                                                            |
| `BIGINT`        | **BigInt**   | `@db.BigInt`の属性指定を付加する。                                          |                                                                                                    |
| `REAL`          | **Float**    | `@db.Float`の属性指定を付加する。                                           | MySQLのFLOAT明示。                                                                                 |
| `FLOAT(N)`      | **Float**    | `N`が25以上の場合は`@db.Double`、24以下の場合は`@db.Float`を付加する。      | MySQL前提のため、N=25を境にDOUBLEとして扱う。                                                      |
| `DECIMAL(P, S)` | **Decimal**  | `P`を桁数、`S`を精度として抽出し、`@db.Decimal(P, S)`の属性指定を付加する。 |                                                                                                    |
| `NUMERIC(P, S)` | **Decimal**  | `P`を桁数、`S`を精度として抽出し、`@db.Decimal(P, S)`の属性指定を付加する。 |                                                                                                    |
| `BOOLEAN`       | **Boolean**  | `@db.Boolean`の属性指定を付加する。                                         |                                                                                                    |
| `BOOL`          | **Boolean**  | `@db.Boolean`の属性指定を付加する。                                         |                                                                                                    |
| `TINYINT(1)`    | **Boolean**  | `@db.TinyInt`の属性指定を付加する。                                         | MySQLでの真偽値の慣習的なマッピング。                                                              |
| `BIT`           | **Boolean**  | `@db.Bit`の属性指定を付加する。                                             | SQL Server固有のため、設定されている場合は[WARN]としてログ出力せよ。                               |
| `DATE`          | **DateTime** | `@db.Date`の属性指定を付加する。                                            | MySQLのDATE明示。                                                                                  |
| `TIME`          | **DateTime** | `@db.Time`の属性指定を付加する。                                            | MySQLのTIME明示。                                                                                  |
| `TIMESTAMP(N)`  | **DateTime** | `@db.Timestamp(N)`の属性指定を付加する。                                    | 桁数指定がない場合、ミリ秒と解釈して桁数設定し、[ADVICE]としてログ出力せよ。                       |
| `DATETIME(N)`   | **DateTime** | `@db.DateTime(N)`の属性指定を付加する。                                     | 桁数指定がない場合、ミリ秒と解釈して桁数設定し、[ADVICE]としてログ出力せよ。                       |
| `JSON`          | **Json**     | `@db.Json`の属性指定を付加する。                                            |                                                                                                    |
| `JSONB`         | **Json**     | `@db.Json`の属性指定を付加する。                                            | PostgreSQL固有の型だが、MySQLのJSONにマッピングし、警告としてログ出力せよ。                        |
| `BYTEA`         | **Bytes**    | `@db.Binary`の属性指定を付加する。                                          | PostgreSQL固有のため、設定されている場合は警告としてログ出力せよ。                                 |
| `BLOB`          | **Bytes**    | `@db.Blob`の属性指定を付加する。                                            |                                                                                                    |
| `ENUM`          | **未対応**   | 該当カラムが検出された時点で処理を中止し、[ERROR]としてログ出力する。       | 未対応型。Enum定義は本プロンプトのスコープ外であり、対応するためには追加のドキュメント構造が必要。 |
| (不明な型)      | **String**   | [WARN]としてログ出力し、型をStringとして処理を続行する。                    | 変換表にない型が発見された場合のフォールバック処理を明確化。                                       |

**ENUM型検出時の処理** カラム定義から型がENUMと判断された場合、ログにエラーメッセージ「[ERROR]未対応の型(ENUM)が検出されました。」を出力し、生成処理を中止してログのみ出力せよ。

- `columns.isPrimaryKey === true`の場合、当該カラムにPRIMARY KEY制約を付与するため、以下のロジックでアトリビュートを設定する。
  - 同一テーブル内で複数のカラムに`columns.isPrimaryKey === true`が設定されている場合は(複合主キー)、すべてのPKに関する処理をここでスキップし、テーブルの最後に`@@id([{カラムリスト}])`アトリビュートとして集約して生成する。
  - 同一テーブル内で単一のカラムに`columns.isPrimaryKey === true`が設定されている場合は、当該カラムに`@id`アトリビュートを付与する。
- `columns.isForeignKey === true`の場合、当該カラムにFOREIGN KEY制約を付与する。後続の外部キー定義で詳細な設定を行う。
- `columns.unique`の配列に`UKn`が格納されている場合、当該カラムにUNIQUE制約を付与するため、以下のロジックでアトリビュートを設定する。
  - 前提: `n`はユニークキーを設定するカラムの組み合わせを識別するための通し番号。同一テーブル内で、ユニークキーを設定するカラム群ごとに一意な番号である。
  - 同一テーブル内で`UKn`が単一のカラムに対して設定されている場合、当該カラムに`@unique`アトリビュートを付与する。
  - 同一テーブル内で`UKn`が複数のカラムに跨って設定されている場合、後続のインデックス定義読み込み(複合ユニークキー)で処理するため、ここでは読み飛ばす。
- `columns.isNotNull`の設定に応じて当該カラムにNOT NULL制約を付与するため、以下のロジックでアトリビュートを設定する。
  - `columns.isNotNull === true`の場合、Prisma型定義の後に`?`(Optionality)を付与しない。
  - `columns.isNotNull === false`の場合は、`?`を付与する。
- `columns.defaultValue === ""`以外の場合、当該カラムのDEFAULT値を付与するため、以下のロジックで`@default({値})`アトリビュートを設定する。
  - 当該テーブルが単一の`PK`項目を持つ場合、下記のロジックでサロゲートキーのデフォルト値を設定する。
    - `columns.typeAndSize === "VARCHAR(36)"`かつ`columns.defaultValue === "UUID"`の場合、`@default(uuid())`アトリビュートを付与する。
    - `columns.typeAndSize === "INTEGER"`かつ`columns.defaultValue === "AUTO_INCREMENT"`または`columns.defaultValue === ""`の場合、`@default(autoincrement())`アトリビュートを付与する。
  - `columns.typeAndSize === "DATETIME"`であり、かつ`columns.defaultValue === "CURRENT_TIMESTAMP"`または`columns.defaultValue === "NOW()"`の場合は、`@default(now())`アトリビュートを付与する。
    - 但し、監査項目「更新日時(`update_at`/`updateAt`)」は、`@default({値})`の代わりに`@updatedAt`アトリビュートを付与する。
  - 真偽値項目は、`columns.defaultValue`の設定に合わせて`@default(true)`もしくは`@default(false)`アトリビュートを付与する。
    - 監査項目「削除フラグ(`is_deleted`/`isDeleted`)」は、`@default(false)`アトリビュートを付与する。
  - `columns.isNotNull === false`かつ`columns.defaultValue === null`の場合は、`@default({値})`アトリビュートを設定してはならない。

- `columns.note`は変換に直接寄与しない項目のため、読み飛ばす。

#### 3. インデックス定義読み込み

テーブル個別定義書の「インデックス定義」セクションから、下記の情報を読み込み、Prismaモデルの`@@index`または`@@unique`アトリビュートを生成する。

- **インデックス物理名** `name:`オプションの設定内容として取得する。
- **カラム物理名** インデックスを設定するカラムリストとして取得し、camelCaseに変換する。
  - **PK/UKとの重複排除:** カラム定義セクションで`PK`として指定されている単一カラム、または`UKn`が設定されている単一カラムと、インデックスのカラムリストが完全に一致する場合、そのインデックス定義はRDBMSで自動作成されるとみなし、`@@index`の生成をスキップする。その際、ログに「冗長なインデックス定義(自動作成される単一PK/UK)をスキップしました」と警告を記録する。
- **UNIQUE** `YES`が設定されている場合は、`@@unique([{カラムリスト}])`アトリビュートとして生成する。それ以外の場合は、`@@index([{カラムリスト}])`アトリビュートとして生成する。
- **インデックスタイプ** 作成するインデックスの種類を取得する。
  - `B-Tree`の場合はB-Treeインデックスとして作成する。
  - `Hash`の場合は、Prismaの標準機能としてサポートされていないため、`@@index`として処理しつつ、ログに「HashインデックスはPrismaでネイティブサポートされないため、標準インデックスとして処理します」と警告を記録する。
- **ソート順** `B-Tree`インデックスのソート順を取得する。カラムリストの並び順に対応して、`(sort: Asc)` `(sort: Desc)`の設定を行う。ソート順が`-`の場合はオプションを省略する。
- **備考** 変換に直接寄与しない項目のため、読み飛ばす。

##### 特殊対応と警告

- **複合主キーとの重複排除:** 複合主キーとして`@@id`が生成された場合、その複合キーと完全に一致する`@@index`定義は冗長とみなし、生成をスキップする。
- **MySQL特有のtype:** `Fulltext`や`length`などの設定は、本プロンプトの対象外である。備考欄等で記載がある場合、ログに警告を出力して標準の`@@index`として処理を続行する。
- **ドキュメントの整合性警告(処理完了後):** インデックス定義の読み込みが完了した後、以下のチェックを行い、対応する`@@unique`または`@@index`が生成されていない場合は、[WARN]としてログ出力する。
  - **複合UNIQUEキー:** カラム定義で複合`UKn`が設定されているカラムの組み合わせ。
  - **外部キー:**：`columns.isForeignKey === true`設定カラム(単独または複合インデックスの一部)。

#### 4. 外部キー定義読み込み(foreignKeys)

テーブル個別定義書の`foreignKeys`配列の各要素に基づき、Prismaモデルのリレーションフィールド及び逆リレーションフィールドを生成する。

- **foreignKeys.foreignKeyPhysicalName**
  - 設定値そのものを、`@relation`アトリビュートのリレーション名として取得する。
  - 外部キー名から接頭辞`fk_`を除去し、camelCaseに変換した文字列をリレーションフィールドのフィールド名として用いる。(例: `fk_users_orders` → `usersOrders`)
  - リレーションフィールド名をPascalCaseに変換し、接頭辞`rev`を付加した文字列を逆リレーションフィールドのフィールド名として用いる。(例: `usersOrders` → `revUsersOrders`)
- **foreignKeys.sourceColumnPhysicalName** 設定値をcamelCaseに変換し、`fields: [{値}]`属性の設定値として取得する。
- **foreignKeys.targetTablePhysicalName** テーブル物理名をPascalCaseに変換し、リレーションフィールドの型とする。
- **foreignKeys.targetTablePhysicalName** 設定値をcamelCaseに変換し、`references[{値}]`属性の設定値として取得する。
- **foreignKeys.onDelete** `onDelete`オプションの設定値として取得する。設定がない場合はデフォルト値`Restrict`を設定し、[WARN]としてログ出力する。
- **foreignKeys.onUpdate** `onUpdate`オプションの設定値として取得する。設定がない場合はデフォルト値`Restrict`を設定し、[WARN]としてログ出力する。
- **foreignKeys.note** 変換に直接寄与しない項目のため、読み飛ばす。

##### リレーションフィールドの追加ロジック(参照元モデルへ)

**リレーションフィールド**の定義文字列は、以下の構造で生成し、参照元テーブルに対応するPrismaモデルに追加する。

- **フィールド名**: `foreignKeys.foreignKeyPhysicalName`から生成したcamelCaseの文字列(例: `fk_users_orders` → `usersOrders`)
- **型**: `foreignKeys.targetTablePhysicalName`から生成したPascalCaseの文字列(例: `Users`)
- **アノテーション**: `@@relation` アノテーションを付加し、以下の属性を設定する。
  - **リレーション名**: `foreignKeys.foreignKeyPhysicalName`をそのまま利用する(例: `"fk_users_orders"`)
  - **`fields`**: `foreignKeys.sourceColumnPhysicalName`から生成した設定値を設定する。
  - **`references`**: `foreignKeys.targetTablePhysicalName`から生成した設定値を設定する。
  - **`onDelete`**: `foreignKeys.onDelete`の設定値またはデフォルト値(`Restrict`)を設定する。
  - **`onUpdate`**: `foreignKeys.onUpdate`の設定値またはデフォルト値(`Restrict`)を設定する。
- **生成例**: `usersOrders Users @relation("fk_users_orders", fields: [usersId], references: [id], onDelete: Cascade, onUpdate: Restrict)`

##### 逆リレーションフィールドの追加ロジック(参照先モデルへ)

**逆リレーションフィールド**の定義文字列は、以下の構造で生成し、参照先テーブルに対応するPrismaモデルに追加する。

- **フィールド名**: `foreignKeys.foreignKeyPhysicalName`から生成した`rev`接頭辞付きのPascalCase文字列とする。(例: `fk_users_orders` → `revUsersOrders`)
- **型**: 参照元テーブルのPrismaモデル名(処理対象のテーブル名)の後に**配列を示す `[]`** を付加する。(例: `Orders[]`)
- **アノテーション**: `@@relation` アノテーションを付加し、以下の属性を設定する。
  - **リレーション名**: リレーションフィールドと一致させるため、`foreignKeys.foreignKeyPhysicalName`をそのまま利用する。(例: `fk_users_orders`)
  - **`fields`および`references`属性は設定しない**(多対一のリレーションの多側を示すため)。
- **生成例**: `revUsersOrders Orders[] @relation("fk_users_orders")`

### 4. Prismaコードの作成

最終的な`schema.prisma`ファイルを構成する。

#### 1. ヘッダー情報の挿入

以下のdatasourceとgeneratorブロックをファイル先頭に挿入する。

```prisma
// Prisma code of simple-contract-management-system
// !!! DO NOT EDIT MANUALLY !!!
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "mysql"
  url      = env("DATABASE_URL")
}
```

#### 2. モデル定義の挿入

手順2および手順3で読み込んだ各テーブルのモデル定義を、`model {モデル物理名} { ... }`の形式で挿入する。この際、手順2で生成したPrismaコメントをモデル定義の直前に挿入する。

#### 3. ロギングの完了

`generate.log`ファイルに「Prismaスキーマの生成が完了しました。」という成功メッセージと、処理中に発生した警告・エラーメッセージをすべて追記し、処理を終了する。

## 出力形式

出力内容は、下記のフォーマットで返却せよ。受領側でスクリプト処理を行い、セパレーター(`------`)で分割して、そのまま計算機で処理するためのインプットとして用いる。このため、セパレーター・ファイル名・JSON・ログ以外の内容を含めてはならない。

また、ログは指摘のレベルに応じて、行頭に[ERROR]あるいは[WARN]のプレフィックスを付与せよ。

```text
------
generate.log
------
// ログの出力内容
------
schema.prisma
------
// Prismaコードの出力内容
------
```

{DB_JSON}
