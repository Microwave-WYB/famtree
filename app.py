import streamlit as st
from pydantic import TypeAdapter

from famtree.core import FamilyTree, Gender
from famtree.visualization import create_family_tree_graph

# pylint: disable=all


st.set_page_config(layout="wide")

if "tree" not in st.session_state:
    st.session_state.tree = FamilyTree()


def display_family_tree():
    st.graphviz_chart(create_family_tree_graph(st.session_state.tree))


def create_person():
    with st.form("create_person"):
        name = st.text_input("姓名")
        gender = st.selectbox(
            "性别",
            [Gender.MALE, Gender.FEMALE, Gender.OTHER],
            format_func=lambda x: {Gender.MALE: "男", Gender.FEMALE: "女", Gender.OTHER: "其他"}[x],
        )
        birth_year = st.number_input("出生年份", min_value=1800, max_value=2024, value=2000)
        with st.expander("更多选项"):
            death_year = st.number_input(
                "死亡年份(可选)", min_value=1800, max_value=2024, value=None
            )
        submit_person = st.form_submit_button("添加", type="primary")
        update_person = st.form_submit_button("更新")

        if submit_person:
            st.session_state.tree.create_person(name, gender, birth_year, death_year)

        if update_person:
            st.session_state.tree.update_person(name, gender, birth_year, death_year)

        st.session_state.tree.sort()


def create_marriage():
    with st.form("create_marriage"):
        spouse1 = st.selectbox(
            "配偶1",
            st.session_state.tree.people,
            format_func=lambda x: f"{st.session_state.tree.people[x].name}",
        )
        spouse2 = st.selectbox(
            "配偶2",
            st.session_state.tree.people,
            format_func=lambda x: f"{st.session_state.tree.people[x].name}",
        )
        children = st.multiselect(
            "子女",
            st.session_state.tree.people,
            format_func=lambda x: f"{st.session_state.tree.people[x].name}",
        )
        submit_marriage = st.form_submit_button("添加", type="primary")
        update_marriage = st.form_submit_button("更新")

        if submit_marriage:
            st.session_state.tree.create_marriage(
                spouse1,
                spouse2,
                children,
            )

        if update_marriage:
            st.session_state.tree.update_marriage(
                spouse1,
                spouse2,
                children,
            )

        st.session_state.tree.sort()


if __name__ == "__main__":
    st.title("家谱")
    st.write("欢迎使用家谱应用！")

    col1, col2 = st.columns([1, 2])

    with st.sidebar:
        uploaded_files = st.file_uploader("导入", type="json", accept_multiple_files=True)
        # add all uploaded files to the tree
        for uploaded_file in uploaded_files or []:
            tree = TypeAdapter(FamilyTree).validate_json(uploaded_file.read().decode("utf-8"))
            st.session_state.tree.merge(tree)
            st.session_state.tree.sort()

    with col1:
        create_person()
        create_marriage()
        with st.expander("调试"):
            st.json(st.session_state.tree.model_dump_json())

    with col2:
        display_family_tree()

    # Move the export button to the bottom of the sidebar, after all updates
    with st.sidebar:
        st.download_button(
            "导出",
            TypeAdapter(FamilyTree).dump_json(st.session_state.tree, indent=2),
            "family_tree.json",
            "json",
            type="primary",
        )
