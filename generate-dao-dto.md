# PrismaモデルコードをもとにDTOクラスとDAOクラスの基本メソッドを実装したコードを出力する

このプロンプトは、Prismaコードの内容に基づいてDTO、DAO及び全てのDAOを統括するModuleを出力するための指示書である。

下記のPrismaモデルをもとに、下記に示すDTOクラス及びDAOクラスのコード、Moduleコード、それらのテストコードを出力せよ。PrismaモデルはDB定義書に忠実に作成されてる前提で扱え。

いずれも、NestJSのクリーンアーキテクチャに基づいてデータアクセスを行うDAO層の部品として用いる前提である。

複数のPrismaモデルが与えられた場合、与えられたモデルすべてに対して同様の解析を行い、コードを出力せよ。

## テーブル名等の読み替え方法

設計書内の以下の文言は、Prismaクラスのモデル名、フィールド名、その他付随情報を読み替えたものである。

- **TableName** Prismaクラスのモデル名にそのまま読み替える。(例: `UserServices` → `UserServices`)
- **tableName** Prismaクラスのモデル名をcamelCaseに変換したものに読み替える。(例: `UserServices` → `userServices`)
- **table_name** Prismaクラスのモデル名をsnake_caseに変換したものに読み替える。(例: `UserServices` → `user_services`)
- **[モデル名]** Prismaクラスのモデルにコメントとして付与されている論理名に読み替える。(例: `/// ユーザーサービス` → `ユーザーサービス`)
  - 該当するモデルコメントが見つからない場合、Prismaクラスのモデル名にそのまま読み替える。
- **[フィールド名]** Prismaクラスのフィールドにコメントとして付与されている論理名に読み替える。(例: `/// ユーザー名` → `ユーザー名`)
  - 該当するフィールドコメントが見つからない場合、Prismaクラスのフィールド名にそのまま読み替える。
- **[型名]** `文字列` `数値` `日付` `真偽値` といった、一般的なデータ型の日本語表現に読み替える。
- **[形式名]** `メールアドレス` `電話番号` `URL`といった、`class-validator`がサポートしている文字列フォーマットの日本語表現に読み替える。

## DTOコード設計

### DTOファイル名

`table_name.dto.ts`とする。

### DTO実装内容

Prismaコードに基づいて、下記の2つのクラスを定義する。

1. 検索用DTO

- クラス名をSelectTableNameDtoとする。
- クラスコメントとして`[モデル名]の標準検索用DTO`を付与する。
- 監査フィールド(登録日時、登録者、更新日時、更新者、削除フラグ)以外の項目をフィールドとして持つ。
- フィールドコメントとして、`[フィールド名]`を付与する。
- すべての項目を任意項目とする。
- Prismaのフィールドが数値型の場合はDTOの項目は数値型とする。型や精度(整数型、浮動小数点型、10進数型等)はPrismaフィールドの定義に準ずる。
- Prismaのフィールドが日付時刻型の場合はDTOの項目は日付時刻型とする。
- PrismaのフィールドがBool型の場合はDTOの項目はBool型とする。
- Prismaのフィールドが文字列型の場合はDTOの項目はString型とする。
- Prismaのフィールドが上記以外の型の場合はString型とし、`TODO:`コメントで注釈することで実装者に知らせよ。
- あいまい検索対応のため、型チェックの`class-validator`アノテーションのみを付加する。
- `class-validator`のエラーメッセージは、下記のとおりとせよ。
  - **型チェック違反** `[フィールド名]は[型名]で入力してください。`

1. 登録用DTO

- クラス名をCreateTableNameDtoとする。
- クラスコメントとして`[モデル名]の登録用DTO`を付与する。
- すべての項目をフィールドとして持つ。
- フィールドコメントとして、`[フィールド名]`を付与する。
- 項目の必須設定はPrismaモデルの定義に準ずる。但し、ID(PK)はDBでの発番・ロジックからの発番両方に対応するため、任意項目とする。
- 項目の型はPrismaモデルの定義に準ずる。
- 項目の型、桁数定義をチェックする`class-validator`アノテーションを付与する。
- `class-validator`のエラーメッセージは、下記のとおりとせよ。
  - **必須チェック違反** `[フィールド名]は必ず入力してください。`
  - **型チェック違反** `[フィールド名]は[型名]で入力してください。`
  - **最大桁数違反** `[フィールド名]はXX桁以下で入力してください。` `XX`はPrismaモデルの制約で示されている桁数。
  - **最大値チェック違反** `[フィールド名]はXX以下で入力してください。` `XX`はPrismaモデルの制約で示されている最大値。
  - **最小値チェック違反** `[フィールド名]はXX以上で入力してください。` `XX`はPrismaモデルの制約で示されている最小値。
  - **範囲指定違反** `[フィールド名]はXX以上YY以下で入力してください。` `XX`はPrismaモデルの制約で示されている最小値。`YY`はPrismaモデルの制約で示されている最大値。最大値と最小値の両方が指定されている場合に適用する。
  - **フォーマット違反** `[フィールド名]は[形式名]で入力してください。` `email` `phone` `fax` `url` など、`class-validator` がサポートしている文字列フォーマットを示唆するフィールド名である場合に適用する。但し、最終的に人手確認とするため、`TODO:`コメントで注釈することで実装者に知らせよ。

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

selectTableNameは、検索結果が0件の場合は空の配列を返す。0件の場合の処理(後続ロジック実行、NotFoundException)は呼び出し元のサービスクラスで行うため、DAOは感知しない。

selectTableNameは、検索条件として、「論理削除されていないこと」(`isDeleted: false`)を必須とする。

selectTableNameの要件に当てはまらない検索(他テーブルとの結合、論理削除されているレコードの抽出)は手動で作成するため、本プロンプトの対象外とする。

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

createTableNameは、データの登録そのものを担当し、登録における業務的な整合性は呼び出し元のサービスクラスが保証するため、DAOは感知しない。

createTableNameにおいて、監査フィールドの正当性は呼び出し元のサービスクラスが保証するため、DAOは感知しない。

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

updateTableNameは、データの更新そのものを担当し、更新における業務的な整合性は呼び出し元のサービスクラスが保証するため、DAOは感知しない。

updateTableNameにおいて、監査フィールドの正当性は呼び出し元のサービスクラスが保証するため、DAOは感知しない。

updateTableNameは、下記のPrisma例外を処理する。

- **一意制約違反** ConflictExceptionにラップして例外送出する。
- **外部キー違反** BadRequestExceptionにラップして例外送出する。
- **更新対象のレコードが見つからない** NotFoundExceptionにラップして例外送出する。
- **接続エラーなど、予期せぬ例外** InternalServerErrorExceptionにラップして例外送出する。

#### 論理削除メソッド

```TypeScript
/**
 * TableNameを論理削除する
 * @param prismaTx トランザクション
 * @param id TableNameのID(主キー)
 * @returns 論理削除したレコード
 */
softDeleteTableName(prismaTx: PrismaTransaction, id: string): Promise<TableName>{}
```

softDeleteTableNameは、データの論理削除そのものを担当し、論理削除における業務的な整合性は呼び出し元のサービスクラスが保証するため、DAOは感知しない。

softDeleteTableNameにおいて、監査フィールドの正当性は呼び出し元のサービスクラスが保証するため、DAOは感知しない。

softDeleteTableNameは、下記のPrisma例外を処理する。

- **論理削除対象のレコードが見つからない** NotFoundExceptionにラップして例外送出する。
- **接続エラーなど、予期せぬ例外** InternalServerErrorExceptionにラップして例外送出する。

#### 物理削除メソッド

```TypeScript
/**
 * TableNameを物理削除する
 * @param prismaTx トランザクション
 * @param id TableNameのID(主キー)
 * @returns 物理削除したレコード
 */
hardDeleteTableName(prismaTx: PrismaTransaction, id: string): Promise<TableName>{}
```

hardDeleteTableNameは、データの物理削除そのものを担当し、物理削除における業務的な整合性は呼び出し元のサービスクラスが保証するため、DAOは感知しない。

hardDeleteTableNameは、下記のPrisma例外を処理する。

- **物理削除対象のレコードが見つからない** NotFoundExceptionにラップして例外送出する。
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
                // isDeleted: falseを条件にしていることを確認する。
            });
            test('複数件の結果が返る場合', () => {
                // テストコードを実装
                // isDeleted: falseを条件にしていることを確認する。
            });
            test('0件の結果が返る場合', () => {
                // テストコードを実装
                // isDeleted: falseを条件にしていることを確認する。
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
    describe('softDeleteTableNameのテスト', () => {
        describe('正常系', () => {
            test('正常に論理削除ができる場合', () => {
                test('対象レコードが論理削除されている場合', () => {
                    // テストコードを実装
                });
                test('対象レコードが論理削除されていない場合', () => {
                    // テストコードを実装
                });
            });
        });
        describe('異常系', () => {
            test('論理削除レコードが見つからない場合', () => {
                // テストコードを実装
            });
            test('DB接続エラーが発生した場合', () => {
                // テストコードを実装
            });
        });
    });
    describe('hardDeleteTableNameのテスト', () => {
        describe('正常系', () => {
            test('正常に物理削除ができる場合', () => {
                test('対象レコードが論理削除されている場合', () => {
                    // テストコードを実装
                });
                test('対象レコードが論理削除されていない場合', () => {
                    // テストコードを実装
                });
            });
        });
        describe('異常系', () => {
            test('物理削除レコードが見つからない場合', () => {
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
});
```

## Moduleコード設計

- Moduleコードは、作成したすべてのDAOコードを依存性注入可能な部品としてサービス層に提供する。
- クラス名は`DatabaseModule`固定とする。
- Moduleコードに`@Global()`アノテーションを付与してはならない。

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
export class DatabaseModule {}
```

### Moduleテストコード設計

### Moduleテストコードファイル名

`database.module.spec.ts`とする。

### Moduleテストコードの実装内容

```TypeScript
describe('DatabaseModuleのテスト', () => {
    describe('正常系', () => {
        test('モジュールが正常にコンパイルできる場合', () => {
            // テストコードを実装
        });
    });
});
```

## ファイルパス

各ファイルは、以下のパスに配置される前提とせよ。また、`import`文は絶対パスで記述せよ。

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

- `/src/database/database.module.ts`
- `/src/database/database.module.spec.ts`

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

{PRISMA_CODE}
