# scms-prompts

本作品群は、[simple-contract-management-system](https://github.com/ryo-ichikawa-0308/simple-contract-management-system)において、AIガバナンスを行う、あるいはAIでコードを自動生成する際に用いるプロンプトである。

コードを自動実装するプロンプトにおいては、AI作成のコードを手修正しているため、その過程で発生した仕様変更が反映されていない場合がある。

## プロンプト一覧

* **[create-prisma.md](./create-prisma.md)** DB設計書からPrismaコードを自動生成するPythonコードの設計書。この設計書に基づいてPythonコードを出力させ、必要な部分を手修正して製品コードとする。DBのスキーマは自動生成したPrismaコードを直接適用することで実装する。
* **[create-dao-dto.md](./create-dao-dto.md)** PrismaコードからDAO層のコードを自動生成するプロンプト。Pythonなどのスクリプトから生成AIのAPIに送信し、そのレスポンスをスクリプト側で解析して実コードに分離することを想定している。
* **[review-api-document.md](./review-api-document.md)** API設計書を自動レビューするためのプロンプト。DB設計書に忠実に実装されたPrismaコードが存在することが前提である。
