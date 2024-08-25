# youtube_summarizer.py
# pip install tiktoken
# https://www.youtube.com/watch?v=8jPQjjsBbIc
import streamlit as st
import re
import os
import yt_dlp
import openai
from typing import Dict, Any
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI

# 설정 상수
OPENAI_API_KEY = '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'  # 주의: 실제 사용 시 환경 변수로 관리하는 것이 안전합니다
MODEL_NAME = "gpt-3.5-turbo"  # 사용할 OpenAI 모델 이름
WHISPER_MODEL = "whisper-1"  # 음성 인식에 사용할 Whisper 모델 이름

# OpenAI 클라이언트 초기화
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_audio(url: str) -> str:
    """YouTube 비디오에서 오디오를 다운로드합니다."""
    ydl_opts: Dict[str, Any] = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(title)s.%(ext)s',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filename)
        new_filename = f"{base}.mp3"
    
    return new_filename

def get_transcribe(file_path: str) -> str:
    """OpenAI의 Whisper 모델을 사용하여 오디오 파일을 텍스트로 변환합니다."""
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            response_format="text",
            file=audio_file
        )
    return transcript

def translate_and_summarize(text: str) -> str:
    """OpenAI의 채팅 모델을 사용하여 텍스트를 번역하고 요약합니다."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "당신은 영한 번역가이자 요약가입니다. 들어오는 모든 입력을 한국어로 번역하고 불렛 포인트 요약을 사용합니다."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

def setup_langchain():
    """LangChain 요약 체인을 설정합니다."""
    llm = ChatOpenAI(model_name=MODEL_NAME, openai_api_key=OPENAI_API_KEY)
    
    map_prompt = PromptTemplate(
        template="Summarize the following transcript in English:\n```{text}```",
        input_variables=["text"]
    )
    
    combine_prompt = PromptTemplate(
        template="Combine the following summaries into a concise 10-sentence summary in English:\n```{text}```",
        input_variables=["text"]
    )
    
    return load_summarize_chain(llm, chain_type="map_reduce", verbose=False,
                                map_prompt=map_prompt, combine_prompt=combine_prompt)

def youtube_url_check(url: str) -> bool:
    """입력된 URL이 유효한 YouTube URL인지 확인합니다."""
    pattern = r'^https:\/\/(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)(\&ab_channel=[\w\d]+)?$'
    return re.match(pattern, url) is not None

def display_video(url: str) -> None:
    """Streamlit 앱에 YouTube 비디오를 표시합니다."""
    width = 50
    side = width / 2
    _, container, _ = st.columns([side, width, side])
    container.video(data=url)

def process_video(url: str) -> None:
    """YouTube 비디오를 처리합니다: 오디오 다운로드, 텍스트 변환, 요약, 번역"""
    try:
        audio_file = get_audio(url)
        transcript = get_transcribe(audio_file)

        st.subheader("영어 요약본")
        if st.session_state["flag"]:
            chain = setup_langchain()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=0)
            documents = text_splitter.create_documents([transcript])
            st.session_state["summarize"] = chain.run(documents)
            st.session_state["flag"] = False

        st.success(st.session_state["summarize"])

        translation = translate_and_summarize(st.session_state["summarize"])
        st.subheader("한글 요약본")
        st.info(translation)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
    finally:
        if 'audio_file' in locals():
            os.remove(audio_file)

def main():
    st.set_page_config(page_title="YouTube 요약 서비스", layout="wide")

    if "flag" not in st.session_state:
        st.session_state["flag"] = True
    if "summarize" not in st.session_state:
        st.session_state["summarize"] = ""

    st.header("YouTube 요약 서비스")
    youtube_video_url = st.text_input("YouTube URL을 입력해주세요:", placeholder="https://www.youtube.com/watch?v=**********")
    st.markdown('---')

    if len(youtube_video_url) > 2:
        if not youtube_url_check(youtube_video_url):
            st.error("유효하지 않은 YouTube URL입니다. 확인 후 다시 시도해주세요.")
        else:
            display_video(youtube_video_url)
            process_video(youtube_video_url)

if __name__ == "__main__":
    main()
