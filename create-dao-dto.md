# PrismaモデルコードをもとにDTOクラスとDAOクラスの基本メソッドを実装したコードを出力する

このプロンプトは、Prismaコードの内容に基づいてDTO、DAO及び全てのDAOを統括するModuleを出力するための指示書である。

下記のPrismaモデルをもとに、下記に示すDTOクラス及びDAOクラスのコードそのテストコードを出力せよ。PrismaモデルはDB定義書に忠実に作成されてる前提で扱え。

いずれも、NestJSのクリーンアーキテクチャに基づいてデータアクセスを行うDAO層の部品として用いる前提である。

複数のPrismaモデルが与えられた場合、与えられたモデルすべてに対して同様の解析を行い、コードを出力せよ。

## テーブル名等の読み替え方法

設計書内の以下の文言は、Prismaクラスのモデル名を読み替えたものである。

- **TableName** Prismaクラスのモデル名にそのまま読み替える。(例: `UserServices` → `UserServices`)
- **tableName** Prismaクラスのモデル名をcamelCaseに変換したものに読み替える。(例: `UserServices` → `userServices`)
- **table_name** Prismaクラスのモデル名をsnake_caseに変換したものに読み替える。(例: `UserServices` → `user_services`)

## DTOコード設計

### DTOファイル名

`table_name.dto.ts`とする。

### DTO実装内容

Prismaコードに基づいて、下記の2つのクラスを定義する。

1. 検索用DTO

- クラス名をSelectTableNameDtoとする。
- 監査フィールド(登録日時、登録者、更新日時、更新者、削除フラグ)以外の項目をフィールドとして持つ。
- すべての項目を任意項目とする。
- Prismaのフィールドが数値型の場合はDTOの項目は数値型とする。型や精度(整数型、浮動小数点型、10進数型等)はPrismaフィールドの定義に準ずる。
- Prismaのフィールドが日付時刻型の場合はDTOの項目は日付時刻型とする。
- PrismaのフィールドがBool型の場合はDTOの項目はBool型とする。
- Prismaのフィールドが文字列型の場合はDTOの項目はString型とする。
- あいまい検索対応のため、型チェックの`class-validator`アノテーションのみを付加する。

1. 登録用DTO

- クラス名をCreateTableNameDtoとする。
- すべての項目をフィールドとして持つ。
- 項目の必須設定はPrismaモデルの定義に準ずる。但し、ID(PK)はDBでの発番・ロジックからの発番両方に対応するため、任意項目とする。
- 項目の型はPrismaモデルの定義に準ずる。
- 項目の型、桁数定義をチェックする`class-validator`アノテーションを付与する。

## DTOテストコード設計

### DTOテストコードファイル名

`table_name.dto.spec.ts`とする。

### DTOテストコード実装内容

DTOクラスそれぞれのバリデーション確認を行う。テストメソッドの構成は下記のとおりとする。

```TypeScript
describe('TableNameDtoのテスト', () => {
    describe('SelectTableNameDtoのテスト', () => {
        describe('正常系', () => {
            test('必須項目すべてに入力がある場合', () => {
                // テストコードを実装
            });
            test('任意項目のみに入力がある場合', () => {
                // テストコードを実装
            });
        });
        describe('異常系', () => {
            test('必須項目が未入力の場合', () => {
                // テストコードを実装
            });
            test('型違反の入力がある場合', () => {
                // テストコードを実装
            });
        });
    });
    describe('CreateTableNameDtoのテスト', () => {
        describe('正常系', () => {
            test('必須項目すべてに入力がある場合', () => {
                // テストコードを実装
            });
            test('任意項目のみに入力がある場合', () => {
                // テストコードを実装
            });
        });
        describe('異常系', () => {
            test('必須項目が未入力の場合', () => {
                // テストコードを実装
            });
            test('型違反の入力がある場合', () => {
                // テストコードを実装
            });
        });
    });
});
```

## DAOコード設計

### DAOコードファイル名

`table_name.dao.ts`とする。

### DAO実装内容

- クラス名をTableNameDaoとする。
- NestJSの依存性注入により、Prismaアクセスを抽象化したクラスPrismaServiceと、PrismaServiceからトランザクション管理に関係のないメソッド($connect, $disconnectなど)を省いたPrismaTransaction型のクラスを持つ。

下記のメソッドを実装すること。

#### 選択メソッド

```TypeScript
/**
 * TableNameを取得する
 * @param dto TableNameの検索用DTO
 * @returns 取得したテーブルの配列
 */
selectTableName(dto: SelectTableNameDto): Promise<TableName[]>{}
```

selectTableNameは、検索結果が0件の場合は空の配列を返す。0件の場合の処理(後続ロジック実行、NotFoundException)は呼び出し元で行うため、DAOは感知しない。

selectTableNameは、下記のPrisma例外を処理する。

- **接続エラーなど、予期せぬ例外** InternalServerErrorExceptionにラップして例外送出する。

#### 登録メソッド

```TypeScript
/**
 * TableNameを新規登録する
 * @param dto TableNameの登録用DTO
 * @returns 登録したレコード
 */
createTableName(prismaTx: PrismaTransaction, dto: CreateTableNameDto): Promise<TableName>{}
```

createTableNameは、下記のPrisma例外を処理する。

- **一意制約違反** ConflictExceptionにラップして例外送出する。
- **外部キー違反** BadRequestExceptionにラップして例外送出する。
- **接続エラーなど、予期せぬ例外** InternalServerErrorExceptionにラップして例外送出する。

#### 更新メソッド

```TypeScript
/**
 * TableNameを更新する
 * @param prismaTx トランザクション
 * @param dto TableNameのPrisma型
 * @returns 更新したレコード
 */
updateTableName(prismaTx: PrismaTransaction, updateData: TableName): Promise<TableName>{}
```

updateTableNameは、下記のPrisma例外を処理する。

- **一意制約違反** ConflictExceptionにラップして例外送出する。
- **外部キー違反** BadRequestExceptionにラップして例外送出する。
- **更新対象のレコードが見つからない** NotFoundExceptionにラップして例外送出する。
- **接続エラーなど、予期せぬ例外** InternalServerErrorExceptionにラップして例外送出する。

## DAOテストコード設計

### DAOテストコードファイル名

`table_name.dao.spec.ts`とする。

### DAOテストコード実装内容

DAOクラスの各メソッドの正常系・異常系確認を行う。テストメソッドの構成は下記のとおりとする。

```TypeScript
describe('TableNameDaoのテスト', () => {
    describe('selectTableNameのテスト', () => {
        describe('正常系', () => {
            test('1件の結果が返る場合', () => {
                // テストコードを実装
            });
            test('複数件の結果が返る場合', () => {
                // テストコードを実装
            });
            test('0件の結果が返る場合', () => {
                // テストコードを実装
            });
        });
        describe('異常系', () => {
            test('DB接続エラーが発生した場合', () => {
                // テストコードを実装
            });
        });
    });
    describe('createTableNameのテスト', () => {
        describe('正常系', () => {
            test('正常に登録ができる場合', () => {
                // テストコードを実装
            });
        });
        describe('異常系', () => {
            test('一意制約違反が発生した場合', () => {
                // テストコードを実装
            });
            test('外部キー違反が発生した場合', () => {
                // テストコードを実装
            });
            test('DB接続エラーが発生した場合', () => {
                // テストコードを実装
            });
        });
    });
    describe('updateTableNameのテスト', () => {
        describe('正常系', () => {
            test('正常に更新ができる場合', () => {
                // テストコードを実装
            });
        });
        describe('異常系', () => {
            test('一意制約違反が発生した場合', () => {
                // テストコードを実装
            });
            test('外部キー違反が発生した場合', () => {
                // テストコードを実装
            });
            test('更新レコードが見つからない場合', () => {
                // テストコードを実装
            });
            test('DB接続エラーが発生した場合', () => {
                // テストコードを実装
            });
        });
    });
});
```

## Moduleコード設計

- Moduleコードは、作成したすべてのDAOコードを依存性注入可能な部品としてサービス層に提供する。
- クラス名は`DataBaseModule`固定とする。

### Moduleコードファイル名

`database.module.ts`とする。

### Moduleコードの実装内容

```TypeScript
@Module({
  imports: [PrismaModule], 
  providers: [
    TableNameDao,
    // 作成したすべてのDaoを記載する
  ],
  exports: [
    TableNameDao,
    // 作成したすべてのDaoを記載する
  ],
})
export class DataBaseModule {}
```

### Moduleテストコード設計

### Moduleテストコードファイル名

`database.module.spec.ts`とする。

### Moduleテストコードの実装内容

```TypeScript
describe('DataBaseModuleのテスト', () => {
    describe('正常系', () => {
        test('モジュールが正常にコンパイルできる場合', () => {
            // テストコードを実装
        });
    });
});
```

## ファイルパス

各ファイルは、以下のパスに配置される前提とせよ。

### PrismaServiceのパス

- `/src/prisma/prisma.service.ts`

### PrismaTransactionのパス

- `/src/prisma/prisma.type.ts`

### DAOコード及びDAOテストコードのパス

- `/src/database/dao/table_name.dao.ts`
- `/src/database/dao/table_name.dao.spec.ts`

### DTOコード及びDTOテストコードのパス

- `/src/database/dto/table_name.dto.ts`
- `/src/database/dto/table_name.dto.spec.ts`

### Moduleコード及びModuleテストコードのパス

- `/src/database/dto/database.module.ts`
- `/src/database/dto/database.module.spec.ts`

## 出力方式

作成したコードは、下記のフォーマットで返却せよ。受領側でスクリプト処理を行い、セパレーター(`------`)で分割して、そのまま実装コードとして出力する想定である。このため、セパレーター・ファイル名・実装内容以外の内容を含めてはならない。

```text
------
database.module.ts
------
// database.module.tsの実装内容
------
database.module.spec.ts
------
// database.module.spec.tsの実装内容
------
table_name.dto.ts
------
// table_name.dto.tsの実装内容
------
table_name.dto.spec.ts
------
// table_name.dto.spec.tsの実装内容
------
table_name.dao.ts
------
// table_name.dao.tsの実装内容
------
table_name.dao.spec.ts
------
// table_name.dao.spec.tsの実装内容
------
```

## Prismaコード

(PrismaCodeHere)
