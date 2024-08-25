# 필요한 패키지들 import
import streamlit as st  # Streamlit 패키지 불러오기
from audiorecorder import audiorecorder  # 음성 녹음 기능을 위한 패키지
from openai import OpenAI  # OpenAI API 사용을 위한 패키지
import os  # 파일 처리를 위한 os 패키지
from datetime import datetime  # 시간 정보를 다루기 위한 datetime 패키지
import numpy as np  # 오디오 데이터를 비교하기 위한 numpy 패키지
import base64  # 음원 파일을 base64로 인코딩하기 위한 패키지
import requests  # HTTP 요청을 보내기 위한 requests 패키지
import json  # JSON 데이터를 다루기 위한 json 패키지
import re  # 정규표현식을 위한 re 패키지

# 음성을 텍스트로 변환하는 함수 정의
def convert_speech_to_text(audio_data, openai_client):
    # 음성 파일을 'speech_input.mp3'로 저장
    file_name = 'speech_input.mp3'
    with open(file_name, "wb") as audio_file:
        audio_file.write(audio_data.export().read())

    # 저장된 음성 파일을 열기
    with open(file_name, "rb") as audio_file:
        try:
            # OpenAI의 Whisper API를 사용하여 음성을 텍스트로 변환
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            # 변환이 완료되면 파일 삭제
            os.remove(file_name)
        except:
            transcription = 'API Key를 확인해주세요'
    return transcription

# 텍스트를 음성으로 변환하는 함수 정의
def convert_text_to_speech(response_text, openai_client):
    # OpenAI TTS 모델을 사용하여 텍스트를 음성으로 변환
    tts_response = openai_client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=response_text
    )
    output_file = "speech_output.mp3"
    tts_response.stream_to_file(output_file)

    # 변환된 음성 파일을 자동 재생하기 위해 base64로 인코딩
    with open(output_file, "rb") as audio_file:
        audio_data = audio_file.read()
        base64_audio = base64.b64encode(audio_data).decode()
        audio_html = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{base64_audio}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    # 재생 후 파일 삭제
    os.remove(output_file)

# GPT-3.5 모델을 사용하여 질문에 대한 답변을 얻는 함수 정의
def get_gpt_response(prompt_list, openai_client):
    response = openai_client.chat.completions.create(model='gpt-3.5-turbo', messages=prompt_list)
    return response.choices[0].message.content

# 날씨 정보를 가져오는 함수 정의
def get_weather_info(city_name, api_key):
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = base_url + "q=" + city_name + "&appid=" + api_key + "&units=metric&lang=kr"
    response = requests.get(complete_url)
    weather_data = response.json()
    
    if weather_data["cod"] != "404":
        main = weather_data["main"]
        weather = weather_data["weather"][0]
        weather_description = weather["description"]
        temperature = main["temp"]
        humidity = main["humidity"]
        weather_response = f"현재 {city_name}의 날씨는 {weather_description}이며, 온도는 {temperature}도, 습도는 {humidity}%입니다."
    else:
        weather_response = "도시 정보를 찾을 수 없습니다. 도시 이름을 확인해주세요."
    
    return weather_response

# 사용자의 질문에서 도시 이름을 추출하는 함수 정의
def extract_city_name(user_question):
    # 정규 표현식을 사용하여 사용자가 말한 도시 이름 추출 (예: "서울")
    city_name_match = re.search(r'지금\s*(.*?)\s*의\s*날씨', user_question)
    if city_name_match:
        return city_name_match.group(1)
    return None

# Streamlit 페이지 설정
st.set_page_config(
    page_title="인공지능 비서 자비스(날씨 추가)",
    layout="wide"
)

# session state 초기화
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

if "previous_audio" not in st.session_state:
    st.session_state["previous_audio"] = []

if "prompts" not in st.session_state:
    st.session_state["prompts"] = [{"role": "system", "content": 'You are a thoughtful assistant. Respond to all input in 25 words and answer in korean'}]

# 페이지 제목 설정
st.header('인공지능 비서 자비스입니다')
st.subheader('제가 무엇을 도와드릴까요? 🤖')
st.markdown('---')

# OpenAI API 키 지정
openai_client = OpenAI(
    api_key = "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"
)

# OpenWeatherMap API 키 지정
weather_api_key = "a525268a4f284f71278ab51ab757924b"  # 여기에 실제 OpenWeatherMap API 키를 입력하세요

start_flag = False

# Streamlit 레이아웃 설정
left_column, right_column = st.columns(2)
with left_column:
    # 음성 녹음 기능
    recorded_audio = audiorecorder("질문하기", "듣고 있는 중입니다...")
    if len(recorded_audio) > 0 and not np.array_equal(recorded_audio, st.session_state["previous_audio"]):
        # 녹음된 음성을 재생
        st.audio(recorded_audio.export().read())

        # 녹음된 음성을 텍스트로 변환
        user_question = convert_speech_to_text(recorded_audio, openai_client)

        # 대화 내용을 기록하기 위해 현재 시간을 가져오기
        current_time = datetime.now().strftime("%H:%M")
        st.session_state["conversation"] = st.session_state["conversation"] + [("user", current_time, user_question)]
        
        # GPT 모델에 입력할 프롬프트 업데이트
        st.session_state["prompts"] = st.session_state["prompts"] + [{"role": "user", "content": user_question}]
        
        # 현재 녹음된 음성을 저장하여 다음 녹음과 비교
        st.session_state["previous_audio"] = recorded_audio
        start_flag = True

with right_column:
    # 대화 기록을 위한 공간
    st.image('ai.png', width=100)
    st.subheader('대화기록 ⌨')
    if start_flag:
        # GPT 모델을 사용하여 답변 얻기
        ai_response = get_gpt_response(st.session_state["prompts"], openai_client)
        
        # 사용자가 날씨 정보를 요청했는지 확인
        city_name = extract_city_name(user_question)
        if city_name:
            # OpenWeatherMap API를 사용하여 날씨 정보 가져오기
            ai_response = get_weather_info(city_name, weather_api_key)

        # 프롬프트 업데이트
        st.session_state["prompts"] = st.session_state["prompts"] + [{"role": "assistant", "content": ai_response}]
        
        # 대화 기록 업데이트
        current_time = datetime.now().strftime("%H:%M")
        st.session_state["conversation"] = st.session_state["conversation"] + [("bot", current_time, ai_response)]

        # 대화 기록을 채팅 형식으로 표시
        for sender, time, message in st.session_state["conversation"]:
            if sender == "user":
                st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                st.write("")
            else:
                st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                st.write("")
        
        # TTS를 사용하여 텍스트를 음성으로 변환 및 재생
        convert_text_to_speech(ai_response, openai_client)
