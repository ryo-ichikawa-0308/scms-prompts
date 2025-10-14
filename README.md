# scms-prompts

ミニ契約管理システムにおいて、AIガバナンスを行う、あるいはAIでコードを自動生成する際に用いるプロンプト。

## プロンプト一覧

* **[create-prisma.md](./create-prisma.md)** DB設計書からPrismaコードを自動生成するPythonコードの設計書。この設計書に基づいてPythonコードを出力させ、必要な部分を手修正して製品コードとする。DBのスキーマは自動生成したPrismaコードを直接適用することで実装する。
* **[create-dao-dto.md](./create-dao-dto.md)** PrismaコードからDAO層のコードを自動生成するプロンプト。Pythonなどのスクリプトから生成AIのAPIに送信し、そのレスポンスをスクリプト側で解析して実コードに分離する。
