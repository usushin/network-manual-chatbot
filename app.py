import streamlit as st
import os
import time
from pathlib import Path

# 環境変数を最初に読み込み（確実に）
from dotenv import load_dotenv
load_dotenv()

# デバッグ情報
print(f"🔍 起動時環境変数確認:")
print(f"   GROQ_API_KEY: {'設定済み' if os.getenv('GROQ_API_KEY') else '未設定'}")

# カスタムモジュールのインポート
from config import config
from src.document_processor import DocumentProcessor
from src.chatbot import NetworkManualChatbot
from src.logger import setup_logger, get_logger
from src.performance import get_performance_monitor, log_system_status

# ロガーの初期化
logger = setup_logger(log_dir=config.LOG_DIR, log_level=config.LOG_LEVEL)

# ページ設定
st.set_page_config(
    page_title="ネットワーク製品 Knowledge Database",
    page_icon="🌐",
    layout="wide"
)

# セッション状態の初期化
def initialize_session_state():
    """セッション状態を初期化"""
    default_states = {
        "chatbot": None,
        "chat_history": [],
        "vectorstore_loaded": False,
        "api_key_validated": False,
        "last_system_check": 0,
        "env_api_key_checked": False,  # 新規追加
        "default_api_key": ""          # 新規追加
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def validate_api_key(api_key: str) -> bool:
    """APIキーの妥当性をチェック"""
    if not api_key:
        return False
    if not api_key.startswith("gsk_"):
        st.error("❌ Groq APIキーは 'gsk_' で始まる必要があります")
        return False
    if len(api_key) < 20:
        st.error("❌ APIキーが短すぎます")
        return False
    return True

def show_system_status():
    """システム状態を表示"""
    current_time = time.time()
    
    # 10秒ごとにシステム状態をチェック
    if current_time - st.session_state.last_system_check > 10:
        log_system_status()
        st.session_state.last_system_check = current_time

def show_performance_stats():
    """パフォーマンス統計を表示"""
    with st.expander("📊 システム統計", expanded=False):
        monitor = get_performance_monitor()
        stats = monitor.get_all_stats()
        
        if stats:
            for func_name, func_stats in stats.items():
                st.write(f"**{func_name}**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("実行回数", func_stats['call_count'])
                with col2:
                    st.metric("平均実行時間", f"{func_stats['avg_execution_time']:.3f}秒")
                with col3:
                    st.metric("平均メモリ使用量", f"{func_stats['avg_memory_usage_mb']:.1f}MB")
        else:
            st.info("まだ統計データがありません")

def show_cache_stats():
    """キャッシュ統計を表示"""
    if st.session_state.chatbot and config.ENABLE_CACHE:
        cache_stats = st.session_state.chatbot.get_cache_stats()
        if cache_stats:
            st.write("**💾 キャッシュ統計**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("総リクエスト", cache_stats['total_requests'])
            with col2:
                st.metric("ヒット数", cache_stats['hits'])
            with col3:
                st.metric("ヒット率", f"{cache_stats['hit_rate']:.1f}%")
            with col4:
                st.metric("キャッシュファイル数", cache_stats['cache_files'])

def main():
    """メイン関数"""
    # セッション状態の初期化
    initialize_session_state()
    
    # 環境変数からAPIキーを自動設定（初回のみ）
    if not st.session_state.get("env_api_key_checked", False):
        env_api_key = os.getenv("GROQ_API_KEY")
        if env_api_key:
            st.session_state["default_api_key"] = env_api_key
            st.session_state.api_key_validated = True
            config.GROQ_API_KEY = env_api_key
            logger.info(f"環境変数からAPIキーを自動設定しました")
        else:
            st.session_state["default_api_key"] = ""
            logger.warning("環境変数にAPIキーが設定されていません")
        st.session_state["env_api_key_checked"] = True
    
    # システム状態の監視
    show_system_status()
    
    # タイトル
    st.title("🌐 ネットワーク製品 Knowledge Database")
    st.markdown("CISCO等のネットワーク機器に関する技術的な質問にお答えします。")
    
    # 設定の妥当性チェック（APIキーチェックを除外）
    config_error = config.validate()
    if config_error:
        st.error(f"⚠️ 設定エラー: {config_error}")
    
    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # APIキーの入力（デフォルト値を設定）
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            value=st.session_state.get("default_api_key", ""),
            help="Groq APIキーを入力してください（https://console.groq.com/keys で無料取得）"
        )
        
        # APIキーの設定と検証
        if api_key:
            if validate_api_key(api_key):
                os.environ["GROQ_API_KEY"] = api_key
                config.GROQ_API_KEY = api_key
                st.session_state.api_key_validated = True
                st.success("✅ APIキーが有効です")
            else:
                st.session_state.api_key_validated = False
        else:
            st.session_state.api_key_validated = False
            # 環境変数にAPIキーがある場合の表示
            if st.session_state.get("default_api_key"):
                st.info("💡 .envファイルからAPIキーを読み込み中...")
        
        st.divider()
        
        # モデル設定
        st.subheader("🤖 モデル設定")
        model_options = ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]
        selected_model = st.selectbox(
            "LLMモデル",
            model_options,
            index=model_options.index(config.MODEL_NAME) if config.MODEL_NAME in model_options else 0
        )
        
        temperature = st.slider(
            "Temperature（回答の創造性）",
            min_value=0.0,
            max_value=1.0,
            value=config.TEMPERATURE,
            step=0.1,
            help="低い値: より確実な回答、高い値: より創造的な回答"
        )
        
        st.divider()
        
        # PDFアップロード機能
        st.subheader("📄 マニュアルのアップロード")
        uploaded_files = st.file_uploader(
            "PDFファイルを選択",
            type="pdf",
            accept_multiple_files=True,
            help="複数のPDFファイルを同時にアップロード可能です"
        )
        
        # ファイル情報の表示
        if uploaded_files:
            st.write("**選択されたファイル:**")
            total_size = 0
            for file in uploaded_files:
                file_size_mb = len(file.getvalue()) / 1024 / 1024
                total_size += file_size_mb
                st.write(f"• {file.name} ({file_size_mb:.2f}MB)")
            st.write(f"**総サイズ:** {total_size:.2f}MB")
            
            if total_size > 100:
                st.warning("⚠️ 大きなファイルです。処理に時間がかかる可能性があります。")
        
        # 処理ボタン
        if uploaded_files and st.button("🔄 マニュアルを処理", type="primary"):
            if not st.session_state.api_key_validated:
                st.error("❌ 有効なAPIキーを入力してください")
            else:
                with st.spinner("PDFを処理中..."):
                    try:
                        # アップロードされたファイルを保存
                        manual_dir = Path("./data/manuals")
                        manual_dir.mkdir(parents=True, exist_ok=True)
                        
                        saved_files = []
                        for uploaded_file in uploaded_files:
                            file_path = manual_dir / uploaded_file.name
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            saved_files.append(file_path.name)
                            logger.info(f"ファイル保存: {file_path.name}")
                        
                        # ドキュメント処理
                        processor = DocumentProcessor()
                        vectorstore = processor.process_documents(str(manual_dir))
                        
                        # チャットボットの初期化（設定値を反映）
                        retriever = vectorstore.as_retriever(search_kwargs={"k": config.SEARCH_K})
                        st.session_state.chatbot = NetworkManualChatbot(
                            retriever, 
                            model_name=selected_model
                        )
                        st.session_state.vectorstore_loaded = True
                        
                        st.success(f"✅ マニュアルの処理が完了しました！ (ファイル数: {len(saved_files)})")
                        logger.info(f"マニュアル処理完了 - ファイル数: {len(saved_files)}")
                        
                    except Exception as e:
                        error_msg = f"処理エラー: {str(e)}"
                        st.error(f"❌ {error_msg}")
                        logger.error(error_msg)
        
        st.divider()
        
        # 既存のベクトルストアを読み込む
        st.subheader("💾 保存済みデータ")
        if st.button("📂 保存済みデータを読み込む"):
            if not st.session_state.api_key_validated:
                st.error("❌ 有効なAPIキーを入力してください")
            else:
                try:
                    with st.spinner("データを読み込み中..."):
                        processor = DocumentProcessor()
                        vectorstore_info = processor.get_vectorstore_info()
                        
                        if vectorstore_info["status"] == "not_found":
                            st.warning("⚠️ 保存済みデータが見つかりません")
                        elif vectorstore_info["status"] == "error":
                            st.error(f"❌ データ読み込みエラー: {vectorstore_info['error']}")
                        else:
                            vectorstore = processor.load_vectorstore()
                            retriever = vectorstore.as_retriever(search_kwargs={"k": config.SEARCH_K})
                            st.session_state.chatbot = NetworkManualChatbot(
                                retriever,
                                model_name=selected_model
                            )
                            st.session_state.vectorstore_loaded = True
                            
                            st.success(
                                f"✅ データを読み込みました！ "
                                f"(ドキュメント数: {vectorstore_info['document_count']}, "
                                f"サイズ: {vectorstore_info['size_mb']:.1f}MB)"
                            )
                            logger.info(f"ベクトルストア読み込み完了")
                            
                except Exception as e:
                    error_msg = f"読み込みエラー: {str(e)}"
                    st.error(f"❌ {error_msg}")
                    logger.error(error_msg)
        
        # 管理機能
        if st.session_state.vectorstore_loaded:
            st.divider()
            st.subheader("🔧 管理機能")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ 会話履歴をクリア"):
                    if st.session_state.chatbot:
                        st.session_state.chatbot.clear_memory()
                    st.session_state.chat_history = []
                    st.rerun()
            
            with col2:
                if st.button("💾 キャッシュをクリア") and config.ENABLE_CACHE:
                    if st.session_state.chatbot:
                        st.session_state.chatbot.clear_cache()
                    st.success("キャッシュをクリアしました")
        
        # システム情報の表示
        if config.DEBUG:
            st.divider()
            show_performance_stats()
            show_cache_stats()
    
    # メインコンテンツ
    if not st.session_state.api_key_validated:
        st.warning("⚠️ Groq APIキーを入力してください。無料で取得できます: https://console.groq.com/keys")
    elif not st.session_state.vectorstore_loaded:
        st.info("📄 サイドバーからPDFマニュアルをアップロードするか、保存済みデータを読み込んでください。")
        
        # 使用方法の説明
        with st.expander("📖 使用方法", expanded=True):
            st.markdown("""
            ### 🚀 クイックスタート
            
            1. **APIキーの設定** (サイドバー)
               - Groq API Key を入力してください
               - [こちら](https://console.groq.com/keys)で無料取得可能
            
            2. **マニュアルのアップロード**
               - PDFファイルを選択
               - 「マニュアルを処理」ボタンをクリック
            
            3. **質問の開始**
               - チャット入力欄に質問を入力
               - 技術的な質問に対して正確な回答を提供
            
            ### 💡 質問例
            - "VRRPの設定手順を教えてください"
            - "BGPの基本設定方法は？"
            - "show コマンドの使い方を説明してください"
            """)
    else:
        # チャット履歴の表示
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sources" in message and message["sources"]:
                    with st.expander("📄 参照元を表示"):
                        for i, source in enumerate(message["sources"], 1):
                            st.markdown(f"**{i}. {source['file']}** (ページ: {source['page']})")
                            st.markdown(f"```\n{source['content']}\n```")
        
        # ユーザー入力
        if prompt := st.chat_input("質問を入力してください..."):
            # 入力の妥当性チェック
            if len(prompt.strip()) < 3:
                st.error("❌ 質問は3文字以上入力してください")
                return
            
            # ユーザーメッセージを表示
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # アシスタントの回答を生成
            with st.chat_message("assistant"):
                with st.spinner("回答を生成中..."):
                    try:
                        start_time = time.time()
                        answer, sources = st.session_state.chatbot.ask(prompt)
                        processing_time = time.time() - start_time
                        
                        st.markdown(answer)
                        
                        # 処理時間とメタ情報の表示
                        if config.DEBUG:
                            st.caption(f"⏱️ 処理時間: {processing_time:.2f}秒 | 📄 参照元数: {len(sources)}")
                        
                        # ソース情報を表示
                        if sources:
                            with st.expander("📄 参照元を表示"):
                                for i, source in enumerate(sources, 1):
                                    st.markdown(f"**{i}. {source['file']}** (ページ: {source['page']})")
                                    st.markdown(f"```\n{source['content']}\n```")
                        else:
                            st.info("ℹ️ 関連する文書が見つかりませんでした")
                        
                        # ログ記録
                        logger.info(f"質問応答完了 - 処理時間: {processing_time:.2f}秒")
                        
                    except Exception as e:
                        error_msg = f"回答生成エラー: {str(e)}"
                        st.error(f"❌ {error_msg}")
                        logger.error(error_msg)
                        answer = "申し訳ございません。エラーが発生しました。しばらく待ってから再度お試しください。"
                        sources = []
            
            # 履歴に追加
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })

# フッター情報
def show_footer():
    """フッター情報を表示"""
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            f"""
            <div style='text-align: center'>
                <small>
                    ネットワーク製品 Knowledge Database v2.0<br>
                    Powered by LangChain & Groq (Llama 3) | 
                    モデル: {config.MODEL_NAME} | 
                    キャッシュ: {'有効' if config.ENABLE_CACHE else '無効'}
                </small>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # デバッグ情報
    if config.DEBUG:
        with st.expander("🔧 デバッグ情報", expanded=False):
            st.json({
                "config": {
                    "MODEL_NAME": config.MODEL_NAME,
                    "TEMPERATURE": config.TEMPERATURE,
                    "CHUNK_SIZE": config.CHUNK_SIZE,
                    "CHUNK_OVERLAP": config.CHUNK_OVERLAP,
                    "SEARCH_K": config.SEARCH_K,
                    "ENABLE_CACHE": config.ENABLE_CACHE
                },
                "session_state": {
                    "vectorstore_loaded": st.session_state.vectorstore_loaded,
                    "api_key_validated": st.session_state.api_key_validated,
                    "chat_history_length": len(st.session_state.chat_history),
                    "env_api_key_checked": st.session_state.get("env_api_key_checked", False)
                }
            })

if __name__ == "__main__":
    try:
        main()
        show_footer()
    except Exception as e:
        st.error(f"❌ アプリケーションエラー: {str(e)}")
        logger.error(f"アプリケーションエラー: {str(e)}")
        st.info("📋 詳細なエラー情報はログファイルを確認してください")

