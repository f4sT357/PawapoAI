import streamlit as st
from typing import List, Optional, Dict, Any
from schemas.models import SlidePlan, SlideDetail

class AppState:
    """
    Streamlitのセッション状態を一元管理するクラス
    """
    def __init__(self):
        # 内部状態のキー定義
        self._keys = {
            "plan": "plan",
            "slide_data": "slide_data",
            "context_text": "context_text",
            "topic": "topic",
            "slide_count": "slide_count",
            "points_per_slide": "points_per_slide",
            "char_limit": "char_limit"
        }

    def init_state(self):
        """初期状態の設定"""
        if self._keys["plan"] not in st.session_state:
            st.session_state[self._keys["plan"]] = []
        if self._keys["slide_data"] not in st.session_state:
            st.session_state[self._keys["slide_data"]] = []
        if self._keys["context_text"] not in st.session_state:
            st.session_state[self._keys["context_text"]] = ""

    @property
    def plan(self) -> List[SlidePlan]:
        # セッション状態から取得。なければ空リスト
        plan_raw = st.session_state.get(self._keys["plan"], [])
        # SlidePlanオブジェクトのリストとして扱う
        if plan_raw and isinstance(plan_raw[0], dict):
            return [SlidePlan(**item) for item in plan_raw]
        return plan_raw

    @plan.setter
    def plan(self, value: List[SlidePlan]):
        # 保存時は辞書形式に変換 (data_editorなどとの親和性のため)
        st.session_state[self._keys["plan"]] = [item.model_dump() if hasattr(item, "model_dump") else item for item in value]

    @property
    def slide_data(self) -> List[SlideDetail]:
        raw_data = st.session_state.get(self._keys["slide_data"], [])
        if raw_data and isinstance(raw_data[0], dict):
            return [SlideDetail(**item) for item in raw_data]
        return raw_data

    @slide_data.setter
    def slide_data(self, value: List[SlideDetail]):
        st.session_state[self._keys["slide_data"]] = [item.model_dump() if hasattr(item, "model_dump") else item for item in value]

    @property
    def context_text(self) -> str:
        return st.session_state.get(self._keys["context_text"], "")

    @context_text.setter
    def context_text(self, value: str):
        st.session_state[self._keys["context_text"]] = value

app_state = AppState()
