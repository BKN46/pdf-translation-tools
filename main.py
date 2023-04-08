import base64
from genericpath import isfile
from io import BytesIO
import os
import re
import time

from annotated_text import annotated_text
from PyPDF2 import PdfReader
import streamlit as st


from utils.login import login
from utils.mt import get_translate_block
from utils.pdf import pdf_page_image

if not os.path.isdir("tmp"):
    os.makedirs("tmp")
if not os.path.isdir("test_files"):
    os.makedirs("test_files")

st.set_page_config(
    page_title="BKN Translation Tool",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

def add_new_term(pdf_name, new_term, new_meaning):
    new_term = new_term.lower()
    term_tsv_path = f"tmp/{pdf_name}.tsv"
    if os.path.isfile(term_tsv_path):
        terms = {
            x.strip().split("\t")[0].lower(): x.strip().split("\t")[1]
            for x in open(term_tsv_path, "r").readlines()
        }
        if new_term in terms:
            terms[new_term] = new_meaning
            open(term_tsv_path, "w").write(
                "\n".join({f"{term}\t{meaning}" for term, meaning in terms.items()})
            )
        else:
            open(term_tsv_path, "a").write(f"{new_term}\t{new_meaning}\n")
    else:
        open(term_tsv_path, "a").write(f"{new_term}\t{new_meaning}\n")


def add_new_index(pdf_name, new_index, index_page):
    new_index = new_index.lower()
    term_tsv_path = f"tmp/{pdf_name}.index"
    if os.path.isfile(term_tsv_path):
        terms = {
            x.strip().split("\t")[0].lower(): x.strip().split("\t")[1]
            for x in open(term_tsv_path, "r").readlines()
        }
        if new_index in terms:
            terms[new_index] = index_page
            open(term_tsv_path, "w").write(
                "\n".join({f"{term}\t{meaning}" for term, meaning in terms.items()})
            )
        else:
            open(term_tsv_path, "a").write(f"{new_index}\t{index_page}\n")
    else:
        open(term_tsv_path, "a").write(f"{new_index}\t{index_page}\n")
    st.session_state.page = 0


def bottom_render(pdf_name, pdf_reader):
    st.write("Progress:")
    st.bar_chart(
        [
            f"{i}.txt" in os.listdir(os.path.join("tmp", pdf_name))
            for i in range(len(pdf_reader.pages))
        ],
    )

    if st.button("Generate markdown result"):
        markdown_result = f"# {pdf_name}\n\n" + "\n\n".join(
            [
                f"## {x.split('.')[0]}\n\n{open(os.path.join('tmp', pdf_name, x), 'r').read()}"
                for x in os.listdir(os.path.join("tmp", pdf_name))
                if x.endswith(".txt")
            ]
        )
        open(f"tmp/{pdf_name}.md", "w").write(markdown_result)
        st.download_button(
            "Download Result",
            data=open(f"tmp/{pdf_name}.md", "r"),
            file_name=f"{pdf_name}.md",
        )

    if st.button("Init all page images"):
        all_page_num = len(pdf_reader.pages)
        use_times = []
        with st.spinner("Initializing..."):
            my_bar = st.progress(0)
            for i in range(all_page_num):
                start_time = time.time()
                page_image = pdf_page_image(pdf_reader, pdf_name, page_num=i)
                use_time = time.time() - start_time
                if use_time > 0.1:
                    use_times.append(use_time)
                if len(use_times) > 0:
                    my_bar.progress(
                        i / all_page_num,
                        text=f"{i + 1}/{all_page_num}  {(all_page_num - i - 1)/(sum(use_times)/len(use_times))/60:.2f}min left",
                    )
                else:
                    my_bar.progress(i / all_page_num, text=f"{i + 1}/{all_page_num}")


def display_pdf():
    col1, col2, col3 = st.columns([1, 0.7, 1], gap="medium")
    with st.sidebar:
        upload_file = st.file_uploader("Upload PDF", type=["pdf"])
        if upload_file:
            save_path = os.path.join("test_files", upload_file.name)
            open(save_path, "wb").write(upload_file.getbuffer())
        pdf_name = st.radio(
            "PDFs",
            (x for x in os.listdir("test_files")),
        )
        pdf_path = os.path.join("test_files", pdf_name)  # type: ignore
        pdf_reader = PdfReader(str(pdf_path))
        pdf_name = ".".join(os.path.basename(pdf_name).split(".")[:-1])  # type: ignore
        index_tsv_path = f"tmp/{pdf_name}.index"
        if os.path.isfile(index_tsv_path):
            pdf_index = {
                x.strip().split("\t")[0]: int(x.strip().split("\t")[1])
                for x in open(index_tsv_path, "r").readlines()
            }
        else:
            pdf_index = None
    if pdf_name:
        with col1:
            c11, c12 = st.columns([1, 1])
            with c11:
                first_page_num = int(
                    st.number_input(
                        "Page", min_value=1, max_value=len(pdf_reader.pages),
                    )
                    - 1
                )
                page_num = first_page_num
            # with c12:
            #     if pdf_index:
            #         now_index = st.selectbox(
            #             "Index", [k for k, v in pdf_index.items()] if pdf_index else [],
            #         ) or pdf_index.keys()[0] # type: ignore
            #         second_page_num = int(pdf_index[now_index]) - 1
            #     else:
            #         second_page_num = 0
            save_path = f"tmp/{pdf_name}/{page_num}.txt"

            origin_text = pdf_reader.pages[page_num].extract_text()
            if os.path.isfile(save_path):
                saved_text = open(save_path, "r").read()
            else:
                saved_text = origin_text
            page_text = st.text_area("Text", value=saved_text, height=600)
            if st.button("Submit"):
                open(save_path, "w").write(page_text)

        with col3:
            # st.write(f"DEBUG: {page_num}")
            with st.spinner("Page is rendering..."):
                page_image = pdf_page_image(pdf_reader, pdf_name, page_num=page_num)
            st.image(BytesIO(page_image))

        with col2:
            index_tsv_path = f"tmp/{pdf_name}.index"
            tab1, tab2, tab3 = st.tabs(["Terms", "Index", "MT"])
            with tab1:
                term_tsv_path = f"tmp/{pdf_name}.tsv"
                c21, c22, c23 = st.columns([1, 1, 0.5])
                with c21:
                    new_term = st.text_input("New term")
                with c22:
                    new_meaning = st.text_input("New meaning")
                with c23:
                    new_term_publish = st.button("Add term")
                if new_term_publish:
                    add_new_term(pdf_name, new_term, new_meaning)

                if os.path.isfile(term_tsv_path):
                    terms = {
                        x.strip().split("\t")[0].lower(): x.strip().split("\t")[1]
                        for x in open(term_tsv_path, "r").readlines()
                    }
                    term_trans_text = []
                    last_end = 0
                    for i, c in enumerate(origin_text):
                        for term, meaning in terms.items():
                            if origin_text[i : i + len(term)].lower() == term:
                                term_trans_text += [
                                    origin_text[last_end:i],
                                    (origin_text[i : i + len(term)], meaning),
                                ]
                                last_end = i + len(term)
                    term_trans_text += [origin_text[last_end:]]
                    annotated_text(*term_trans_text)

            with tab2:
                c21, c22, c23 = st.columns([1, 1, 0.5])
                with c21:
                    new_index = st.text_input("Title")
                with c22:
                    new_index_page = st.number_input("Index", step=1)
                with c23:
                    new_index_publish = st.button("Add index")
                if new_index_publish:
                    add_new_index(pdf_name, new_index, new_index_page)

                if pdf_index:
                    pdf_index = list(sorted(pdf_index.items(), key=lambda x: x[1]))
                    st.text("\n".join([f"{v:<5}{k:<15}" for k, v in pdf_index]))

            with tab3:
                mt_save_path = f"tmp/{pdf_name}/{page_num}.mt"
                c21, c22 = st.columns(2)
                if os.path.isfile(mt_save_path):
                    mt_text = open(mt_save_path, "r").read()
                else:
                    mt_text = "Click on machine translate to get the MT result"
                with c21:
                    if st.button("Machine Translate"):
                        mt_text = get_translate_block(page_text)
                        open(mt_save_path, "w").write(mt_text)
                st.write(mt_text)


        st.divider()
        bottom_render(pdf_name, pdf_reader)

    else:
        st.write("No PDFs uploaded yet")


if login():
    display_pdf()
