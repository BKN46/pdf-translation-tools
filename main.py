import base64
from genericpath import isfile
from io import BytesIO
import os
import re

from PyPDF2 import PdfReader, PdfWriter
import streamlit as st
from annotated_text import annotated_text

from utils.login import login
from utils.mt import get_translate_block

if not os.path.isdir('tmp'):
    os.makedirs('tmp')
if not os.path.isdir('test_files'):
    os.makedirs('test_files')

st.set_page_config(
    page_title="BKN Translation Tool",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
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


def add_new_term(pdf_name, new_term, new_meaning):
    new_term = new_term.lower()
    term_tsv_path = f"tmp/{pdf_name}.tsv"
    if os.path.isfile(term_tsv_path):
        terms = {
            x.strip().split('\t')[0].lower() : x.strip().split('\t')[1]
            for x in open(term_tsv_path, 'r').readlines()
        }
        if new_term in terms:
            terms[new_term] = new_meaning
            open(term_tsv_path, 'w').write('\n'.join(
                {f"{term}\t{meaning}" for term, meaning in terms.items()}
            ))
        else:
            open(term_tsv_path, 'a').write(f"{new_term}\t{new_meaning}\n")
    else:
        open(term_tsv_path, 'a').write(f"{new_term}\t{new_meaning}\n")


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
    if pdf_name:
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
            tab1, tab2= st.tabs(["Terms", "MT"])
            with tab1:
                term_tsv_path = f"tmp/{pdf_name}.tsv"
                c21, c22, c23  = st.columns([1, 1, 0.5])
                with c21:
                    new_term = st.text_input("New term")
                with c22:
                    new_meaning = st.text_input("New meaning")
                with c23:
                    new_term_publish = st.button("Add")
                if new_term_publish:
                    add_new_term(pdf_name, new_term, new_meaning)

                if os.path.isfile(term_tsv_path):
                    terms = {
                        x.strip().split('\t')[0].lower() : x.strip().split('\t')[1]
                        for x in open(term_tsv_path, 'r').readlines()
                    }
                    term_trans_text = []
                    last_end = 0
                    for i, c in enumerate(origin_text):
                        for term, meaning in terms.items():
                            if origin_text[i:i+len(term)].lower() == term:
                                term_trans_text += [
                                    origin_text[last_end: i], (origin_text[i:i+len(term)], meaning)
                                ]
                                last_end = i + len(term)
                    term_trans_text += [origin_text[last_end:]]
                    annotated_text(*term_trans_text)

            with tab2:
                mt_save_path = f"tmp/{pdf_name}/{page_num}.mt"
                c21, c22 = st.columns(2)            
                if os.path.isfile(mt_save_path):
                    mt_text = open(mt_save_path, 'r').read()
                else:
                    mt_text = "Click on machine translate to get the MT result"
                with c21:
                    if st.button("Machine Translate"):
                        mt_text = get_translate_block(page_text)
                        open(mt_save_path, 'w').write(mt_text)
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

        if st.button("Generate markdown result"):
            markdown_result = f"# {pdf_name}\n\n" + "\n\n".join([
                f"## {x.split('.')[0]}\n\n{open(os.path.join('tmp', pdf_name, x), 'r').read()}"
                for x in os.listdir(os.path.join("tmp", pdf_name)) if x.endswith(".txt")
            ])
            open(f"tmp/{pdf_name}.md", 'w').write(markdown_result)
            st.download_button(
                "Download Result",
                data=open(f"tmp/{pdf_name}.md", 'r'),
                file_name=f"{pdf_name}.md",
            )
    else:
        st.write("No PDFs uploaded yet")

if login():
    display_pdf()
