import streamlit as st
import os
# 유튜브 동영상을 다운로드하기 위한 라이브러리 pip install pytube
from pytube import YouTube   
from openai import OpenAI

# OpenAI API Key 값
client = OpenAI(
    api_key='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'
)

# https://platform.openai.com/docs/guides/speech-to-text/quickstart

# mp3 파일에서 자막 추출해 srt 형식으로 저장
def get_transcript(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            response_format="srt",
            file=audio_file
        )
        return transcript

# 주소를 입력받으면 유튜브 동영상(mp4)과 유튜브 동영상의 음성(mp3)을 추출하는 함수.
def get_audio_and_video(url):
    yt = YouTube(url)

    # 음성 추출
    audio = yt.streams.filter(only_audio=True).first()
    #audio_file = audio.download(output_path=".")
    audio_file = audio.download()
    base, ext = os.path.splitext(audio_file)
    new_audio_file = base + '.mp3'
    os.rename(audio_file, new_audio_file)

    # 영상 추출
    video = yt.streams.filter(file_extension='mp4').get_highest_resolution()
    video_file = video.download()

    # 파일의 크기를 측정하기 위한 코드
    audio_file = os.stat(new_audio_file)
    video_file = os.stat(video_file)

    return new_audio_file, video_file

st.title('유투브 영상 자막 추출기')

url = st.text_input('유투브 URL을 입력하세요.')

if st.button('다운로드'):
    if url:
        try:
            # get_audio_and_video 함수로부터 
            # 현재 코드가 실행되는 경로에 음성 파일(mp3), 영상 파일(mp4)을 저장
            audio_file, video_file = get_audio_and_video(url)
        
            # 자막 파일을 subtitle.srt 라는 이름으로 저장
            result = get_transcript(audio_file)
            subtitle_file = './subtitle.srt'
            with open(subtitle_file, 'w', encoding='utf-8') as file:
                file.write(result)

            st.success('다운로드를 완료했습니다!')
            
            # 화면에 자막 파일의 경로를 출력.
            subtitle_file_path = os.path.abspath(subtitle_file)
            st.markdown(f'자막파일 저장: `{subtitle_file_path}`')
          
            # 자막 파일을 읽어서 화면에 자막들을 출력
            with open(subtitle_file, 'r', encoding='utf-8') as file:
                subtitles = file.read()
                st.info(subtitles)

        except Exception as e:
            st.error(f'예외 발생: {e}')
            
            
#https://platform.openai.com/docs/tutorials/meeting-minutes