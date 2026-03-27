# PawapoAI (Pro PPTX Generator) 🚀

ローカルAI（LLM）を活用して、PowerPointのスライド構成から詳細内容の生成、そして実際の `.pptx` ファイル作成までを一気通貫で行うデスクトップアプリケーションです。

「よく動く試作品」から「壊れないプロダクト」へ。堅牢なアーキテクチャと並列処理による高速な生成体験を提供します。

## 🌟 主な機能

- **📋 フェーズ1：構成案（アジェンダ）の自動作成**
  - テーマと指示を入力するだけで、スライド全体の流れをAIが企画します。
- **🚀 フェーズ2：スライド詳細の並列生成**
  - ThreadPoolを利用した並列処理により、全スライドの内容を短時間で一括生成します。
- **💎 フェーズ3：AIリライト（美化）**
  - 生成されたテキストを指定したトーン（ビジネス、カジュアル、エネルギッシュ等）で自動修正。差分表示機能付きで修正箇所が一目でわかります。
- **📂 参考資料の読み込み (RAG対応)**
  - PDF, TXT, HTML（URL抽出対応）を解析し、資料に基づいた正確なコンテンツを作成します。
- **🎨 PowerPoint 構築**
  - テンプレート（.pptx）を利用して、実際のパワーポイントファイルとして書き出し可能です。

## 🛠️ 技術スタック

- **Frontend/UI**: Streamlit
- **LLM Engine**: LM Studio (Local OpenAI-compatible API)
- **Logic**: Python 3.10+
- **Parsing**: Trafilatura (HTML), PyPDF2 (PDF)
- **Validation**: Pydantic v2

## 🚀 クイックスタート

詳細な手順は [セットアップガイド](docs/setup_guide.md) を参照してください。

### 1. 環境構築
```bash
# リポジトリのクローン
git clone https://github.com/f4sT357/PawapoAI.git
cd PawapoAI

# 仮想環境の作成と起動
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. LM Studio の準備
1. [LM Studio](https://lmstudio.ai/) を起動します。
2. お好みのモデルをロードし、**Local Server** を `ON` にします。
3. デフォルトのURLは `http://localhost:1234/v1` です。

### 3. アプリの起動
```bash
streamlit run app.py
```

## ⚠️ 注意事項
- 本アプリはローカル環境での動作を前提としており、外部サーバーへデータを送信しません（LM Studioを使用する場合）。
- `data/` フォルダにアップロードした資料は、AIの回答精度向上のために解析されます。

## 📄 ライセンス
このプロジェクトは [MIT License](LICENSE) の下で公開されています。
