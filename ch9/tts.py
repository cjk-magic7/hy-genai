import os
import streamlit as st
from openai import OpenAI
import openai

# OpenAI API Key 값
client = OpenAI(
    api_key="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"
)

st.title("인공지능 성우 서비스")

# OpenAI API를 사용하여 인공지능 성우 서비스를 구현해보자.
# 인공지능 성우 선택 박스를 생성.
# 공식 문서 참고: https://platform.openai.com/docs/guides/text-to-speech
options = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
selected_option = st.selectbox("성우 선택:", options)

# 생성할 음성 스크립트를 입력하는 텍스트 상자
default_text = '안녕하세요. 저는 인공지능 성우입니다.'
prompt = st.text_area("스크립트 입력", value=default_text, height=200)

# Generate Audio 버튼을 클릭하면 True가 되면서 if문 실행.
if st.button("음성 파일 생성"):

    # 텍스트로부터 음성을 생성.
    response = client.audio.speech.create(
        model="tts-1",  # tts-1-hd
        voice=selected_option,
        input=prompt,
    )

    # 음성을 mp3 파일로 저장. 코드가 있는 경로에 파일이 생성된다.
    content = response.content

    with open("temp_audio.mp3", "wb") as audio_file:
        audio_file.write(content)

    # mp3 파일을 재생.
    st.audio("temp_audio.mp3", format="audio/mp3")