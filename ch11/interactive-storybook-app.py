import os
import uuid
import io
from PIL import Image
import base64
import streamlit as st
from openai import OpenAI

# OpenAI 클라이언트 설정
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 기본 페이지 설정
st.set_page_config(
    page_title="🌈 어린이 동화책 서비스",
    layout='wide',
    menu_items={
        'About': "어린이 동화책은 GPT-4o와 DALL-E를 사용한 인터랙티브 스토리북 경험입니다."
    },
    initial_sidebar_state='expanded'
)

st.title("🌈 어린이 동화책 서비스")

# 세션 상태 초기화
if 'data_dict' not in st.session_state:
    st.session_state['data_dict'] = {}
if 'oid_list' not in st.session_state:
    st.session_state['oid_list'] = []
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = ''
if 'apiBox_state' not in st.session_state:
    st.session_state['apiBox_state'] = False
if 'genre_input' not in st.session_state:
    st.session_state['genre_input'] = '토끼와 거북이의 달리기 경주'
if 'genreBox_state' not in st.session_state:
    st.session_state['genreBox_state'] = True

# OpenAI API 키 인증
def auth():
    os.environ['OPENAI_API_KEY'] = st.session_state.openai_api_key
    st.session_state.genreBox_state = False
    st.session_state.apiBox_state = True

# GPT-4o를 사용한 스토리 생성
def get_story_from_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """
            당신은 어린이를 위한 인터랙티브 동화책을 만드는 작가입니다. 
            "Infinity Ring" 시리즈와 유사한 스타일로 이야기를 만들어주세요.

            다음 지침을 따라주세요:
            1. 유명한 작가가 쓴 것처럼 시각적으로 풍부한 이야기를 2-3 단락으로 작성하세요.
            2. 그 후, 이야기가 어떻게 진행될지에 대한 네 가지 선택지(A, B, C, D)를 제시하세요.
            3. 선택지와 주요 이야기 사이에 "-- -- --"를 넣어 구분해주세요.
            4. 각 선택지는 새로운 줄에 작성하고, 쉼표로 구분하지 마세요.
            5. 주인공의 이름이 정해졌다면, 모든 선택지에 그 이름을 포함시켜주세요.
            6. 선택지 제시 후, "선택지: [주인공 이름]은/는 어떻게 해야 할까요?"라고 물어보세요.
            7. 마지막으로, DALL-E에게 현재 장면을 그리도록 하는 프롬프트를 제공하세요. 이 프롬프트는 "Dalle Prompt Start!"로 시작해야 합니다.

            항상 한국어로 작성해주세요. 어린이를 위한 이야기이므로 적절한 언어를 사용해주세요.
            """},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2048
    )
    return response.choices[0].message.content

# DALL-E를 사용한 이미지 생성
def get_image_by_dalle(img_prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=img_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        response_format='b64_json'
    )
    image_data = base64.b64decode(response.data[0].b64_json)
    image = Image.open(io.BytesIO(image_data))
    return image

# 스토리와 이미지 생성
def get_story_and_image(user_choice):
    llm_generation_result = get_story_from_gpt(user_choice)
    response_list = llm_generation_result.split("\n")
    
    img_prompt = next((line for line in response_list if "Dalle Prompt Start!" in line), None)
    dalle_img = get_image_by_dalle(img_prompt) if img_prompt else None
    
    choices = []
    story = ''
    responses = [s for s in response_list if s.strip() and s != '-- -- --' and 'Dalle Prompt' not in s]
    
    for response in responses:
        response = response.strip()
        if response.startswith('선택지:'):
            decisionQuestion = '**' + response + '**'
        elif response[1] == '.':
            choices.append(response)
        else:
            story += response + '\n'
    
    return {
        'story': story,
        'decisionQuestion': decisionQuestion,
        'choices': choices,
        'dalle_img': dalle_img
    }

# 새로운 데이터 추가
def add_new_data(*data):
    oid = str(uuid.uuid4())
    st.session_state['oid_list'].append(oid)
    st.session_state['data_dict'][oid] = data

# 스토리 생성 및 표시
@st.cache_data(show_spinner='이야기를 만들고 있어요...')
def get_output(user_input):
    return get_story_and_image(user_input)

# 콘텐츠 생성 및 표시
def generate_content(story, decisionQuestion, choices: list, img, oid):
    if f'expanded_{oid}' not in st.session_state:
        st.session_state[f'expanded_{oid}'] = True
    if f'radio_{oid}_disabled' not in st.session_state:
        st.session_state[f'radio_{oid}_disabled'] = False
    if f'submit_{oid}_disabled' not in st.session_state:
        st.session_state[f'submit_{oid}_disabled'] = False
    
    story_pt = list(st.session_state["data_dict"].keys()).index(oid) + 1

    expander = st.expander(f'파트 {story_pt}', expanded=st.session_state[f'expanded_{oid}'])
    col1, col2 = expander.columns([0.65, 0.35])

    if img:
        col2.image(img, width=40, use_column_width='always')
    
    with col1:
        st.write(story)
        
        if decisionQuestion and choices:
            with st.form(key=f'user_choice_{oid}'): 
                st.radio(decisionQuestion, choices, disabled=st.session_state[f'radio_{oid}_disabled'], key=f'radio_{oid}')
                submit_button = st.form_submit_button(
                    label="진행하기", 
                    disabled=st.session_state[f'submit_{oid}_disabled']
                )
                
                if submit_button:
                    user_choice = st.session_state[f'radio_{oid}']
                    st.session_state['genreBox_state'] = True
                    st.session_state[f'expanded_{oid}'] = False
                    st.session_state[f'radio_{oid}_disabled'] = True
                    st.session_state[f'submit_{oid}_disabled'] = True
                    new_data = get_output(user_choice)
                    add_new_data(new_data['story'], new_data['decisionQuestion'], new_data['choices'], new_data['dalle_img'])
                    st.experimental_rerun()

# 사이드바 UI
with st.sidebar:
    st.header("🌈 어린이 동화책 서비스")
    st.markdown('GPT-4o와 DALL-E를 사용한 인터랙티브 동화책 경험입니다.')
    st.info('**참고:** OpenAI API Key를 입력하세요.')

    with st.form(key='API Keys'):
        openai_key = st.text_input(
            label='OpenAI API Key', 
            key='openai_api_key',
            type='password',
            disabled=st.session_state.apiBox_state,
            help='OpenAI API key는 https://platform.openai.com/account/api-keys 에서 발급 가능합니다.',
        )
        
        btn = st.form_submit_button(label='확인', on_click=auth)

    with st.expander('사용 가이드'):
        st.markdown('''
        1. OpenAI API Key를 입력하고 [확인] 버튼을 누르세요.
        2. 오른쪽 화면에서 동화의 주제나 주인공을 입력하고 [시작!] 버튼을 누르세요.
        3. 이야기가 시작되면 선택지를 골라 이야기를 전개해 나가세요.
        ''')

# 메인 UI
with st.container():
    col_1, col_2, col_3 = st.columns([8, 1, 1], gap='small')
    
    col_1.text_input(
        label='동화의 주제나 주인공을 입력하세요',
        key='genre_input',
        placeholder='예: 토끼와 거북이의 달리기 경주', 
        disabled=st.session_state.genreBox_state
    )
    col_2.write('')
    col_2.write('')
    col_2_cols = col_2.columns([0.5, 6, 0.5])
    col_2_cols[1].button(
        ':arrows_counterclockwise: &nbsp; 지우기', 
        key='clear_btn',
        on_click=lambda: setattr(st.session_state, "genre_input", ''),
        disabled=st.session_state.genreBox_state
    )
    col_3.write('')
    col_3.write('')
    begin = col_3.button(
        '시작!',
        disabled=st.session_state.genreBox_state
    )

    if begin:
        initial_data = get_output(st.session_state.genre_input)
        add_new_data(initial_data['story'], initial_data['decisionQuestion'], initial_data['choices'], initial_data['dalle_img'])
        st.experimental_rerun()

# 스토리 표시
for oid in st.session_state['oid_list']:
    data = st.session_state['data_dict'][oid]
    story = data[0]
    decisionQuestion = data[1]
    choices = data[2]
    img = data[3]
    generate_content(story, decisionQuestion, choices, img, oid)

# OpenAI API 키 검증
if not st.session_state.openai_api_key.startswith('sk-'): 
    st.warning('올바른 OpenAI API Key를 입력해주세요.', icon='⚠')
