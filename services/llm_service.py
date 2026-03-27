import json
import re
import time
from typing import Type, TypeVar, Any, Optional
from pydantic import BaseModel, ValidationError
from openai import OpenAI
from utils.logger import logger

T = TypeVar("T", bound=BaseModel)

class LLMService:
    def __init__(self, base_url: str = "http://localhost:1234/v1", api_key: str = "lm-studio"):
        self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=600.0)

    def extract_json(self, text: str) -> str:
        """文字列からJSON部分を抽出する（正規表現を使用）"""
        # ```json ... ``` 形式を優先的に検索
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        
        # ``` ... ``` 形式を検索
        code_match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # 最初と最後の { } を探す
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            return brace_match.group(0).strip()
            
        return text.strip()

    def call_llm(
        self, 
        prompt: str, 
        response_model: Type[T], 
        system_prompt: str = "あなたは正確なアシスタントです。必ずJSON形式で回答してください。",
        model: str = "local-model",
        temperature: float = 0.3,
        max_retries: int = 3
    ) -> Optional[T]:
        """
        LLMを呼び出し、結果をPydanticモデルでバリデーションして返す
        """
        # PydanticモデルからJSONスキーマを生成（LM StudioのGuided JSON用）
        schema = response_model.model_json_schema()

        for attempt in range(max_retries):
            try:
                logger.info(f"LLM呼び出し開始 (試行 {attempt + 1}/{max_retries}) - Prompt: {prompt[:50]}...")
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    # LM Studio (LocalAI/vLLM系) での動的スキーマ注入
                    extra_body={
                        "guided_json": schema
                    },
                    temperature=temperature,
                )
                
                result_text = response.choices[0].message.content
                if not result_text:
                    raise ValueError("空のレスポンスを受け取りました")

                logger.debug(f"LLM Raw Response: {result_text}")
                
                json_str = self.extract_json(result_text)
                data = json.loads(json_str)
                
                # Pydanticによるバリデーション
                validated_data = response_model.model_validate(data)
                logger.info("LLMレスポンスのバリデーションに成功しました")
                return validated_data

            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"パース/バリデーションエラー (試行 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"{wait_time}秒待機して再試行します...")
                    time.sleep(wait_time)
                else:
                    logger.error("最大リトライ回数に達しました (パース失敗)")
            
            except Exception as e:
                logger.error(f"予期しないエラー (試行 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    logger.error("最大リトライ回数に達しました")
        
        return None
