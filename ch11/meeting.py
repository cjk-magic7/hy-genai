# MoviePy 라이브러리를 사용하여 영상을 특정 시간의 길이로 다수의 영상 파일로 분할하는 기능.
# pip install moviepy langchain langchain-community openai streamlit 

import streamlit as st
import os 
import openai
import math
from moviepy.editor import VideoFileClip, AudioFileClip
# RecursiveCharacterTextSplitter 사용해 긴 문서를 분할
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter 
from langchain.document_loaders import TextLoader


# 영상을 interval(초) 길이로 분할
def split_file(filename, interval=180):
    split_filenames = []   # 분할된 파일명을 저장할 리스트
    # 파일 확장자에 따라 오디오 또는 비디오 클립을 로드합니다.
    if filename.endswith(('.mp3', '.m4a', '.wav')):
        clip = AudioFileClip(filename) # 오디오 파일인 경우
    else:
        clip = VideoFileClip(filename) # 비디오 파일인 경우
    
    # interval 단위로 분할된 영상 개수 계산.
    total = math.ceil(clip.duration / interval)
    st.write(str(interval) + '초 단위로 분할된 ' + str(total) + '개 영상을 생성합니다.')

    for part in range(total):
        # 시작 및 종료 시간을 계산합니다.
        start_time = part * interval
        end_time = min((part + 1) * interval, clip.duration)

        # interval 기준으로 파일을 자름
        new_clip = clip.subclip(start_time, end_time)

        # 새 파일 이름을 생성해 저장 
        new_filename = f"{filename.rsplit('.', 1)[0]}_part{part + 1}.{filename.rsplit('.', 1)[1]}"
        split_filenames.append(new_filename)

        # interval 단위로 분할한 비디오 및 오디오 파일 저장 
        if not filename.endswith(('.mp3', '.m4a', '.wav')):
            new_clip.write_videofile(new_filename, codec="libx264")
        else:
            new_clip.write_audiofile(new_filename)

        st.write(new_filename + ' 파일을 저장했습니다.')

    clip.close()
    # 분할된 파일명 리스트를 반환합니다.
    return split_filenames

# 회의 내용 요약
def summarize(client, text):
    response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """
                    회의 핵심 내용을 개조식으로 요약합니다. 
                    문장의 시작은 불렛포인트로 구성합니다.
                    """},
                    {"role": "user", "content": text}
                ]
            )
    return response.choices[0].message.content

# 특정 파일에서 STT를 통해 추출된 텍스트를 파일로 저장
def save_meeting(file_path, result):
    # 동일 파일이 존재하면 삭제
    if os.path.exists(file_path):
        os.remove(file_path)
        st.write(f"기존 파일을 삭제했습니다.")
    else:
        st.write(f"파일 '{file_path}'이(가) 존재하지 않습니다.")

    # 새 파일 생성
    with open(file_path, 'w') as file:
        file.write(result)
    st.write(f"'{file_path}'이(가) 생성되었습니다.")


# OpenAI API Key
client = openai.OpenAI(
    api_key = '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'
)

st.set_page_config(page_title="회의록 작성 인공지능!")
st.session_state.setdefault("meeting", None)
st.title("회의록 작성 인공지능!")

# 회의 파일 업로드
data = st.file_uploader("Upload File", 
                type=['webm', 'mp4', 'mpeg', 'mp3', 'm4a', 'wav'])

# 회의록 생성 버튼을 클릭
if st.button("회의록 생성") and data:
    with st.spinner('처리중...'):
        data_dir = 'data'  # data 디렉토리를 생성
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, data.name)

        # 업로드 파일을 data 디렉토리에 저장.
        with open(file_path, 'wb') as f:
            f.write(data.getbuffer())
        
        # 해당 디렉토리에 있는 영상 파일을 split_file() 함수를 이용해 분할
        split_filenames = split_file(file_path)

        result = ''

        # 분할한 파일에서 STT(whisper 사용)를 사용해 텍스트 추출
        for sub_file in split_filenames:
            with open(sub_file, 'rb') as audio_file:
                st.write(sub_file, '을 분석합니다.')
                st.session_state.meeting = client.audio.translations.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="text"
                            )
            # 각 영상에 대한 스크립트를 result 문자열에 누적하여 저장.
            # 즉, 영상 전체의 스크립트가 result 문자열에 저장.
            result += st.session_state.meeting

        # 영상의 전체 스크립트를 meeting.txt에 저장
        file_path = "./meeting.txt"
        save_meeting(file_path, result)
        st.write('영상내 음성 내용을 meeting.txt 파일로 저장합니다.')

        # Langchain의 RecursiveCharacterTextSplitter는 긴 문서를 특정 길이로 분할
        loader = DirectoryLoader('.', glob="*.txt", loader_cls=TextLoader)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)

        # 다수의 텍스트로 분할하여 texts라는 문자열 리스트에 저장
        texts = text_splitter.split_documents(documents)
        st.write('스크립트를 분할하였을 때 생긴 텍스트의 개수 :', len(texts))

        final_result = ''

        # 분할된 각 텍스트마다 ChatGPT를 이용하여 요약을 수행
        for t in texts:
            final_result += summarize(client, str(t))
            
        st.write('회의록')
        st.markdown(final_result)

