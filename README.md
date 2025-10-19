# scms-prompts

本作品群は、[simple-contract-management-system](https://github.com/ryo-ichikawa-0308/simple-contract-management-system)において、AIガバナンスを行う、あるいはAIでコードを自動生成する際に用いるプロンプトである。これらのプロンプトをCI過程に組み込むことにより、DevOpsの向上を図ることが可能である。

## プロンプト一覧

* **[review-db-document.md](./review-db-document.md)** DB設計書を自動レビューするためのプロンプト。業務的な要件は人手で確認されていることが前提である。
* **[review-api-document.md](./review-api-document.md)** API設計書を自動レビューするためのプロンプト。DB設計書に忠実に実装されたPrismaコードが存在することが前提である。
* **[generate-prisma-code.md](./generate-prisma-code.md)** DB設計書からPrismaコードを自動生成するプロンプト。Pythonなどのスクリプトから生成AIのAPIに送信し、そのレスポンスをスクリプト側で解析して実コードに分離することを想定している。
* **[generate-dao-dto.md](./generate-dao-dto.md)** PrismaコードからDAO層のコードを自動生成するプロンプト。Pythonなどのスクリプトから生成AIのAPIに送信し、そのレスポンスをスクリプト側で解析して実コードに分離することを想定している。

(C)2025 Ryo ICHIKAWA
