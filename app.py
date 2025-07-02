import streamlit as st
import os
from dotenv import load_dotenv
from src.document_processor import DocumentProcessor
from src.chatbot import NetworkManualChatbot

# 環境変数の読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="ネットワーク機器マニュアル チャットボット",
    page_icon="🌐",
    layout="wide"
)

# セッション状態の初期化
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "vectorstore_loaded" not in st.session_state:
    st.session_state.vectorstore_loaded = False

# タイトル
st.title("🌐 ネットワーク機器マニュアル チャットボット")
st.markdown("CISCO等のネットワーク機器に関する技術的な質問にお答えします。")

# サイドバー
with st.sidebar:
    st.header("設定")
    
    # APIキーの入力
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        value=os.getenv("GROQ_API_KEY", ""),
        help="Groq APIキーを入力してください（https://console.groq.com/keys で無料取得）"
    )
    
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    
    st.divider()
    
    # PDFアップロード機能
    st.subheader("マニュアルのアップロード")
    uploaded_files = st.file_uploader(
        "PDFファイルを選択",
        type="pdf",
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("マニュアルを処理"):
        with st.spinner("PDFを処理中..."):
            # アップロードされたファイルを保存
            manual_dir = "./data/manuals"
            os.makedirs(manual_dir, exist_ok=True)
            
            for uploaded_file in uploaded_files:
                file_path = os.path.join(manual_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
            # ドキュメント処理
            processor = DocumentProcessor()
            vectorstore = processor.process_documents(manual_dir)
            
            # チャットボットの初期化
            retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
            st.session_state.chatbot = NetworkManualChatbot(retriever)
            st.session_state.vectorstore_loaded = True
            
            st.success("マニュアルの処理が完了しました！")
    
    st.divider()
    
    # 既存のベクトルストアを読み込む
    if st.button("保存済みデータを読み込む"):
        try:
            processor = DocumentProcessor()
            vectorstore = processor.load_vectorstore()
            retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
            st.session_state.chatbot = NetworkManualChatbot(retriever)
            st.session_state.vectorstore_loaded = True
            st.success("データを読み込みました！")
        except Exception as e:
            st.error(f"データの読み込みに失敗しました: {str(e)}")
    
    # 会話履歴のクリア
    if st.button("会話履歴をクリア"):
        if st.session_state.chatbot:
            st.session_state.chatbot.clear_memory()
        st.session_state.chat_history = []
        st.rerun()

# メインコンテンツ
if not api_key:
    st.warning("⚠️ Groq APIキーを入力してください。無料で取得できます: https://console.groq.com/keys")
    # テスト用：一時的にAPIキーなしでも進められるようにする
    st.info("💡 テスト用：APIキーなしでもPDF処理までは可能です")
elif not st.session_state.vectorstore_loaded:
    st.info("📄 サイドバーからPDFマニュアルをアップロードするか、保存済みデータを読み込んでください。")
else:
    # チャット履歴の表示
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("参照元"):
                    for source in message["sources"]:
                        st.markdown(f"**ファイル:** {source['file']} (ページ: {source['page']})")
                        st.markdown(f"内容: {source['content']}")
    
    # ユーザー入力
    if prompt := st.chat_input("質問を入力してください..."):
        # ユーザーメッセージを表示
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # アシスタントの回答を生成
        with st.chat_message("assistant"):
            with st.spinner("回答を生成中..."):
                answer, sources = st.session_state.chatbot.ask(prompt)
                st.markdown(answer)
                
                # ソース情報を表示
                if sources:
                    with st.expander("参照元"):
                        for source in sources:
                            st.markdown(f"**ファイル:** {source['file']} (ページ: {source['page']})")
                            st.markdown(f"内容: {source['content']}")
        
        # 履歴に追加
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

# フッター
st.divider()
st.markdown(
    """
    <div style='text-align: center'>
        <small>技術サポートチャットボット v1.0 | Powered by LangChain & Groq (Llama 3)</small>
    </div>
    """,
    unsafe_allow_html=True
)