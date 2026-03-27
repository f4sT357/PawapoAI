from pydantic import BaseModel, Field
from typing import List, Optional

class SlidePlan(BaseModel):
    slide_number: int = Field(..., description="スライドの番号")
    title: str = Field(..., description="スライドのタイトル")
    description: str = Field(..., description="このスライドで説明する主な狙い・内容（具体的な数値や事実を含める）")

class Agenda(BaseModel):
    plan: List[SlidePlan] = Field(..., description="プレゼンテーションの構成案一覧")

class SlideDetail(BaseModel):
    title: str = Field(..., description="スライドのタイトル")
    content: List[str] = Field(..., description="スライドの箇条書き内容（完結した文章）")

class Presentation(BaseModel):
    slides: List[SlideDetail] = Field(..., description="全スライドの詳細データ")
