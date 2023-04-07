import base64
from io import BytesIO
import os

from PyPDF2 import PdfReader, PdfWriter
import streamlit as st

from utils.mt import get_translate_block

if not os.path.isdir('tmp'):
    os.makedirs('tmp')
if not os.path.isdir('test_files'):
    os.makedirs('test_files')

padding_top = 0
padding_bottom = 10
padding_left = 0
padding_right = 10
# max_width_str = f'max-width: 100%;'
st.markdown(
    f'''
    <style>
        .reportview-container .sidebar-content {{
            padding-top: {padding_top}rem;
        }}
        .reportview-container .main .block-container {{
            padding-top: {padding_top}rem;
            padding-right: {padding_right}rem;
            padding-left: {padding_left}rem;
            padding-bottom: {padding_bottom}rem;
        }}
    </style>
    ''', unsafe_allow_html=True,
)


def parse_pdf(pdf_path, page_num=0):
    pdf_reader = PdfReader(str(pdf_path))
    writer = PdfWriter()

    pdf_name = '.'.join(os.path.basename(pdf_path).split('.')[:-1])
    save_path = f"tmp/{pdf_name}/{page_num}.pdf"
    if os.path.isfile(save_path):
        return base64.b64encode(open(save_path, 'rb').read()).decode('utf-8')
    if not os.path.isdir(f'tmp/{pdf_name}'):
        os.makedirs(f'tmp/{pdf_name}')

    if 0 > page_num or page_num > len(pdf_reader.pages):
        raise ValueError('Page number out of range')
    page = pdf_reader.pages[page_num]
    writer.add_page(page)

    writer.write(save_path)
    return base64.b64encode(open(save_path, 'rb').read()).decode('utf-8')


def display_pdf():
    col1, col2, col3 = st.columns([1, 0.7, 1], gap="medium")
    with st.sidebar:
        upload_file = st.file_uploader("Upload PDF", type=['pdf'])
        if upload_file:
            save_path = os.path.join('test_files', upload_file.name)
            open(save_path, 'wb').write(upload_file.getbuffer())
        pdf_name = st.radio(
            "PDFs",
            (x for x in os.listdir('test_files')),
        )
        pdf_path = os.path.join('test_files', pdf_name) # type: ignore
        pdf_name = '.'.join(os.path.basename(pdf_name).split('.')[:-1]) # type: ignore
        pdf_reader = PdfReader(str(pdf_path))
    with col1:
        page_num = int(st.number_input('Page', min_value=1, max_value=len(pdf_reader.pages)) - 1)
        save_path = f"tmp/{pdf_name}/{page_num}.txt"

        if os.path.isfile(save_path):
            origin_text = open(save_path, 'r').read()
        else:
            origin_text = pdf_reader.pages[page_num].extract_text()
        page_text = st.text_area("Text", value=origin_text, height=600)
        if st.button("Submit"):
            open(save_path, 'w').write(page_text)
    with col2:
        save_path = f"tmp/{pdf_name}/{page_num}.txt"
        c21, c22 = st.columns(2)            
        mt_text = "Click on machine translate to get the MT result"
        with c22:
            if st.button("Machine Translate"):
                mt_text = get_translate_block(page_text)
        st.write(mt_text)
    with col3:
        page_base64 = parse_pdf(pdf_path, page_num=page_num)
        pdf_display = F'<iframe src="data:application/pdf;base64,{page_base64}" width="500" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    st.divider()
    st.write("Progress:")
    st.bar_chart(
        [f"{i}.txt" in os.listdir(os.path.join("tmp", pdf_name)) for i in range(len(pdf_reader.pages))],
    )


display_pdf()
