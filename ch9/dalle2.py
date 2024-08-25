import streamlit as st
import io
import base64
from openai import OpenAI
from PIL import Image

# OpenAI API Key 값
client = OpenAI(
    api_key = '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' 
)

# OpenAI API를 사용하여 인공지능 화가 서비스
# 공식 문서 참고: https://platform.openai.com/docs/guides/images/introduction

# 이미지를 RGBA 형식으로 변환하는 함수
def convert_to_rgba(image_path):
    image = Image.open(image_path)
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    return image


def get_image_info(): 
    # 이미지를 변환하고 저장
    input_image_path = "sunlit_lounge.png"
    mask_image_path = "mask.png"
    converted_image_path = "converted_sunlit_lounge.png"
    converted_mask_image_path = "converted_mask.png"

    converted_image = convert_to_rgba(input_image_path)
    converted_image.save(converted_image_path)
    converted_image = convert_to_rgba(mask_image_path)
    converted_image.save(converted_mask_image_path)
    
    try:
        response = client.images.edit(
        model="dall-e-2",
        image=open("converted_sunlit_lounge.png", "rb"),
        mask=open("converted_mask.png", "rb"),
        prompt="A sunlit indoor lounge area with a pool containing a flamingo",
        n=1,
        size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        print(f"Unexpected Error: {e}")

st.title("인공지능 화가 서비스 - 일부 영역 새로 그리기")

# Painting이라는 버튼을 클릭하면 True
if st.button("다시 그리기"):
    dalle_image = get_image_info()
    st.image(dalle_image)

