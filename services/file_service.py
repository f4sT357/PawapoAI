import io
from pathlib import Path
from typing import Union, List, Optional
from PyPDF2 import PdfReader
import trafilatura
from utils.logger import logger

class FileService:
    def __init__(self, data_dir: Path, templates_dir: Path):
        self.data_dir = data_dir
        self.templates_dir = templates_dir
        
        # フォルダの自動作成
        self.data_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)

    def extract_text(self, file_source: Union[Path, object]) -> str:
        """
        アップロードされたファイル、またはファイルパスからテキストを抽出する
        """
        try:
            # 1. Path オブジェクトの場合
            if isinstance(file_source, Path):
                suffix = file_source.suffix.lower()
                if suffix == ".pdf":
                    return self._extract_pdf(file_source)
                elif suffix == ".txt":
                    with open(file_source, "r", encoding="utf-8") as f:
                        return f.read()
                elif suffix in [".html", ".htm"]:
                    with open(file_source, "r", encoding="utf-8") as f:
                        return trafilatura.extract(f.read(), output_format="markdown", include_formatting=True)
                return ""
            
            # 2. Streamlit UploadedFile オブジェクトの場合
            # type, name プロパティがあることが前提
            file_type = getattr(file_source, "type", "")
            file_name = getattr(file_source, "name", "")
            
            if "pdf" in file_type or file_name.endswith(".pdf"):
                return self._extract_pdf(file_source)
            elif "text/plain" in file_type or file_name.endswith(".txt"):
                return str(file_source.read(), "utf-8")
            elif "text/html" in file_type or file_name.endswith(".html") or file_name.endswith(".htm"):
                return trafilatura.extract(file_source.read(), output_format="markdown", include_formatting=True)
            
            return ""
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return f"Error: {e}"

    def _extract_pdf(self, source) -> str:
        """PDFからテキストを抽出する内部メソッド"""
        try:
            reader = PdfReader(source)
            text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return ""

    def get_files_in_directory(self, directory: Path) -> List[str]:
        """ディレクトリ内のファイル一覧を取得"""
        if directory.exists():
            return sorted([f.name for f in directory.iterdir() if f.is_file()])
        return []

    def save_uploaded_file(self, uploaded_file, target_dir: Path) -> Optional[Path]:
        """アップロードされたファイルを保存し、保存先のパスを返す"""
        try:
            save_path = target_dir / uploaded_file.name
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return save_path
        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            return None
