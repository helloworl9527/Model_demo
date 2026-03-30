from io import BytesIO
from pathlib import Path
from typing import Optional
from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(pdf_path: str) -> str:
    """从本地 PDF 文件提取文本内容。"""
    reader = PdfReader(pdf_path)
    texts = [(p.extract_text() or "") for p in reader.pages]
    merged = "\n".join(texts).strip()
    if not merged:
        raise ValueError("PDF 未提取到可用文本，可能是扫描件或空文件")
    return merged


def extract_text_from_pdf_bytes(content: bytes) -> str:
    """从 PDF 二进制内容提取文本。"""
    reader = PdfReader(BytesIO(content))
    texts = [(p.extract_text() or "") for p in reader.pages]
    merged = "\n".join(texts).strip()
    if not merged:
        raise ValueError("PDF 未提取到可用文本，可能是扫描件或空文件")
    return merged


def extract_text_from_docx_bytes(content: bytes) -> str:
    """从 DOCX 二进制内容提取文本。"""
    doc = Document(BytesIO(content))
    texts = [p.text for p in doc.paragraphs]
    merged = "\n".join(texts).strip()
    if not merged:
        raise ValueError("DOCX 未提取到可用文本")
    return merged


def load_plan_text(text: Optional[str] = None, pdf_path: Optional[str] = None) -> str:
    """统一加载审计方案文本：优先文本，其次本地 PDF 路径。"""
    if text is not None and text.strip():
        return text.strip()

    if pdf_path is not None and pdf_path.strip():
        p = Path(pdf_path.strip())
        if not p.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        if p.suffix.lower() != ".pdf":
            raise ValueError("pdf_path 必须是 .pdf 文件")
        return extract_text_from_pdf(str(p))

    raise ValueError("text 或 pdf_path 至少提供一个")


def load_plan_from_upload(filename: str, content: bytes) -> str:
    """统一加载上传文件文本，目前支持 PDF/DOCX。"""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf_bytes(content)
    if suffix == ".docx":
        return extract_text_from_docx_bytes(content)
    raise ValueError("仅支持 .pdf 或 .docx")