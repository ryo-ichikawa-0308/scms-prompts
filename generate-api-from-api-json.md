# API設計書をPrismaコードに変換する

本プロンプトは、JSON形式で記述されたAPIの設計書を読み込み、APIのコントローラークラス、ビジネスロジックのスケルトンクラス、DTOクラスを自動生成する手順書である。手動でのコード生成による設計と実装の乖離を予防し、開発効率を向上させることを目的とする。

## 前提

- API一覧及びAPI個別設計書群が「JSON入力構造」セクションのとおり正しく変換されており、API設計書として正しくレビューされている。特に、データベースとの整合性は厳密にチェック済みである。本プロンプトは、API設計のJSON及び`schema.prisma`をsource of truthとする。
- `schema.prisma`はデータベース定義書に忠実に作成されており、`schema.prisma`の各モデルに紐づいたテーブルDAOクラスが作成済みである。
- APIはNestJSで実装し、エンタープライズアーキテクチャに基づいて下記の4種類のディレクトリで構成される。本プロンプトの担当範囲は、`domain`層及び`service`層であり、その他の層は適切に実装されているものとする。
  - `src.domain`
    - エンドポイントとなるコントローラクラスと、登録・更新系APIのトランザクション管理を行うオーケストレーションクラスを格納する。
    - 外部とのデータ入出力の型であるDTOを格納する。
    - 各ドメインコンテキストごとにフォルダ分けされ、`DomainContextModule`(例: `UsersDomainModule`)モジュールとして、外部に機能を提供する。
    - `domain`層のモジュールは、`service`層のモジュール及び、`PrismaTransaction`(オーケストレーションクラスのみ)にのみ依存する。
  - `src.service`
    - ビジネスロジックを実装したサービスクラスを格納する。
    - `domain`層のDTOと、`database`層のDTOは、`service`のビジネスロジックによって詰め替えを行うことで各層の疎結合性を担保する。
    - ビジネスロジックは、機能コンテキストごとにフォルダ分けされ、`ServiceContextModule`(例: `UsersServiceModule`)モジュールとして、`domain`層のモジュールに機能を提供する。
    - `service`層のモジュールは、`database`層のモジュールにのみ依存する。
  - `src.database`
    - DBのテーブルと1:1で紐づくDAO及びDTOを格納する。すべてのDAOを纏めて、`DatabaseModule`モジュールとして`service`層のモジュールに機能を提供する。
    - DAOとテーブルDTOファイルはDBテーブルの物理名(snake_case)に合わせ、`{table_name}.dto/dao.ts`形式で命名されている。
    - 各DAOには、下記の基本メソッド及び、テーブル結合を前提とした取得メソッド・計数メソッドが実装されている。`service`層のモジュールは、これらのメソッドを呼び出すことでDB操作を行う。`{TableName}`はPrismaのモデル物理名を示すプレースホルダである。
      - `select{TableName}(dto: Select{TableName}Dto): Promise<{TableName}[]>{}` // テーブル単体の取得メソッド
      - `count{TableName}(dto: Select{TableName}Dto): Promise<number>{}` // テーブル単体の計数メソッド
      - `create{TableName}(prismaTx: PrismaTransaction, dto: Create{TableName}Dto): Promise<{TableName}>{}` // テーブル登録メソッド
      - `update{TableName}(prismaTx: PrismaTransaction, updateData: {TableName}): Promise<{TableName}>{}` // テーブル更新メソッド
      - `softDelete{TableName}(prismaTx: PrismaTransaction, id: string): Promise<{TableName}>{}` // 論理削除メソッド
      - `hardDelete{TableName}(prismaTx: PrismaTransaction, id: string): Promise<{TableName}>{}` // 物理削除メソッド
    - `database`層のモジュールは、`prisma`層のモジュールにのみ依存する。
  - `src.prisma`
    - `schema.prisma`を格納する。
    - Prisma接続サービスを`PrismaModule`モジュールとして`database`層のモジュールに機能を提供する。
    - `PrismaService`のインスタンスを`PrismaTransaction`型として`domain`層に提供するため、下記の型が提供されている。
      - `export type PrismaTransaction = Omit<PrismaClient, '...transaction以外を除外...' >;`

## JSON入力構造

入力は、下記の構造を持つJSONデータである。`apis`配下の配列は、`apiList.resource`(リソース)をキーとした配列オブジェクトである。`apis`配下の定義を元にAPIのコードを実装する。

DBのカラムと紐づく項目は、DBカラムの物理名と同じ物理名が与えられている。対応するテーブルは、Prismaコードのモデルコメントと`dbTable`の設定値(テーブル論理名)で紐づける。

| オブジェクトパス  | 概要                                                    | 主なプロパティ(抜粋)                                                                                                                                |
| ----------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| apis.{resource}[] | 各APIの定義情報。                                       | `summary`, `pathParameters`, `urlParameters`, `requestBody`, `response`, `errors`                                                                   |
| summary           | APIの基本情報。クラス名・メソッド名等の基本情報となる。 | `resource`, `action`, `method`, `endpoint`, `authRequired` (Boolean)                                                                                |
| pathParameters[]  | パスパラメータ。DTOのフィールドとなる。                 | `name` (物理名), `description` (論理名), `type`, `dbTable`, `required` (Boolean), `minLength`/`maxLength`, `min`/`max`, `format`, `children` (配列) |
| urlParameters[]   | URLパラメータ。DTOのフィールドとなる。                  | `name` (物理名), `description` (論理名), `type`, `dbTable`, `required` (Boolean), `minLength`/`maxLength`, `min`/`max`, `format`, `children` (配列) |
| requestBody[]     | リクエストボディ。DTOのフィールドとなる。               | `name` (物理名), `description` (論理名), `type`, `dbTable`, `required` (Boolean), `minLength`/`maxLength`, `min`/`max`, `format`, `children` (配列) |
| response          | レスポンス情報。                                        | `status` (Number), `body` (配列)                                                                                                                    |
| errors[]          | エラー情報。テストコードの異常系パターンとなる。        | `status` (Number), `message`, `detail`                                                                                                              |

## 命名規則

`apis.resource.summary`の記載に基づき、各クラスの命名規則を下記の通り定める。

### 0. 命名の基本情報

- `apis.resource.summary.resource` の記載をそのまま、あるいはPascalCaseとして、フォルダ名、クラス名等の基本文字列とする。以下、`{resource}`もしくは`{Resource}`のプレースホルダとして表現する。
- `apis.resource.summary.action` の記載をそのまま、あるいはPascalCaseとして、メソッドの基本文字列とする。以下、`{action}`もしくは`{Action}`のプレースホルダとして表現する。

### 1. DTOクラスの命名規則

`apis.resource.requestBody` `apis.resource.pathParameters` `apis.resource.urlParameters`の記載内容に基づき、下記のDTOを作成する。

- `apis.resource.requestBody`が空配列`[]`でない場合、下記の通りDTOクラスを作成する。
  - ファイル名を`{resource}-{action}-request.dto.ts`とする。(例: `users-list-request.dto.ts`)
  - クラス名を`{Resource}{Action}RequestDto`とする。(例: `UsersListRequestDto`)
  - `Controller`のメソッドが`@Body`引数として受け取る前提である。

- `apis.resource.pathParameters`が空配列`[]`でない場合、下記の通りDTOクラスを作成する。
  - ファイル名を`{resource}-{action}-pathparams.dto.ts`とする。(例: `users-list-pathparams.dto.ts`)
  - クラス名を`{Resource}{Action}PathParamsDto`とする。(例: `UsersListPathParamsDto`)
  - `Controller`のメソッドが`@Param()`として受け取る前提である。

- `apis.resource.urlParameters`が空配列`[]`でない場合、下記の通りDTOクラスを作成する。
  - ファイル名を`{resource}-{action}-urlparams.dto.ts`とする。(例: `users-list-urlparams.dto.ts`)
  - クラス名を`{Resource}{Action}UrlParamsDto`とする。(例: `UsersListUrlParamsDto`)
  - `Controller`のメソッドが`@Query()`として受け取る前提である。

- `apis.resource.response`が空配列`[]`でない場合、下記の通りDTOクラスを作成する。
  - ファイル名を`{resource}-{action}-response.dto.ts`とする。(例: `users-list-response.dto.ts`)
  - クラス名を`{Resource}{Action}ResponseDto`とする。(例: `UsersListResponseDto`)

- `apis.resource.requestBody.children[]`あるいは`apis.resource.response.body.children[]`項目に要素が存在する場合、親項目と同じディレクトリに、別ファイルとして切り出す。
  - 親項目における当該項目.`name`の設定値をkebab-caseあるいはPascalCaseとして、ファイル名、クラス名の基本文字列とする。以下、`{child-name}`もしくは`{ChildName}`のプレースホルダとして表現する。
  - `requestBody`の子要素の場合、`{parent-name}`は`request`(kebab-case)とする。
  - `response.body`の子要素の場合、`{parent-name}`は`response`(kebab-case)とする。
  - ファイル名を`{resource}-{parent-name}-{child-name}.dto.ts`とする。(例: `orders-request-details.dto.ts`)
  - クラス名を`{Resource}{ParentName}{ChildName}Dto`とする。(例: `OrdersRequestDetailsDto`)

- `apis.resource.pathParameters` `apis.resource.urlParameters`に基づくDTOクラスを作成した場合、この2つを統合して統合クエリDTOを作成する。
  - ファイル名を`{resource}-{action}-query.dto.ts`とする。(例: `users-list-query.dto.ts`)
  - クラス名を`{Resource}{Action}QueryDto`とする。(例: `UsersListQueryDto`)

### 2. DTOクラスの生成規則と共通化 (`src/domain`配下)

#### 2.1 共通 Paging DTO の適用と継承

- 共通クラスの事前定義: `src/domain/dto/common-paging.dto.ts` に、下記の `ListRequestBase`(クエリオプション)および `ListResponseBase<T>`(レスポンスラッパー)が実装済みの前提である。

```Typescript
export class ListRequestBase {
  /** 取得位置 */
  offset?: number;
  /** 取得件数 */
  limit?: number;
  /** ソートキー */
  sortBy?: string;
  /** ソート順 */
  sortOrder?: string;
}

export class ListResponse<T> {
  /** 検索条件にあてはまる総件数 */
  total: number;
  /** ページ番号(サーバー側で(offset / limit) + 1 として計算) */
  currentPage: number;
  /** 取得位置(リクエストと同じ値) */
  offset: number;
  /** 取得件数(リクエストと同じ値) */
  limit: number;
  /** 取得されたデータリスト。派生クラスで具体的なプロパティ名をつけて再定義する。 */
  @Exclude()
  data?: T[];
}
```

- リクエストDTOへの継承
  - リスト取得系API(`summary.action === "list"`)は、メソッドによって下記の通り`ListRequestBase`を継承する。
    - `method === "POST"`の場合、リクエストボディDTO (`{Resource}{Action}RequestDto`) が`ListRequestBase`を継承する。
    - `method === "GET"`の場合、統合クエリDTO (`{Resource}{Action}QueryDto`) が`ListRequestBase`を継承する。
  - ただし、`ListRequestBase`のプロパティと重複するフィールドがJSON入力構造に存在する場合は、そちらを優先する。
  - `import { ListRequestBase } from 'src/domain/dto/common-paging.dto.ts';`でページングDTOの型をimportする。
- レスポンスDTOへの適用
  - リスト取得系APIのレスポンスDTO (`{Resource}{Action}ResponseDto`) は、`ListResponseBase<T>` を利用し、`<T>` にリストの要素DTO(ネスト要素DTO)を渡す形で定義する。
  - レスポンスDTOで、`response.body`の配列型プロパティ名を用いてデータリスト配列を再定義する。(例: `contracts: Contract[];`)
  - `import { ListResponseBase } from 'src/domain/dto/common-paging.dto.ts';`でページングDTOの型をimportする。

#### 2.2 DTOのバリデーション

`pathParameters`, `urlParameters`, `requestBody` のフィールド定義を基に、以下の`NestJS/Class-Validator`のデコレータを適用する。

- 型: `type`を基に下記のClass-Validatorを適用する。
  - `type === "string"` の場合、`@IsString()`を適用する。
    - `format`に設定がある場合、対応するデコレータを適用する。最終的に人手確認とするため、[ADVICE]としてログ出力する。
      - `email`の場合、`@IsEmail()`を適用する。
      - `url`の場合、`@IsEmail()`を適用する。
      - `UUID`の場合、`@IsUUID()`を適用する。
      - 日付を示唆する可能性がある場合、`@IsDateString()`を適用する。
  - `type === "number"` の場合、`@IsNumber(), @Type(() => Number)`を適用する。`format`に`"int"`の指定がある場合(またはDBカラムが整数型と紐づく場合)、`@IsInt()`を併せて適用する。
  - `type === "boolean"` の場合、`@IsBoolean(), @Type(() => Boolean)`を適用する。
  - `type === "date"` の場合、`@IsDateString(), @Type(() => Date)`を適用する。
  - `type === "array"` の場合、`@IsArray(), @ValidateNested(), @Type()`を適用する。
  - `type === "object"` の場合、`@IsObject(), @ValidateNested(), @Type()`を適用する。`@Type(() => ChildDto)`とセットで利用する。
- 必須: `isRequired === true`の場合は`@IsNotEmpty()`を適用し、`isRequired === false`の場合は`@IsOptional()`を適用する。
  - `type === "array"`の場合は`@ArrayNotEmpty()`の適用有無と解釈する。
  - `pathParameters`の場合は常に`isRequired === true`として処理する。
- 桁数: `minLength`, `maxLength`の指定がある場合、`@MinLength()`, `@MaxLength()`を適用する。
- 範囲: `min`, `max`の指定がある場合、`@Min()`, `@Max()`を適用する。
  - `type === "array"`の場合は`@ArrayMinSize()`, `@ArrayMaxSize()`の適用有無と解釈する。

#### 2.3 パスパラメータとクエリパラメータの統合ルール (Controller/Service/Orchestrator間の連携)

ControllerとService/Orchestrator間で一貫したDTOを渡すため、以下のルールを適用する。

- Controller用 DTOの分離:
  - `pathParameters`が存在する場合: `{Resource}{Action}PathParamsDto` を生成し、Controllerの `@Param()` で使用する。
  - `urlParameters`が存在する場合: `{Resource}{Action}UrlParamsDto` を生成し、Controllerの `@Query()` で使用する。

- Service/Orchestrator用 統合DTOの生成:
  - `pathParameters` と `urlParameters` の両方のフィールドを統合し、`{Resource}{Action}QueryDto` を生成する。

- Controllerでの統合ロジック:
  - Controllerのメソッド内部で、`@Param()`で受け取ったオブジェクトと`@Query()`で受け取ったオブジェクトをスプレッド構文で結合し、`{Resource}{Action}QueryDto`型としてService/Orchestratorのメソッドに渡す。

例: `const {resource}{Action}Query: {Resource}{Action}QueryDto = { ...path, ...query };`

### 3. Controller/Orchestrator/Serviceクラスの命名規則

- Controllerクラス
  - ファイル名を`{resource}.controller.ts`とする。(例: `users.controller.ts`)
  - クラス名を`{Resource}Controller`とする。(例: `UsersController`)
- Orchestratorクラス
  - ファイル名を`{resource}.orchestrator.ts`とする。(例: `users.controller.ts`)
  - クラス名を`{Resource}Orchestrator`とする。(例: `UsersOrchestrator`)
- ドメインモジュール
  - ファイル名を`{resource}.domain.module.ts`とする。(例: `users.domain.module.ts`)
  - クラス名を`{Resource}DomainModule.ts`とする。(例: `UsersDomainModule`)
- Serviceクラス
  - ファイル名を`{resource}.service.ts`とする。(例: `users.service.ts`)
  - クラス名を`{Resource}Service`とする。(例: `UsersService`)
- サービスモジュール
  - ファイル名を`{resource}.service.module.ts`とする。(例: `users.service.module.ts`)
  - クラス名を`{Resource}ServiceModule.ts`とする。(例: `UsersServiceModule`)

### 4. 各層のコード生成規則 (Controller, Orchestrator, Service)

生成コードはすべてスケルトンとし、ビジネスロジックやDB操作の詳細は`// TODO: ...`コメントとして残す。

#### 4.1 `src/domain`層(Controllerクラス)の生成

- 処理委譲
  - `summary.method === "GET"` の場合は、トランザクション処理が不要のため、`{Resource}Service`に直接処理を委譲する。
  - `summary.action === "read"` かつ `summary.method === "POST"`の場合は、トランザクション処理が不要のため、`{Resource}Service`に直接処理を委譲する。
  - `summary.action !== "read"` かつ `summary.method === "POST/PATCH/PUT/DELETE"`の場合は、トランザクション処理を行うため、`{Resource}Orchestrator`に処理を委譲する。

- DTO統合: `pathParams`, `urlParams` のDTOが存在する場合、メソッド内部で統合DTOに結合する処理を記述する。

- ルーティングパスの抽出
- `apis.summary.endpoint` の記載から、ルーティングパスを抽出する。
  - ベースパス部分(`/api/v1`など)は省略されている前提である。
  - URLパラメータ部分(`?`以降)を含む場合、これを除去し、残ったパスを下記の通り処理する。
    - 最初のパスセグメント(例: `/users`)を抽出し、前後の`/`を除去して`@Controller('{resource}')`の引数として使用する。(例: `@Controller('users')`)
    - 残りのパスセグメント(例: `/{id}`)を抽出する。`{}`で囲まれた文字列は変数として`:`付き表記に変換する。(例: `{id}` → `:id`)
    - 残りのパスが存在しない場合は`/`とする。
    - これをメソッドデコレーター(例: `@Get('/:id')`)の引数として使用する。

- デコレーターの付与
  - 抽出したデコレーターの記載に基づいて、`@Controller('{resource}')`デコレーターを付与する。
  - `summary.method`及び抽出したデコレーターの記載に基づいて、各メソッドの`@Method('endpoint_path')`デコレーターを付与する。
  - `summary.authRequired === true`の場合、当該メソッドに`@UseGuards(AuthGuard('jwt'))`デコレーターを付与する。
  - `response.status`の記載に基づいて、各メソッドに`@HttpCode(HttpStatus.{CODE})`デコレーターを付与する。番号ではなく、ステータス定数名で付与すること。

- 下記のテンプレートに基づいて、定義されているメソッドを生成する。

```Typescript
// src/domain/{resource}/{resource}.controller.ts
@Controller('{resource}') // apis.resource.summary.resource に基づくエンドポイント
@UsePipes(new ValidationPipe({ transform: true }))
export class {Resource}Controller {
  constructor(
    private readonly {resource}Service: {Resource}Service,
    private readonly {resource}Orchestrator: {Resource}Orchestrator,
  ) {}

  // GETメソッドのテンプレート
  /**
   * {description}
   * @param pathParams Pathパラメータ (apis.resource.pathParametersが存在する場合)
   * @param urlParams URLクエリパラメータ (apis.resource.urlParametersが存在する場合)
   * @returns {Resource}{Action}ResponseDto
   */
  @Get('{endpoint_path}') // 例: 'users' の中の '/:id' など
  @UseGuards(AuthGuard('jwt'))
  @HttpCode(HttpStatus.OK)
  async {action}(
    @Param() pathParams: {Resource}{Action}PathParamsDto, // pathParametersが空配列でない場合のみ設定
    @Query() urlParams: {Resource}{Action}UrlParamsDto, // urlParametersが空配列でない場合のみ設定
  ): Promise<{Resource}{Action}ResponseDto> {
    // 1. Path/Queryパラメータの統合
    // 必須項目がなければ、DTOのプロパティを ? でOptionalにするか、Path/QueryDTOの代わりに{}を利用する
    const query: {Resource}{Action}QueryDto = { ...pathParams, ...urlParams };

    // 2. 処理委譲 (GETメソッドはServiceに委譲)
    return this.{resource}Service.{action}(query);
  }

  // Post/listメソッドのテンプレート
  /**
   * {description}
   * @param pathParams Pathパラメータ (apis.resource.pathParametersが存在する場合)
   * @param urlParams URLクエリパラメータ (apis.resource.urlParametersが存在する場合)
   * @param body Request Body (apis.resource.requestBodyが存在する場合)
   * @param req Express Requestオブジェクト (authRequired === trueの場合のみ)
   * @returns {Resource}{Action}ResponseDto
   */
  @Post('{endpoint_path}') // 例: 'users' の中の '/' や '/:id/reset-password' など
  @UseGuards(AuthGuard('jwt')) // authRequired === trueの場合のみ指定する
  @HttpCode(HttpStatus.OK)
  async {action}(
    @Param() pathParams: {Resource}{Action}PathParamsDto, // pathParametersが空配列でない場合のみ設定
    @Query() urlParams: {Resource}{Action}UrlParamsDto, // urlParametersが空配列でない場合のみ設定
    @Body() body: {Resource}{Action}RequestDto,
  ): Promise<{Resource}{Action}ResponseDto> {

    // 1. クエリの結合
    const query: {Resource}{Action}QueryDto = { ...pathParams , ...urlParams };

    // 2. 処理委譲 (POST/readメソッドはServiceに委譲)
    return this.{resource}Service.{action}(body, query);
  }

  // 登録系メソッドのテンプレート
  /**
   * {description}
   * @param pathParams Pathパラメータ (apis.resource.pathParametersが存在する場合)
   * @param urlParams URLクエリパラメータ (apis.resource.urlParametersが存在する場合)
   * @param body Request Body (apis.resource.requestBodyが存在する場合)
   * @param req Express Requestオブジェクト (authRequired === trueの場合のみ)
   * @returns 登録したリソースのID
   */
  @Post('{endpoint_path}') // 例: 'users' の中の '/' や '/:id/reset-password' など
  @UseGuards(AuthGuard('jwt')) // authRequired === trueの場合のみ指定する
  @HttpCode(HttpStatus.CREATED)
  async {action}(
    @Param() pathParams: {Resource}{Action}PathParamsDto, // pathParametersが空配列でない場合のみ設定
    @Query() urlParams: {Resource}{Action}UrlParamsDto, // urlParametersが空配列でない場合のみ設定
    @Body() body: {Resource}{Action}RequestDto,
    @Req() req: Request,　// authRequired === trueの場合のみ指定する
  ): Promise<string> {

    // 1. Path/Queryパラメータの統合 (POST/PUT/PATCH/DELETEではURLパラメータは稀だが、存在する場合は統合する)
    const query: {Resource}{Action}QueryDto = { ...pathParams , ...urlParams };

    // 2. 処理委譲 (POST/PUT/PATCH/DELETEメソッドはOrchestratorに委譲)
    // 委譲の引数として、統合されたクエリ情報、リクエストボディ、認証情報から取得したユーザーIDなどを渡す。
    // const userId = req.user.id; // authRequired === trueの場合のみ、userIdを取得する。
    return this.{resource}Orchestrator.{action}(body, query /*, userId */);
  }

  // 更新系メソッドのテンプレート
  /**
   * {description}
   * @param pathParams Pathパラメータ (apis.resource.pathParametersが存在する場合)
   * @param urlParams URLクエリパラメータ (apis.resource.urlParametersが存在する場合)
   * @param body Request Body (apis.resource.requestBodyが存在する場合)
   * @param req Express Requestオブジェクト (認証情報を取得する目的で利用)
   */
  @Patch('{endpoint_path}') // 例: 'users' の中の '/' や '/:id/reset-password' など。デコレーター@Patch、@Put、@Deleteはmethodの設定値により選択する。
  @UseGuards(AuthGuard('jwt')) // authRequired === trueの場合指定する
  @HttpCode(HttpStatus.NO_CONTENT)
  async {action}(
    @Param() pathParams: {Resource}{Action}PathParamsDto, // pathParametersが空配列でない場合のみ設定
    @Query() urlParams: {Resource}{Action}UrlParamsDto, // urlParametersが空配列でない場合のみ設定
    @Body() body: {Resource}{Action}RequestDto,
    @Req() req: Request,　// authRequired === trueの場合のみ指定する
  ): Promise<void> {

    // 1. Path/Queryパラメータの統合 (POST/PUT/PATCH/DELETEではURLパラメータは稀だが、存在する場合は統合する)
    const query: {Resource}{Action}QueryDto = { ...pathParams , ...urlParams };

    // 2. 処理委譲 (POST/PUT/PATCH/DELETEメソッドはOrchestratorに委譲)
    // 委譲の引数として、統合されたクエリ情報、リクエストボディ、認証情報から取得したユーザーIDなどを渡す。
    // const userId = req.user.id; // authRequired === trueの場合のみ、userIdを取得する。
    this.{resource}Orchestrator.{action}(body, query /*, userId */);
  }
}
```

#### 4.2 `src/domain`層(Orchestratorクラス)の生成

- 責務
  - `summary.action !== "read"` かつ `summary.method === "POST/PATCH/PUT/DELETE"`の場合に対応する。
  - トランザクション管理と、必要なサービスクラスのオーケストレーションを行う。
  - 下記のテンプレートに基づいて、定義されている`summary.action`に対応するメソッドのスケルトンを作成する。
  - テンプレートの`{name}`は、`apis.resource.summary.name`の記載内容のプレースホルダである。

```Typescript
// src/domain/{resource}/{resource}.orchestrator.ts
/** 
 * {Resource}のオーケストレーションクラス 
 */
@Injectable()
export class {Resource}Orchestrator {
  constructor(
    private readonly {resource}Service: {Resource}Service,
    // PrismaServiceから $transaction のみ公開するインターフェースをDI
    private readonly prismaTransaction: PrismaTransaction,
  ) {}

  // 登録系Actionのオーケストレーションメソッド
  /**
   * {name}
   * @param body {Resource}{Action}RequestDto
   * @param query {Resource}{Action}QueryDto
   * @param userId 認証情報から取得したユーザーID(認証を前提とするAPIの場合)
   * @returns 登録したリソースのID
   */ 
  async {action}(
      body: {Resource}{Action}RequestDto, 
      query: {Resource}{Action}QueryDto, 
      userId: string // authRequired === trueの場合のみ指定する
    ): Promise<string> {  
    // 1. TODO: 項目間関連チェック(Service層のメソッドを呼び出す)

    // 2. TODO: 作成者IDとトランザクション開始作成時刻の取得
    // const userId = {USER_UUID}; // 認証を前提としない場合、トランザクション開始時に生成する。
    const txDateTime = {CURRENT_TIMESTAMP};

    // 3. TODO: PrismaTransactionServiceを呼び出し、トランザクションを開始
    await this.prismaTransaction.$transaction(async (prismaTx: PrismaTransaction) => {
    
    // 4. TODO: Service層のトランザクション対応メソッドを呼び出し、prismaTx, userId, txDateTime, 各種dtoを渡す
    const result = this.service.createWithTx(prismaTx, userId, txDateTime, dto);

    // 5. TODO: 複数のリソースを跨ぐ場合は、他のServiceのprismaTx対応メソッドも呼び出す

    // 6. TODO: 成功したら自動的にコミット。失敗時はロールバック。
    return result.id;
    });
  }

  // 更新系・その他Actionのオーケストレーションメソッド
  /**
   * {name}
   * @param body {Resource}{Action}RequestDto
   * @param query {Resource}{Action}QueryDto
   * @param userId 認証情報から取得したユーザーID(認証を前提とするAPIの場合)
   */ 
  async {action}(
    body: {Resource}{Action}RequestDto,
    query: {Resource}{Action}QueryDto,
    userId: string // authRequired === trueの場合のみ指定する
    ) {
    // 1. TODO: 項目間関連チェック(Service層のメソッドを呼び出す)
  
    // 2. TODO: トランザクション開始作成時刻の取得
    // const userId = {USER_UUID}; // 認証を前提としない場合、トランザクション開始時に生成する。
    const txDateTime = {CURRENT_TIMESTAMP};
  
    // 3. TODO: PrismaTransactionServiceを呼び出し、トランザクションを開始
    await this.prismaTransaction.$transaction(async (prismaTx: PrismaTransaction) => {
  
    // 4. TODO: Service層のトランザクション対応メソッドを呼び出し、prismaTx, userId, txDateTime, 各種DTOを渡す
    const result = this.service.{action}WithTx(prismaTx, userId, txDateTime, dto);
  
    // 5. TODO: 複数のリソースを跨ぐ場合は、他のServiceのprismaTx対応メソッドも呼び出す

    // 6. TODO: 成功したら自動的にコミット。失敗時はロールバック。
    });
  }
}
```

#### 4.3 `src/domain`層(Moduleクラス)の生成

```TypeScript
// src/service/{resource}/{resource}.domain.module.ts
@Module({
  imports: [{Resource}ServiceModule], 
  providers: [
    {Resource}Controller,
    {Resource}Orchestrator,
    // 当該リソースに紐づいて作成したコントローラークラス・オーケストレーションクラスを記載する
  ],
})
export class {Resource}DomainModule {}
```

#### 4.4 `src/service`層(Serviceクラス)の生成

- Serviceクラスの生成
  - DI: コンストラクタで、DatabaseModuleから提供されるDAO(例: UsersDao)をDIする。

- メソッド定義
  - 取得系 (`GET`および `POST/read`)
    - 定義: 統合クエリDTO(及び、`POST/read`の場合はリクエストボディを含む)を受け取り、DAOを呼び出すメソッドを定義する。
    - 命名規則: `{action}のCamelCase`表現(例: `findAll`, `findOne`)。

  - 登録・更新・削除系 (`POST`, `PATCH`, `PUT`, `DELETE`)
    - Orchestratorがトランザクションを管理するため、トランザクション非対応メソッドは定義しない。
    - 定義: 以下の引数を必須とする `{action}WithTx`メソッドを定義し、DAOのトランザクション対応メソッドを呼び出す。
    - `prismaTx: PrismaTransaction` トランザクションオブジェクト
    - `userId: string` 認証情報から取得した作成/更新者ID
    - `txDateTime: Date` トランザクション開始日時
    - `data: {Resource}{Action}RequestDto` リクエストボディDTO。更新・登録系の場合のみ。
    - 命名規則: `{action}WithTx`のCamelCase表現(例: `createWithTx`, `updateWithTx`)。
  
  - 関連チェックメソッド
    - DB検索を前提とするバリデーションは、取得系メソッドとして人手で実装するため、スケルトンは作成しない。

```Typescript
// src/service/{resource}/{resource}.service.ts
/** 
 * {Resource}のサービスクラス 
 */
@Injectable()
export class {Resource}Service {
  constructor(
    private readonly {tableName}Dao: {TableName}Dao, //(例：usersDao: UsersDao, ordersDao: OrdersDao等)
  ) {}
  // 取得系メソッドのテンプレート
  /**
   * {name}
   * @param body {Resource}{Action}QueryRequestDto // POST/listの場合
   * @param query {Resource}{Action}QueryDto
   * @returns 登録した{resource}のTableNameDto
   */
  async {action}(
      body {Resource}{Action}QueryRequestDto, // POST/listの場合
      query: {Resource}ListQueryDto
    ): Promise<{Resource}ListResponseDto> {
    // 1. TODO: Request/QueryDtoからDB検索条件を生成 (Paging/Filtering)
    // 2. TODO: DatabaseModule (DAO)を呼び出し、DB検索を実行
    // 3. TODO: 検索結果をResponseDtoへ詰め替え (TableDto -> ResponseDto)
    // 4. TODO: ResponseDtoを返却
  }
  
  // 登録・更新系メソッドのテンプレート
  /**
   * {name}
   * @param prismaTx トランザクション
   * @param userId トランザクション実行者のID(認証情報から取得)
   * @param txDateTime トランザクション開始日時
   * @param query {Resource}{Action}RequestDto
   * @returns {Resource}{Action}ResponseDto
   */
  async {action}WithTx(
    prismaTx: PrismaTransaction, 
    userId: string, 
    txDateTime: Date, 
    query: {Resource}{Action}RequestDto
  ): Promise<{Resource}{Action}ResponseDto> {
    // 1. TODO: RequestDtoからDB登録データ (DAO) へ詰め替え (RequestDto -> TableDto) schema.prismaの型情報、制約を利用する。
    // 2. TODO: ビジネスロジックの実行 (バリデーション、採番、属性付与など)
    // 3. TODO: DAOのtx対応メソッドを呼び出し、DB登録を実行 (prismaTxを渡す)
    // 4. TODO: DB結果を ResponseDto へ詰め替え (TableDto -> ResponseDto)
    // 5. TODO: ResponseDtoを返却
  }
}
```

#### 4.5 `src/service`層(Moduleクラス)の生成

```TypeScript
// src/service/{resource}/{resource}.service.module.ts
@Module({
  imports: [DatabaseModule], 
  providers: [
    {Resource}Service,
    // 当該リソースに紐づいて作成したサービスクラスを記載する
  ],
  exports: [
    {Resource}Service,
    // 当該リソースに紐づいて作成したサービスクラスを記載する
  ],
})
export class {Resource}ServiceModule {}
```

### 5. テストクラスの作成

各クラスと同階層に、クラスファイルと対応するテストコードを作成する。テストコードのファイル名は、テスト対象のファイル名に対して、`{source-code.name}.spec.ts`とする。

#### 5.1 DTOのテストコード(例: users-create-request.dto.spec.ts)

DTOクラスそれぞれのバリデーション確認を行う。テストにはclass-transformerとclass-validatorを使用する。

```TypeScript
describe('{Resource}{Action}RequestDtoのテスト', () => {
  // 正常なテストデータを定義 (プロンプト内の型情報に基づき生成)
  const validData = {
    // TODO: 全ての必須項目と任意項目を満たした正常データ
    // userId: 1,
    // name: "Test User",
  };
  describe('正常系', () => {
    test('必須項目すべてに入力がある場合、エラーがないこと', async () => {
      const dto = plainToInstance({Resource}{Action}RequestDto, validData);
      const errors = await validate(dto);
      expect(errors.length).toBe(0);
    });
    test('任意項目が未入力の場合、エラーがないこと', async () => {
      const optionalDataMissing = {
        ...validData,
        // TODO: 任意項目を一つ削除
      };
      const dto = plainToInstance({Resource}{Action}RequestDto, optionalDataMissing);
      const errors = await validate(dto);
      expect(errors.length).toBe(0);
    });
  });
  describe('異常系', () => {
    test('必須項目が未入力の場合、エラーが発生すること', async () => {
      const dataMissingRequired = {
        ...validData,
        // TODO: 必須項目を一つ null または undefined に設定
      };
      const dto = plainToInstance({Resource}{Action}RequestDto, dataMissingRequired);
      const errors = await validate(dto);
      // TODO: エラー件数と、対象フィールドのエラーメッセージを検証
      expect(errors.length).toBeGreaterThan(0);
    });
    test('型違反の入力がある場合、エラーが発生すること', async () => {
      const dataWithTypeViolation = {
        ...validData,
        // TODO: 数値型のはずのフィールドに文字列を設定
      };
      const dto = plainToInstance({Resource}{Action}RequestDto, dataWithTypeViolation);
      const errors = await validate(dto);
      // TODO: エラー件数と、対象フィールドのエラーメッセージを検証
      expect(errors.length).toBeGreaterThan(0);
    });
  });
});
```

#### 5.2 Controllerクラスのテストコード (例: users.controller.spec.ts)

NestJSのTestingModuleとモックを利用した単体テストのスケルトンを定義する。

```TypeScript
describe('{Resource}Controllerのテスト', () => {
  let controller: {Resource}Controller;
  // Service/Orchestratorはモック化する
  const mockService = {
    // TODO: Serviceメソッドをモック化
    findAll: jest.fn(),
    findOne: jest.fn(),
  };
  const mockOrchestrator = {
    // TODO: Orchestratorメソッドをモック化
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  };
  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [{Resource}Controller],
      // 依存関係をモックで提供
      providers: [
        { provide: {Resource}Service, useValue: mockService },
        { provide: {Resource}Orchestrator, useValue: mockOrchestrator },
      ],
    }).compile();
    controller = module.get<{Resource}Controller>({Resource}Controller);
  });
  it('コントローラが定義されていること', () => {
    expect(controller).toBeDefined();
  });
  describe('{Action} (GET) APIのテスト', () => {
    const responseData = { /* TODO: 期待されるレスポンスデータ */ };
      
    test('正常系: クエリパラメータを統合し、Serviceを呼び出すこと', async () => {
      mockService.findOne.mockResolvedValue(responseData);
          
      // TODO: テスト用のパス/クエリデータ
      const pathParams = { /* ... */ };
      const queryParams = { /* ... */ };
      // 統合DTOがServiceに渡されることを検証
      await controller.findOne(pathParams, queryParams);
      expect(mockService.findOne).toHaveBeenCalledWith(
        expect.objectContaining({ ...pathParams, ...queryParams })
      );
    });
    test('異常系: DB接続エラーが発生した場合', async () => {
      mockService.findOne.mockRejectedValue('DB Error');
          
      // TODO: テスト用のパス/クエリデータ
      const pathParams = { /* ... */ };
      const queryParams = { /* ... */ };
      // 統合DTOがServiceに渡されることを検証
      await controller.findOne(pathParams, queryParams);
      expect(mockService.findOne).toHaveBeenCalledWith(
        expect.objectContaining({ ...pathParams, ...queryParams })
      );
    });
    // TODO: apis.resource.errorsのエラー定義に基づいて、エラーが発生した場合の動作を検証する。
  });
  // TODO: {Action} (POST/PUT/DELETE) APIのテストも同様に追加し、Orchestratorの呼び出しを検証する。
});
```

#### 5.3 Orchestrator/Serviceクラスのテストコード (例: users.orchestrator.spec.ts / users.service.spec.ts)

OrchestratorとServiceのテストは、ビジネスロジックの実行と、下位レイヤー(Service/DAO)の適切な呼び出しを検証する単体テストのスケルトンとする。

```TypeScript
// Orchestrator/Serviceのテストスケルトン (共通)
// TODO: テスト対象のクラスと依存関係をインポート
describe('{ClassName}のテスト', () => {
  let target: {ClassName};
  // TODO: 依存関係のモック
  const mockService = { /* ... */ };
  const mockDAO = { /* ... */ };
  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        {ClassName},
        // TODO: 依存関係をモックでプロバイダーに設定
      ],
    }).compile();
    target = module.get<{ClassName}>({ClassName});
  });
  describe('{Action}WithTx メソッドのテスト', () => {
    const mockTx = { /* TODO: PrismaTransactionモック */ };
    const mockId = 'user-id-123';
    const mockDate = new Date();
    test('正常系: Service/DAOのメソッドがトランザクション内で正しく呼び出されること', async () => {
      // TODO: モックの戻り値を設定
      // mockService.createWithTx.mockResolvedValue(/* ... */);
      await target.create(/* TODO: Request DTOデータ */);
      // TODO: 呼び出し検証
      // expect(mockService.createWithTx).toHaveBeenCalledWith(
      //     mockTx, 
      //     mockId, 
      //     mockDate, 
      //     expect.any(Object)
      // );
    });
    test('異常系: 処理中にエラーが発生した場合、トランザクションがロールバックされること', async () => {
      // TODO: エラーをスローするようにモックを設定
      // mockService.createWithTx.mockRejectedValue(new Error('DB Error'));
      // トランザクションのエラー処理を検証
      await expect(target.create(/* ... */)).rejects.toThrow('DB Error');
    });
    // TODO: apis.resource.errorsのエラー定義に基づいて、エラーが発生した場合の動作を検証する。
  });
  // TODO: 取得系メソッドのテストも同様に追加
});
```

#### 5.4 Moduleクラスのテストコード  (例: users.service.module.spec.ts)

モジュールクラスが正常にコンパイルできることを検証する単体テストとする。

```TypeScript
describe('ModuleNameのテスト', () => {
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

- `src/prisma/prisma.type.ts`

### database層のDAO/DTO/Moduleコードのパス

- `src/database/dao/table_name.dao.ts`
- `src/database/dto/table_name.dto.ts`
- `src/database/database.module.ts`

### domain層のController/Orchestrator/Dto/Moduleコード・テストコードのパス

- `src/domain/{resource}/{resource}.controller.ts`
- `src/domain/{resource}/{resource}.controller.spec.ts`
- `src/domain/{resource}/{resource}.orchestrator.ts`
- `src/domain/{resource}/{resource}.orchestrator.spec.ts`

- `src/domain/{resource}/{resource}-{child-name}.dto.ts`
- `src/domain/{resource}/{resource}-{child-name}.dto.spec.ts`

- `
- `src/domain/{resource}/{resource}-{action}-request.dto.ts`
- `src/domain/{resource}/{resource}-{action}-request.dto.spec.ts`

- `src/domain/{resource}/{resource}-{action}-urlparams.dto.ts`
- `src/domain/{resource}/{resource}-{action}-urlparams.dto.spec.ts`

- `src/domain/{resource}/{resource}-{action}-pathparams.dto.ts`
- `src/domain/{resource}/{resource}-{action}-pathparams.dto.spec.ts`

- `src/domain/{resource}/{resource}-{parent-name}-{child-name}.dto.ts`
- `src/domain/{resource}/{resource}-{parent-name}-{child-name}.dto.spec.ts`

- `src/domain/{resource}/{resource}.domain.module.ts`
- `src/domain/{resource}/{resource}.domain.module.spec.ts`

### service層のService/Moduleコード・テストコードのパス

- `src/service/{resource}/{resource}.service.ts`
- `src/service/{resource}/{resource}.service.spec.ts`
- `src/service/{resource}/{resource}.service.module.ts`
- `src/service/{resource}/{resource}.service.module.spec.ts`

## 出力方式

作成したコードは、下記のフォーマットで返却せよ。受領側でスクリプト処理を行い、セパレーター(`------`)で分割して、そのまま実装コードとして出力する想定である。このため、セパレーター・ファイル名・実装内容以外の内容を含めてはならない。

```text
------
xxxxx.module/controller/orchestrator/service.ts
------
// xxxxx.module/controller/orchestrator/service.tsの実装内容
------
xxxxx.module/controller/orchestrator/service.spec.ts
------
// xxxxx.module/controller/orchestrator/service.spec.tsの実装内容
------
xxxxx.dto.ts
------
// xxxxx.dto.tsの実装内容
------
xxxxx.dto.spec.ts
------
// xxxxx.dto.spec.tsの実装内容
------
```

## API設計書とPrismaコード

{API_JSON}

{SCHEMA_PRISMA}
