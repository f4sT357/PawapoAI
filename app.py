import streamlit as st
import io
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# カスタムモジュールのインポート
from schemas.models import Agenda, SlideDetail, SlidePlan
from services.llm_service import LLMService
from services.prompt_service import PromptService
from services.file_service import FileService
from services.pptx_service import PPTXService
from core.state import app_state
from utils.logger import logger

# --- アプリケーション初期設定 ---
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
TEMPLATES_DIR = APP_DIR / "templates"

# サービスと状態の初期化
file_service = FileService(DATA_DIR, TEMPLATES_DIR)
prompt_service = PromptService()
app_state.init_state()

# --- サイドバー設定 ---
st.set_page_config(page_title="Pro PPTX Generator", layout="wide")
st.sidebar.title("🛠️ LLM 設定")

# モデル一覧の取得
@st.cache_data(ttl=60)
def get_models(url):
    try:
        # 一時的なクライアントでモデル一覧を取得
        temp_llm = LLMService(base_url=url)
        return [m.id for m in temp_llm.client.models.list().data]
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        return ["local-model", "⚠️ 接続エラー (URLを確認してください)"]

base_url = st.sidebar.text_input("Server URL", "http://localhost:1234/v1")
llm_service = LLMService(base_url=base_url)

# URLを引数に渡してキャッシュを連動させる
models = get_models(base_url)
selected_model = st.sidebar.selectbox("使用モデル", models)

if "接続エラー" in selected_model:
    st.sidebar.error("LM Studioとの接続に失敗しました。以下の点を確認してください：\n1. LM Studioが起動しているか\n2. Server ONになっているか\n3. URLが正しいか")

# --- ファイル管理 UI ---
with st.sidebar.expander("📂 参考資料とテンプレート", expanded=False):
    st.info("保存済みファイルを選択、または新規アップロードしてください。")
    
    # テンプレート選択
    st.subheader("🎨 テンプレート (.pptx)")
    template_files = file_service.get_files_in_directory(TEMPLATES_DIR)
    selected_template_name = st.selectbox("保存済みテンプレート", ["(なし)"] + template_files)
    
    uploaded_template = st.file_uploader("新規テンプレートをアップロード", type="pptx")
    if uploaded_template:
        saved_path = file_service.save_uploaded_file(uploaded_template, TEMPLATES_DIR)
        if saved_path:
            st.success(f"✅ {uploaded_template.name} を保存しました")
            st.rerun()

    # 資料選択
    st.subheader("📚 参考資料 (PDF/TXT/HTML)")
    ref_files = file_service.get_files_in_directory(DATA_DIR)
    selected_ref_name = st.selectbox("保存済み資料", ["(なし)"] + ref_files)
    
    uploaded_ref = st.file_uploader("新規資料をアップロード", type=["pdf", "txt", "html", "htm"])
    if uploaded_ref:
        saved_path = file_service.save_uploaded_file(uploaded_ref, DATA_DIR)
        if saved_path:
            st.success(f"✅ {uploaded_ref.name} を保存しました")
            st.rerun()

# 最終的な資料・テンプレートパスの確定
final_template_path = TEMPLATES_DIR / selected_template_name if selected_template_name != "(なし)" else None
final_ref_source = DATA_DIR / selected_ref_name if selected_ref_name != "(なし)" else None

# --- メイン UI ---
st.title("🚀 Pro PPTX Generator v2")
st.markdown("### 「よく動く試作品」から「壊れないプロダクト」へ。")

with st.expander("📝 プレゼン基本情報の入力", expanded=True):
    topic = st.text_input("プレゼンのメインテーマ", "AIの歴史について")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        slide_count = st.number_input("スライド枚数", min_value=3, max_value=30, value=10)
    with col2:
        points_per_slide = st.number_input("1スライドの箇条書き数", min_value=2, max_value=10, value=5)
    with col3:
        char_limit = st.number_input("1箇条書きの文字数目安", min_value=10, max_value=200, value=50, step=10)
    
    custom_instruction = st.text_area(
        "AIへの追加指示（役割・制約）",
        value="あなたは専門的なITコンサルタントです。ビジネス視点でのメリットや課題も考慮してください。",
        height=100
    )

# --- フェーズ1: 構成案の生成 ---
st.subheader("📋 フェーズ1：構成案（アジェンダ）の作成")

if st.button("📌 ステップ1：構成案を生成", type="primary"):
    context_text = ""
    if final_ref_source:
        with st.status("参考資料を解析中...", expanded=False):
            context_text = file_service.extract_text(final_ref_source)
            context_text = prompt_service.summarize_context(context_text) # 要約/制限
            app_state.context_text = context_text
    
    plan_prompt = prompt_service.get_agenda_prompt(topic, slide_count, custom_instruction, context_text)
    
    with st.status("構成案を企画中...", expanded=True) as status:
        try:
            agenda_data = llm_service.call_llm(
                prompt=plan_prompt,
                response_model=Agenda,
                system_prompt=prompt_service.BASE_SYSTEM_PROMPT,
                model=selected_model
            )
            
            if agenda_data:
                app_state.plan = agenda_data.plan
                status.update(label="✅ 構成案の作成が完了しました！", state="complete")
            else:
                st.error("❌ 構成案の生成に失敗しました。リトライするかモデルを確認してください。")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

# 構成案の編集
if app_state.plan:
    st.write("作成された構成案を確認・編集してください：")
    edited_plan_dict = st.data_editor(
        [p.model_dump() for p in app_state.plan],
        use_container_width=True,
        num_rows="dynamic"
    )
    # 編集結果をステートに戻す
    app_state.plan = [SlidePlan(**p) for p in edited_plan_dict]

    # --- フェーズ2: スライド詳細の生成 ---
    st.subheader("🚀 フェーズ2：スライド詳細の生成")
    
    if st.button("🔥 ステップ2：全スライドを並列生成", type="primary"):
        results = []
        progress_bar = st.progress(0.0)
        
        # 並列生成用のワーカー関数
        def generate_single_slide(args):
            idx, row, prev_title, next_title = args
            prompt = prompt_service.get_slide_detail_prompt(
                title=row.title,
                description=row.description,
                points_count=points_per_slide,
                context=app_state.context_text,
                prev_slide=prev_title,
                next_slide=next_title,
                total_slides=len(app_state.plan),
                idx=idx
            )
            data = llm_service.call_llm(
                prompt=prompt,
                response_model=SlideDetail,
                system_prompt=prompt_service.BASE_SYSTEM_PROMPT,
                model=selected_model
            )
            if not data:
                # 失敗時はプレースホルダー
                return SlideDetail(title=row.title, content=["【生成失敗】再生成ボタンを押してください。"])
            return data

        # パラメータセットの作成
        plan_list = app_state.plan
        tasks = []
        for i, row in enumerate(plan_list):
            prev_t = plan_list[i-1].title if i > 0 else None
            next_t = plan_list[i+1].title if i < len(plan_list)-1 else None
            tasks.append((i, row, prev_t, next_t))

        with st.status("☕ 全スライドを並列生成中（高速化モード）...", expanded=True) as status:
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 非同期で実行し、完了したものから表示
                for i, result in enumerate(executor.map(generate_single_slide, tasks)):
                    results.append(result)
                    progress_bar.progress((i + 1) / len(tasks))
                    st.write(f"✅ {i+1}/{len(tasks)}枚目: 「{result.title}」完了")
            
            app_state.slide_data = results
            status.update(label="✅ 全スライドの生成が完了しました！", state="complete")

# --- フェーズ3: 確認・編集・ダウンロード ---
if app_state.slide_data:
    st.subheader("✨ フェーズ3：推敲と最終調整")
    
    # --- AI リライト セクション ---
    with st.expander("🤖 AI による最終推敲（ブラッシュアップ）", expanded=True):
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            tone_key = st.radio(
                "リライトのトーンを選択",
                options=list(prompt_service.TONE_PRESETS.keys()),
                format_func=lambda x: f"**{x.capitalize()}**: {prompt_service.TONE_PRESETS[x]}",
                index=0,
                horizontal=True
            )
        
        with col_t2:
            st.write("") # スペース調整
            if st.button("🚀 全スライドを一括リライト", type="primary", use_container_width=True):
                # 現在のデータを「オリジナル」として保存（差分表示用）
                if "original_slide_data" not in st.session_state:
                    st.session_state.original_slide_data = [s.model_dump() for s in app_state.slide_data]
                
                new_results = []
                progress_bar = st.progress(0.0)
                
                def rewrite_worker(args):
                    idx, slide_detail = args
                    prompt = prompt_service.get_rewrite_prompt(
                        slide_detail.title, slide_detail.content, tone_key
                    )
                    return llm_service.call_llm(
                        prompt, SlideDetail, prompt_service.BASE_SYSTEM_PROMPT, selected_model
                    )

                tasks = list(enumerate(app_state.slide_data))
                
                with st.status("💎 日本語を美化しています...", expanded=True) as status:
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        for i, res in enumerate(executor.map(rewrite_worker, tasks)):
                            if res:
                                new_results.append(res)
                            else:
                                new_results.append(app_state.slide_data[i])
                            progress_bar.progress((i + 1) / len(tasks))
                    
                    app_state.slide_data = new_results
                    status.update(label="✅ 全リライトが完了しました！差分を確認してください。", state="complete")

    # プレビューと個別再生成
    tabs = st.tabs([f"スライド {i+1}" for i in range(len(app_state.slide_data))])
    
    original_data = st.session_state.get("original_slide_data")

    for i, (tab, slide) in enumerate(zip(tabs, app_state.slide_data)):
        with tab:
            col_l, col_r = st.columns([3, 1])
            with col_l:
                st.write(f"### {slide.title}")
                
                # 差分表示のロジック
                if original_data and i < len(original_data):
                    old_slide = original_data[i]
                    # タイトルの変更チェック
                    if old_slide['title'] != slide.title:
                        st.markdown(f"~~{old_slide['title']}~~")
                        st.markdown(f"**{slide.title}**")
                    
                    # コンテンツの比較
                    for idx, new_p in enumerate(slide.content):
                        old_p = old_slide['content'][idx] if idx < len(old_slide['content']) else None
                        if old_p and old_p != new_p:
                            st.error(f"- {old_p}")
                            st.success(f"+ {new_p}")
                        else:
                            st.write(f"- {new_p}")
                else:
                    # 通常表示
                    for point in slide.content:
                        st.write(f"- {point}")
            
            with col_r:
                if st.button(f"🔄 再生成", key=f"regen_{i}"):
                    row = app_state.plan[i]
                    prev_t = app_state.plan[i-1].title if i > 0 else None
                    next_t = app_state.plan[i+1].title if i < len(app_state.plan)-1 else None
                    
                    with st.spinner("単一スライド再生成中..."):
                        prompt = prompt_service.get_slide_detail_prompt(
                            row.title, row.description, points_per_slide, 
                            app_state.context_text, prev_t, next_t, 
                            len(app_state.plan), i
                        )
                        new_data = llm_service.call_llm(
                            prompt, SlideDetail, prompt_service.BASE_SYSTEM_PROMPT, selected_model
                        )
                        if new_data:
                            current_slides = app_state.slide_data
                            current_slides[i] = new_data
                            app_state.slide_data = current_slides
                            st.success("再生成完了！")
                            st.rerun()

    st.divider()
    
    # 全体編集エディタ
    st.write("### 📝 テキストの一括微調整")
    final_edit_data = st.data_editor(
        [s.model_dump() for s in app_state.slide_data],
        use_container_width=True
    )
    
    if st.button("📦 PowerPoint を構築する", type="primary"):
        # 編集結果を反映
        app_state.slide_data = [SlideDetail(**s) for s in final_edit_data]
        
        try:
            pptx_bytes = PPTXService.create_pptx_with_template(
                [s.model_dump() for s in app_state.slide_data],
                str(final_template_path) if final_template_path else None
            )
            
            st.download_button(
                label="📥 ファイルをダウンロード (.pptx)",
                data=pptx_bytes,
                file_name=f"{topic}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
            st.balloons()
        except Exception as e:
            st.error(f"PPTX構築エラー: {e}")