
# Prismaモデルコードを元にAPI設計書をレビューする

このプロンプトは、Prismaコードの内容に基づいてAPI設計書の内容をレビューするための手順書である。

下記のPrismaコードをもとに、下記のAPI設計書の内容をレビューし、レビュー記録票を出力せよ。

## 前提

- Prismaモデルコードは、DB設計書に忠実に作成されており、モデル名、カラム名にはPrismaコメントで適切に論理名が付与されている。
- 原則として、DB設計書を正とする。
- 配列の要素に対するチェック指示において、配列インデックスが省略されている場合、当該配列のすべての要素を対象とした指示であると解釈せよ。
- 確認観点に違反する項目は、「警告」「助言」の指定がない場合、すべて「エラー」として報告せよ。

## 入力

- **Prismaコード** 本システムで使用するDBスキーマのPrismaコードである。
- **API設計書** API一覧と、それに紐づくAPIごとの個別設計を下記の構造を持つJSONデータで表現したものある。レビューの対象物である。

```JSON
{
  "basePath": "{BASE_PATH}",
  "apiList": [
    {
      "no": "{API_NO}",
      "name": "{API_NAME_LINK_TEXT}",
      "path": "{API_FILE_PATH}",
      "endpoint": "{API_ENDPOINT}",
      "method": "{API_METHOD}",
      "category": "{API_SYSTEM_TYPE}",
      "authRequired": {AUTH_REQUIRED_BOOLEAN},
      "note": "{API_LIST_NOTE}"
    }
  ],
  "apis": [
    {
      "summary": {
        "name": "{API_NAME_TEXT}",
        "endpoint": "{API_ENDPOINT}",
        "method": "{API_METHOD}",
        "category": "{API_SYSTEM_TYPE}",
        "authRequired": {AUTH_REQUIRED_BOOLEAN},
        "dataType": "{API_DATA_TYPE}"
      },
      "requestHeader": [
        {
          "name": "{HEADER_NAME}",
          "required": {HEADER_REQUIRED_BOOLEAN},
          "sample": "{HEADER_SAMPLE_VALUE}",
          "note": "{HEADER_NOTE}"
        }
      ],
      "pathParameters": [
        {
          "description": "{論理名}",
          "name": "{物理名}",
          "type": "{型}",
          "required": {REQUIRED_BOOLEAN},
          "minLength": {MIN_LENGTH_NUMBER_OR_NULL},
          "maxLength": {MAX_LENGTH_NUMBER_OR_NULL},
          "format": "{フォーマット}",
          "min": {MIN_VALUE_NUMBER_DATE_OR_NULL},
          "max": {MAX_VALUE_NUMBER_DATE_OR_NULL},
          "note": "{備考}"
        }
      ],
      "urlParameters": [
        {
          "description": "{論理名}",
          "name": "{物理名}",
          "type": "{型}",
          "required": {REQUIRED_BOOLEAN},
          "minLength": {MIN_LENGTH_NUMBER_OR_NULL},
          "maxLength": {MAX_LENGTH_NUMBER_OR_NULL},
          "format": "{フォーマット}",
          "min": {MIN_VALUE_NUMBER_DATE_OR_NULL},
          "max": {MAX_VALUE_NUMBER_DATE_OR_NULL},
          "note": "{備考}"
        }
      ],
      "requestBody": [
        {
          "description": "{論理名}",
          "name": "{物理名}",
          "type": "{型}",
          "dbTable": "{DBテーブル}",
          "dbColumn": "{DBカラム}",
          "required": {REQUIRED_BOOLEAN},
          "minLength": {MIN_LENGTH_NUMBER_OR_NULL},
          "maxLength": {MAX_LENGTH_NUMBER_OR_NULL},
          "format": "{フォーマット}",
          "min": {MIN_VALUE_NUMBER_DATE_OR_NULL},
          "max": {MAX_VALUE_NUMBER_DATE_OR_NULL},
          "note": "{備考}",
          "children": []
        }
      ],
      "description": "{処理概要_TEXT}",
      "response": {
        "status": {RESPONSE_STATUS_NUMBER},
        "body": [
          {
            "description": "{論理名}",
            "name": "{物理名}",
            "type": "{型}",
            "dbTable": "{DBテーブル}",
            "dbColumn": "{DBカラム}",
            "note": "{備考}",
            "children": []
          }
        ]
      },
      "errors": [
        {
          "status": {ERROR_STATUS_NUMBER},
          "message": "{ERROR_MESSAGE_REQUIRED}",
          "detail": "{ERROR_MESSAGE_DETAIL_OR_EMPTY}",
          "description": "{ERROR_OCCURRENCE_CONDITION_OR_EMPTY}"
        }
      ]
    }
  ]
}
```

## レビュー手順

### 1. ファイル整合性チェック

#### ファイル整合性チェックの確認観点

- Prismaコード、API設計書がすべて入力されていること。

  - Prismaコードは、Prismaモデル形式に従って記述されており、すべてのモデル名、カラム名にPrismaコメントで論理名が付与されていること。
  - モデル物理名はPascalCase、カラム物理名はcamelCaseで記載されていること。
  - リレーションフィールド、逆リレーションフィールドは論理名不要である。

- API設計書が、バージョニングを示すキー名`basePath`の文字列、キー名`apiList`の配列、キー名`apis`の配列を持つJSONオブジェクトであること。

- `apiList`の要素は、下記の項目を持つJSONオブジェクトであること。
  - `no`
    - API一覧全体で一意であること。番号のトビは許容する。
  - `name`
  - `path`
  - `endpoint`
  - `method`
  - `category`
  - `authRequired`
  - `note`

- `apis`の要素は、下記の項目を持つJSONオブジェクトであること。
  - `summary`
  - `requestHeader`
  - `description`
  - `response`
  - `errors`

- `apis.summary.method`の内容に応じて、`apis.requestBody` `apis.pathParameters` `apis.urlParameters`が下記の通り定義されていること。
  - `apis.summary.method`が`POST`、`PUT`、`PATCH` の場合、`apis.requestBody`が必須で存在すること。`apis.pathParameters`または`apis.urlParameters`は任意とする。
  - `apis.summary.method`が`GET`、`DELETE` の場合、`apis.requestBody`は存在してはならない。かつ、`apis.pathParameters`と`apis.urlParameters`のうち、少なくとも一方が存在すること(どちらも定義されていない場合はエラー)。

- `apis.summary`に、`apiList[j]`の記載内容と一致する以下のキーが存在すること。但し、`apiList[j]`は、`apis.summary.endpoint === apiList[j].endpoint`を条件に取得した要素とする。
  - `name`
    - `apiList[j].name`と一致すること
  - `endpoint`
  - `method`
    - `apiList[j].method`と一致すること
  - `category`
    - `apiList[j].category`と一致すること
  - `authRequired`
    - `apiList[j].authRequired`と一致すること
  - `dataType`

- API定義書はあくまでエンドポイントの仕様を定義するため、`apis.description`は、100文字程度の簡潔な内容(あるいは機能設計書への移譲)であることが望ましい。`apis.description`に100文字程度を超える詳細な処理が記述されている場合(特に、トランザクション内部の詳細な処理について言及されている場合)は「助言」として指摘せよ。

ファイル整合性チェックで「エラー」となる指摘が発生した場合、以降のレビューを中止し、即座に結果を出力せよ。その際の後段のレビュー結果は「ファイル整合性チェックで指摘が発生したため、中止」と報告せよ。

但し、Prismaコードと`apiList`が「ファイル整合性チェック」の観点上問題なく入力されており、`apis`が未定義あるいは空配列の場合、API一覧のレビュー指示であると解釈せよ。

「ファイル整合性チェック」で「エラー」となる指摘が発生しなかった場合、後段のレビューはすべて実施し、発生した指摘はすべて報告せよ。

### 2. ルーティングと命名規則チェック

#### ルーティングとメソッドの適合性チェック

##### エンドポイント構造の検証

- `apiList.endpoint`が、基本構造(`/api/v1/{リソース名}/<アクション>`)に従っていること。

  - {リソース名}は対応するPrismaモデル物理名をkebab-case変換したものと一致していること。(例: UserServices → user-services)
  - {リソース名}がPrismaモデルに存在しない場合、人手チェックするため警告として指摘せよ。(例: auth、emailなど)

- `read`APIのメソッド検証:

  - `apiList.category === 'read'`である場合、日本のエンタプライズ系システムの慣習に合わせるため、`apiList.method === 'POST'`であること。`apiList.method === 'GET'`の場合、人手チェックとするため警告として指摘せよ。

- `create`/`update`/`delete`APIのメソッド検証:
  - `apiList.category === 'create'`の場合、`apiList.method === 'POST'`であること。
  - `apiList.category === 'update'`の場合、`apiList.method === 'PUT'`または`apiList.method === 'PATCH'`であること。
  - `apiList.category === 'delete'`の場合、`apiList.method === 'DELETE'`であること。

- 認証要否の検証:

  - `apiList.authRequired === false`と設定できるのは、以下のいずれかの**処理**に該当するAPIに限定すること。
    - **認証情報取得・設定処理**：
      - ログイン (`/api/v1/auth/signin`)
      - パスワードリセットや認証情報の初期化など、未認証状態で実行される認証関連アクション
    - **ユーザー登録処理 (サインアップ)**：
      - 新規登録 (`/api/v1/signup/register`)
  - **上記以外のAPI**で`apiList.authRequired === false`となっている場合、セキュリティ上の問題として**エラー**を指摘せよ。

##### 命名規則の整合性チェック

- API個別設計書内のリクエストおよびレスポンスの**すべてのJSONプロパティキー(物理名)**は、すべてcamelCase形式であること。

- **DB項目との物理名一致チェック:**
  - API個別設計書のリクエストおよびレスポンス内で、`dbTable`と`dbColumn`が具体的に指定されている**すべてのJSONプロパティキー**について、以下の確認を行う。
    1. **JSONプロパティキー名**が、対応するPrismaモデルの**カラム物理名**(`dbColumn`で指定されたPrismaフィールド論理名に対応するPrismaフィールド物理名)と**完全に一致していること**。
    2. **不一致の場合**、それはAPI側のキー名を変更していることを意味するため、人手チェックとするため**警告**として指摘せよ。
    3. ただし、以下の項目名は、DB項目と紐づいていても、**不一致を許容しチェック対象外**とする。
    - `{Model}Id`といった、リレーションフィールドと紐づいている可能性がある場合(助言として指摘せよ)
    - `offset`, `limit` (ページングパラメータ)
    - 監査項目: `registeredBy`, `registeredAt`, `updatedBy`, `updatedAt`, `isDeleted`

### 3. リクエストパラメータの詳細チェック

#### 禁止項目

- 認証トークンは`requestHeader`に含めるため、`requestBody` `pathParameters` `urlParameters`のいずれにも含めてはならない。

#### `pathParameters`のチェック

- `apis.pathParameters`が定義されている場合、そのすべての要素について、`required === true`であることを確認せよ。

#### ルートオブジェクト/子オブジェクトのセクションチェック

- JSON構造が適切に定義されていること。
- ルートオブジェクトに`array` `object`型の項目を含む場合、その`children`内の子オブジェクトの定義を必須とする。

#### 項目詳細チェック(ルートオブジェクト/子オブジェクト共通)

- **JSONプロパティの属性**(`logicalName`, `type`, `required`, `dbTable`, `dbColumn`, `minLength/maxLength`, `format`, `min/max`など)が適切に定義されていることを検証する。

- **型チェックの整合性:**

  - 登録系、更新系、削除系の場合かつDBの紐づき先がある場合、API個別設計書の`type`属性が、対応するPrismaカラムの型と一致していること。
    - **`string`** (Prisma: `String`, `DateTime`, `Json`など)
    - **`number`** (Prisma: `Int`, `Float`, `Decimal`)
    - **`boolean`** (Prisma: `Boolean`)
    - **`date`** (Prisma: `DateTime`だが、API側が`string`としている場合、セクション3の「取得系」の警告ルールを適用)

- DBテーブル/DBカラム
  - `dbTable !== null`の場合、`dbTable`の値がPrismaコードのテーブル論理名に存在すること。
  - `dbColumn !== null`の場合、`dbColumn`の値が当該`dbTable`のテーブルのカラム論理名に存在すること。
  - `dbTable === null`の場合、`dbColumn === null`であること。

- 必須
  - `required`が`true` `false`のどちらかであること。

- 桁数/値の検証:

  - `type === 'string'`の場合、`minLength`と`maxLength`が0以上の整数で定義されており、`minLength <= maxLength`以下であること。DBカラムに紐づく場合、**DBの桁数制約を超えていないこと。**
    - 要件上、APIで最大桁数・最小桁数を定義しないことを考慮し、`minLength` `maxLength` は`null`を許容する。その場合、`minLength`と`maxLength`大小関係のチェックは省略する。
    - `type !== 'string'` の場合、`minLength === null` かつ `maxLength === null`であること。
  - `type === 'number'`の場合、`min`と`max`が数値型で定義されており、`min <= max`であること。DBカラムに紐づく場合、**DBの値制約を超えていないこと。**
  - `type === 'date'`の場合、`min`と`max`が日付時刻と解釈可能な文字列で定義されており、`min <= max`であること。
  - `type === 'array'`の場合、`min`と`max`が0以上の整数で定義されており、`min <= max`であること。
    - 要件上、APIで最大・最小値を定義しないことを考慮し、`min` `max` は`null`を許容する。その場合、`min`と`max`大小関係のチェックは省略する。
    - `type === 'number'` `type === 'date'` `type === 'array'` のいずれでもない場合、`min === null` かつ `max === null`であること。
  - `format !=== null`の場合、`email`, `tel`, `fax`, `url`といった特定のフォーマットを示唆する項目名との整合性を**警告**として指摘せよ。

#### `category === 'read'`の場合の個別チェック

- リクエストに下記の監査項目を含めてはならない。

  - **登録者** `registeredBy`
  - **登録日時** `registeredAt`
  - **更新者** `updatedBy`
  - **更新日時** `updatedAt`
  - **削除フラグ** `isDeleted`

- あいまい検索の対象とするため、DBカラムの型が`number` `Date`の場合でもリクエスト側の項目を`string`型で定義することを許容する。但し、人手でチェックするため、警告として指摘せよ。

#### `category === 'create'`の場合の個別チェック

- リクエストボディ内に、**登録対象のテーブルの主キー**に紐づくJSONプロパティを含めてはならない。

- リクエストに下記の監査項目を含めてはならない。

  - **登録者** `registeredBy`
  - **登録日時** `registeredAt`
  - **更新者** `updatedBy`
  - **更新日時** `updatedAt`
  - **削除フラグ** `isDeleted`

- 親子関係の登録検証:

  - 親子関係を持つリソースを対象としている場合、親リソースのリクエストボディに、子リソース(`array`型もしくは`object`型)が、`dbTable/dbColumn`が`null`の項目として含まれていること。
  - 親リソースとなるオブジェクトがDBテーブルに紐づいている場合、親テーブルに紐づくPrismaのリレーションフィールドに子リソースとなるモデルが定義されていること。但し、要件上の都合であえて外部キーを定義していない場合を考慮し、人手チェックとするため警告として指摘せよ。

#### `category === 'update'`の場合の個別チェック

- ルートオブジェクト及び子オブジェクトのレコードに、**更新対象のテーブルの主キー**に紐づくJSONプロパティを必須とする。

- リクエストに下記の監査項目を含めてはならない。

  - **登録者** `registeredBy`
  - **登録日時** `registeredAt`
  - **更新者** `updatedBy`
  - **更新日時** `updatedBy`

- リクエストに「削除フラグ」`isDeleted`を含む場合、PATCHによる論理削除の可能性を考慮し、人手チェックとするため警告として指摘せよ。

- メソッドがPUTである場合、対応するPrismaモデルの、監査項目を除くすべてのフィールドが必須または任意として定義されていること。

#### `category === 'delete'`の場合の個別チェック

- `requestBody`は、**削除対象のテーブルの主キー**に紐づくJSONプロパティのみで構成されていること。

### 4. レスポンスとエラー定義チェック

#### `response.status`の検証

- **`category === 'read'`の場合:** `response.status === 200` であること。
- **`category === 'create'`の場合:** `response.status === 201` であること。
- **`category === 'update'`の場合:** `response.status === 204` であること。
- **`category === 'delete'`の場合:** `response.status === 204` であること。
- **`category`が上記以外の場合:** 人手チェックとするため「警告」として指摘せよ。

#### 項目詳細チェック

- `response.body`のルートオブジェクトおよび子オブジェクトについて、セクション3の「項目詳細チェック」と同様の検証ルールを適用すること。ルートオブジェクトに`array` `object`型の項目を含む場合、その`children`内の子オブジェクトの定義を必須とする。
- **`category === 'read'`の場合:** 取得したデータをレスポンスとしていること。
  - アクションが`list`の場合、ルートオブジェクトの`type`は対象とするリソースの`array`及び総件数(`totalCount`)であること。それ以外の項目を含む場合、人手チェックとするため警告として指摘せよ。
  - アクションが`detail`の場合、ルートオブジェクトの`type`は対象とするリソースの単一`object`であること。それ以外の項目を含む場合、人手チェックとするため警告として指摘せよ。
- **`category === 'create'`の場合:** ID(登録したレコードの主キー)のみをレスポンスとしていること。
- **`category === 'update'`の場合:** `[]`(空配列)であること。
- **`category === 'delete'`の場合:** `[]`(空配列)であること。
- **`category`が上記以外の場合:** 人手チェックとするため「警告」として指摘せよ。

#### エラー定義のチェック

- `errors`の要素に、下記の項目が定義されていること。
  - `status` HTTPエラーコードが数値型で設定されていること。
  - `message !== null`かつ、文字列として設定されていること。
  - `detail !== null`の場合、文字列として設定されていること。
  - `description !== null`かつ、文字列として設定されていること。

- `errors.status`は、下記のエラーコードに基づくエラーが必ず1件以上定義されていること。
  - 全API共通
    - `errors.status === 400`のエラー定義が存在すること。
    - `errors.status === 401`のエラー定義が存在すること。
    - `errors.status === 500`のエラー定義が存在すること。
  - **`category === 'read'`の場合:** `errors.status === 404`のエラー定義が存在すること。
  - **`category === 'create'`の場合:** `errors.status === 409`のエラー定義が存在すること。

## 出力形式

以上のレビューで抽出した指摘を、設計書ごとに下記のフォーマットで出力せよ。レビュー対象がAPI一覧に関する指摘の場合は、{API名} に「API一覧」、{API物理名} に「apis」を適用せよ。

受領側でスクリプト処理を行い、セパレーター(`------`)で分割して、そのままレビュー記録票として用いる。このため、セパレーター・ファイル名・指摘内容以外の内容を含めてはならない。「レビュワー確認事項」セクションはヒューマンチェック結果を記載する想定のため、セクション名と定型メッセージのみ出力せよ。

フォーマット内の下記のプレースホルダーは、下記のとおり実際の項目名に読み替えよ。

- **{API名}** レビュー対象としたAPI個別設計書のAPI名。API一覧の場合は「API一覧」。
- **{API物理名}** レビュー対象としたAPI個別設計書のAPIエンドポイント。API一覧の場合は「apis」。
- **{レビュー日時}** レビューを実施した日時を、日本時間の`YYYY/MM/DD HH:mm:SS`形式で表記する。
- **{NO}** 各セクションごとに纏めた指摘一覧の通し番号。セクションごとに 1 オリジンで採番せよ。
- **{指摘結果}** 下記のいずれかを表記する。
  - **-** ファイル整合性チェック違反のためレビューを中止した項目である場合。
  - **エラー** レビュー観点に明確に違反しており、修正が必須である場合。
  - **警告** レビュー観点で「警告として指摘せよ」としているチェック項目に違反している場合。
  - **OK** レビュー観点違反が検出されなかった場合。
  - **助言** レビュー観点違反は検出されなかったが、改善の余地がある場合。(例: 電話/電話番号 の表記ゆれ等)
- **{項目名}** 検査対象とした DB 項目の名称。
- **{指摘内容}** 検査対象とした項目への、短い文章による指摘。(例: 「指摘なし」「設定されていません」「項目に定義可能な型ではありません」「参照先のテーブルが定義されていません」など)
- **{自由記述}** 当該指摘項目に対する、文章による自由記述形式の備考。修正方針に対する助言等。
- **{レビュワー確認}** ヒューマンフィードバックのテンプレートとして、「指摘結果」に応じて下記のいずれかを表記する。
  - **エラー** 「修正してください」と表記する。
  - **警告** 「**■ 検討結果を記載してください ■**」と表記する。
  - **OK** 「-」と表記する。
  - **助言** 「**■ 検討結果を記載してください ■**」と表記する。

以下のセクションは、レビュー対象の設計書に合わせて出力を調整せよ。

- **### API一覧** API個別設計書のレビュー結果の場合、当該APIに関する内容のみ記載する。
- **### API個別設計書** API一覧のレビュー結果の場合、省略する。
- **## 2. API一覧チェック結果** API個別設計書のレビュー結果の場合、当該APIに関する内容のみ記載する。
- **## 3. API個別設計書チェック結果** API一覧のレビュー結果の場合、省略する。

```text
{API名}_review.md
------
# {API名}設計書レビュー記録票

- レビュー日時 {レビュー日時}

## 1. ファイル整合性チェック結果

### Prismaコード

| No   | 項目名   | 指摘結果   | 指摘内容   | 備考       | レビュワー確認   |
| ---- | -------- | ---------- | ---------- | ---------- | ---------------- |
| {NO} | {項目名} | {指摘結果} | {指摘内容} | {自由記述} | {レビュワー確認} |

### API一覧

| No   | 項目名   | 指摘結果   | 指摘内容   | 備考       | レビュワー確認   |
| ---- | -------- | ---------- | ---------- | ---------- | ---------------- |
| {NO} | {項目名} | {指摘結果} | {指摘内容} | {自由記述} | {レビュワー確認} |

### API個別設計書(JSON)

| No   | 項目名   | 指摘結果   | 指摘内容   | 備考       | レビュワー確認   |
| ---- | -------- | ---------- | ---------- | ---------- | ---------------- |
| {NO} | {項目名} | {指摘結果} | {指摘内容} | {自由記述} | {レビュワー確認} |

## 2. ルーティングと命名規則チェック結果

| No   | 項目名   | 指摘結果   | 指摘内容   | 備考       | レビュワー確認   |
| ---- | -------- | ---------- | ---------- | ---------- | ---------------- |
| {NO} | {項目名} | {指摘結果} | {指摘内容} | {自由記述} | {レビュワー確認} |

## 3. リクエストパラメータの詳細チェック結果

| No   | 項目名   | 指摘結果   | 指摘内容   | 備考       | レビュワー確認   |
| ---- | -------- | ---------- | ---------- | ---------- | ---------------- |
| {NO} | {項目名} | {指摘結果} | {指摘内容} | {自由記述} | {レビュワー確認} |

## 4. レスポンスとエラー定義チェック結果

| No   | 項目名   | 指摘結果   | 指摘内容   | 備考       | レビュワー確認   |
| ---- | -------- | ---------- | ---------- | ---------- | ---------------- |
| {NO} | {項目名} | {指摘結果} | {指摘内容} | {自由記述} | {レビュワー確認} |

## レビュワー確認事項

**必ず記入してレビュー記録票として提出してください。**
------
```

{PRISMA_CODE}

{API_JSON}
