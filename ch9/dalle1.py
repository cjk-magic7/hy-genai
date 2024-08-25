import streamlit as st
import io
import base64
from openai import OpenAI
from PIL import Image

# OpenAI API Key 값
client = OpenAI(
    api_key = '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' 
)

def get_image(prompt):
    # DALLE로부터 Base64 형태의 이미지를 얻음
    response = get_image_info(prompt) 
    # Base64로 쓰여진 데이터를 이미지 형태로 변환
    image_data = base64.b64decode(response) 
    # 컴퓨터에서 이미지를 볼 수 있도록 설정
    image = Image.open(io.BytesIO(image_data)) 
    return image

# OpenAI API를 사용하여 인공지능 화가 서비스
# 공식 문서 참고: https://platform.openai.com/docs/guides/images/introduction
# DALLE가 이미지를 반환하는 함수.
def get_image_info(prompt): 
    response = client.images.generate(
    model="dall-e-3", # 모델은 DALLE 버전3 사용
    prompt=prompt, # 사용자의 프롬프트
    size="1024x1024", # 이미지의 크기
    quality="standard", # 이미지 퀄리티는 '표준'
    response_format='b64_json', # 이때 Base64 형태의 이미지를 전달한다.
    n=1,
    )
    return response.data[0].b64_json

st.title("인공지능 화가 서비스")

input_text = st.text_area("원하는 이미지를 글로 설명해 주세요!", height=200)

# 그리기 버튼 설정
if st.button("그리기"):

    # 이미지 프롬프트가 작성된 경우 이미지를 생성
    if input_text:
        try:
            # 이미지를 생성하는 함수를 호출
            image = get_image(input_text)

            # st.image()를 통해 이미지 출력
            st.image(image)
        except:
            st.error("요청 오류가 발생했습니다")
    # 만약 이미지 프롬프트가 작성되지 않았다면
    else:
        st.warning("텍스트를 입력하세요")