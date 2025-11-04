# scms-prompt

本作品群は、[simple-contract-management-system](https://github.com/ryo-ichikawa-0308/simple-contract-management-system)において、AIガバナンスを行う、あるいはAIでコードを自動生成する際に用いるプロンプトである。これらのプロンプトをCI過程に組み込むことにより、DevOpsの向上を図ることが可能である。

## プロンプト一覧

* **[generate-json-from-db-docs.md](./generate-json-from-db-docs.md)** DB設計書をJSON形式に変換するプロンプト。下記の自動レビュープロンプト(JSON版)のインプットとする想定である。
* **[review-db-json.md](./review-db-json.md)** DB設計書(JSON版)を自動レビューするためのプロンプト。業務的な要件は人手で確認されていることが前提である。
* **[generate-prisma-from-db-json.md](./generate-prisma-from-db-json.md)** DB設計書(JSON版)からPrismaコードを自動生成するプロンプト。生成したPrismaコードをAPI設計書のレビュー・API実装に用いる想定である。

---

* **[generate-json-from-api-docs.md](./generate-json-from-api-docs.md)** API設計書をJSON形式に変換するプロンプト。
* **[review-api-json.md](./review-api-json.md)** API設計書(JSON版)を自動レビューするためのプロンプト。業務的な要件は人手で確認されていることと、PrismaコードがSource of truthとして作成されていることが前提。

---

* **[generate-dao-dto.md](./generate-dao-dto.md)** PrismaコードからDAO層のコードを自動生成するプロンプト。Pythonなどのスクリプトから生成AIのAPIに送信し、そのレスポンスをスクリプト側で解析して実コードに分離することを想定している。
* **[generate-api-from-api-docs.md](./generate-api-from-api-docs.md)** API設計書(JSON版)からコントローラー層・サービス層のスケルトンコードを自動生成するプロンプト。Pythonなどのスクリプトから生成AIのAPIに送信し、そのレスポンスをスクリプト側で解析して実コードに分離することを想定している。

## プロンプト一覧(旧作)

Markdownを直接レビューする想定で作成したプロンプト。MarkdownをJSON化してレビューさせたほうが正確性を期待できるので、下記の作品は「JSON化して突き合わせ」のアイディアに至る経過の作品として残しています。

* **[review-db-document.md](./old/review-db-document.md)** DB設計書を自動レビューするためのプロンプト。業務的な要件は人手で確認されていることが前提である。
* **[generate-prisma-code.md](./old/generate-prisma-code.md)** DB設計書からPrismaコードを自動生成するプロンプト。Pythonなどのスクリプトから生成AIのAPIに送信し、そのレスポンスをスクリプト側で解析して実コードに分離することを想定している。
* **[review-api-document.md](./old/review-api-document.md)** API設計書を自動レビューするためのプロンプト。DB設計書に忠実に実装されたPrismaコードが存在することが前提である。

## スクリプト

* **[gemini_script](./gemini_script/)** 上記のプロンプトをGeminiで動作確認するためのスクリプト(簡易版)。APIキーを設定したファイル`api.ini`が必要です。手動で下記の内容のファイルを作成してください。

```ini
[GEMINI]
API_KEY=YOUR_GEMINI_API_KEY
```

(C)2025 Ryo ICHIKAWA
