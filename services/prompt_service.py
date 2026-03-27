from typing import List, Optional
from utils.logger import logger

class PromptService:
    BASE_SYSTEM_PROMPT = """
あなたは専門的なプレゼンテーション資料作成のエキスパートです。
以下の点に注意して資料を作成してください：
1. 提供された資料（もしあれば）に基づき、正確な数値や固有名詞を含める
2. 資料にない情報は創作しないこと
3. 各スライドに具体的で分かりやすいポイントを含める
4. 専門用語も含めながら、全体として理解しやすい構成にする
    """

    TONE_PRESETS = {
        "business": "簡潔で論理的、語尾は「〜である」で統一",
        "impact": "結論を強調し、印象に残る表現を使う",
        "easy": "専門用語を避け、誰でも理解できる表現"
    }

    @staticmethod
    def get_agenda_prompt(topic: str, slide_count: int, custom_instruction: str, context: str) -> str:
        return f"""
プレゼンのテーマ: 「{topic}」
スライド枚数: {slide_count}枚

【ユーザー指示】
{custom_instruction}

【参考資料】
{context if context else "（指定なし）"}

【課題】
上記の情報を踏まえ、{slide_count}枚の構成案（アジェンダ）を作成してください。
各スライドの「タイトル」と「このスライドで説明すべき要点（具体的な数値・事実を含める）」をJSON形式で作成してください。

必ずJSON形式でのみ出力してください。
        """

    @staticmethod
    def get_slide_detail_prompt(
        title: str, 
        description: str, 
        points_count: int, 
        context: str, 
        prev_slide: Optional[str], 
        next_slide: Optional[str],
        total_slides: int,
        idx: int
    ) -> str:
        context_info = f"全体{total_slides}枚のプレゼンの{idx + 1}枚目です。"
        if prev_slide:
            context_info += f"\n前のスライド: 「{prev_slide}」"
        if next_slide:
            context_info += f"\n次のスライド: 「{next_slide}」"

        return f"""
スライドタイトル: {title}
このスライドの狙い: {description}

【前後の文脈】
{context_info}

【要件】
1. 箇条書きは{points_count}個作成
2. 各項目は「～により、～を実現している」という完結した文章（40～60文字程度）
3. 単なる単語ではなく、技術的な背景や数値の意味まで含める
4. 参考資料に記載されている数値・固有名詞を優先して使用
5. 前のスライドから自然に繋がるように、また次のスライドへの引き継ぎも意識してください。

【参考資料】
{context if context else "（指定なし）"}

【出力形式】
{{
  "title": "{title}",
  "content": ["完結した文章の第1ポイント", "完結した文章の第2ポイント", "..."]
}}

必ずJSON形式でのみ出力してください。
        """

    @staticmethod
    def get_rewrite_prompt(title: str, content: List[str], tone_key: str) -> str:
        tone_description = PromptService.TONE_PRESETS.get(tone_key, PromptService.TONE_PRESETS["business"])
        
        content_items = "\n".join([f"- {item}" for item in content])
        
        return f"""
以下のスライド内容をプレゼン用途として最適化（リライト）してください。

【現在の内容】
タイトル: {title}
箇条書き:
{content_items}

【指定トーン】
{tone_description}

【改善の目的】
- 日本語を自然で簡潔にする
- 語尾を統一する
- 冗長な表現を削除し、一目で内容が伝わるようにする
- プレゼンとして印象に残る表現に改善する

【重大な制約（厳守）】
- 情報の内容（事実）を追加・削除しないこと
- 数値や固有名詞は絶対に一字一句変更しないこと
- 元の意味を改変しないこと

【出力形式】
修正後の文章のみを以下のJSON形式で出力してください：
{{
  "title": "{title}",
  "content": ["修正後の文章1", "修正後の文章2", ...]
}}

必ずJSON形式でのみ出力してください。
        """

    @staticmethod
    def summarize_context(context: str, max_chars: int = 4000) -> str:
        """
        簡易的な要約（文字数制限）。
        TODO: 必要であればLLMを使った要約ロジックをここに追加する
        """
        if len(context) > max_chars:
            logger.info(f"Context exceeds {max_chars} chars. Truncating.")
            return context[:max_chars] + "...(以下略)"
        return context
