from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from seating import assign_seats
from trainee_file import COMMUNICATION, COLUMNS, GENDERS, GRADES, export_trainees, import_trainees

local_storage = components.declare_component("trainee_local_storage", path=str(Path(__file__).parent / "local_storage_component"))


def replace_trainees(records, companies):
    st.session_state.trainees = pd.DataFrame(records, columns=COLUMNS)
    st.session_state.companies = companies
    st.session_state.editor_version += 1
    st.session_state.pop("result", None)


def preserve_trainees():
    """企業候補の変更前に、表で編集中の内容を確定する。"""
    frame = st.session_state.trainees.copy()
    state = st.session_state.get(f"trainee_editor_{st.session_state.editor_version}", {})
    for row, changes in state.get("edited_rows", {}).items():
        for column, value in changes.items():
            frame.at[int(row), column] = value
    frame = frame.drop(index=state.get("deleted_rows", []), errors="ignore")
    if state.get("added_rows"):
        frame = pd.concat([frame, pd.DataFrame(state["added_rows"])], ignore_index=True)
    st.session_state.trainees = frame.reindex(columns=COLUMNS).reset_index(drop=True)
    st.session_state.editor_version += 1


st.set_page_config(page_title="席替えアプリ", page_icon="🪑", layout="wide")
st.title("🪑 席替えアプリ")
st.write("研修生を入力して、ランダムに4人ずつのグループに分けます。")

if "trainees" not in st.session_state:
    st.session_state.trainees = pd.DataFrame(
        [{"名前": "", "所属": "", "性別": "未入力", "成績": None, "コミュニケーションスキル": None}]
    )
if "editor_version" not in st.session_state:
    st.session_state.editor_version = 0
if "companies" not in st.session_state:
    st.session_state.companies = []
if "pending_storage_data" in st.session_state:
    imported, companies = st.session_state.pop("pending_storage_data")
    replace_trainees(imported, companies)

st.subheader("企業情報")
st.caption("企業名を入力してEnterで追加できます。削除しても、設定済みの所属は変わりません。")
companies = st.multiselect("企業一覧", options=st.session_state.companies, key="companies", accept_new_options=True, on_change=preserve_trainees, placeholder="企業名を入力")
current_affiliations = st.session_state.trainees["所属"].dropna().tolist()
affiliation_options = list(dict.fromkeys([company for company in [*companies, *current_affiliations] if isinstance(company, str) and company]))

st.subheader("研修生情報")
st.caption("表の下の「＋」で行を追加できます。名前以外の項目は空欄でも構いません。")
edited = st.data_editor(
    st.session_state.trainees,
    num_rows="dynamic",
    hide_index=True,
    width="stretch",
    column_config={
        "名前": st.column_config.TextColumn("名前", required=False),
        "所属": st.column_config.SelectboxColumn("所属", options=affiliation_options),
        "性別": st.column_config.SelectboxColumn("性別", options=GENDERS),
        "成績": st.column_config.SelectboxColumn("成績", options=list(GRADES)),
        "コミュニケーションスキル": st.column_config.SelectboxColumn("コミュニケーションスキル", options=list(COMMUNICATION)),
    },
    key=f"trainee_editor_{st.session_state.editor_version}",
)

_, count_column = st.columns([4, 1])
with count_column:
    st.markdown(f"<div style='text-align: right'>合計：{len(edited)}人</div>", unsafe_allow_html=True)
st.caption("合計は名前が未入力の行も含む、表の行数です。")
st.caption("成績はA〜E（Aが最も良い）、コミュニケーションスキルは3段階です。現在は配置に使用しません。")
records = edited[COLUMNS].astype(object).where(pd.notna(edited[COLUMNS]), None).to_dict("records")
for person in records:
    for column in ("名前", "所属", "性別"):
        if person[column] is None:
            person[column] = ""
serialized = export_trainees(records, companies)
st.subheader("ブラウザへの保存")
st.caption("保存は手動です。企業一覧と研修生情報を保存します。読み込むと現在の入力内容が置き換わります。クリアはブラウザの保存データだけを削除します。")
if "storage_notice" in st.session_state:
    kind, message = st.session_state.pop("storage_notice")
    getattr(st, kind)(message)
storage_event = local_storage(data=serialized.decode("utf-8"), key="browser_storage", default=None)
if storage_event and storage_event.get("id") != st.session_state.get("last_storage_event"):
    st.session_state.last_storage_event = storage_event["id"]
    try:
        imported, loaded_companies = import_trainees(storage_event["data"].encode("utf-8"))
        st.session_state.pending_storage_data = (imported, loaded_companies)
        st.session_state.storage_notice = ("success", f"ブラウザから研修生情報を{len(imported)}件読み込みました。")
    except (ValueError, TypeError, KeyError) as exc:
        st.session_state.storage_notice = ("error", f"ブラウザの保存データを読み込めませんでした: {exc}")
    st.rerun()

signature = repr(records)

if st.button("ランダムに席替え", type="primary"):
    if not records:
        st.warning("研修生を1人以上入力してください。")
        st.session_state.pop("result", None)
    elif any(not str(person["名前"]).strip() for person in records):
        st.warning("すべての研修生の名前を入力してください。")
        st.session_state.pop("result", None)
    else:
        st.session_state.result = assign_seats(records)
        st.session_state.result_signature = signature

if "result" in st.session_state:
    if signature != st.session_state.result_signature:
        st.info("研修生情報が変更されました。席替えボタンを押して結果を更新してください。")
    else:
        st.subheader("席替え結果")
        st.write(f"研修生 {len(records)}人 / {len(st.session_state.result)}グループ")
        groups = st.session_state.result
        for start in range(0, len(groups), 2):
            if start:
                st.html("<div style='height: 1.5rem' aria-hidden='true'></div>")
            group_columns = st.columns(2, gap="large")
            for offset, group in enumerate(groups[start : start + 2]):
                with group_columns[offset]:
                    st.markdown(f"**グループ {start + offset + 1}（{len(group)}人）**")
                    for row in range(0, len(group), 2):
                        if row:
                            st.html("<div style='height: 0.75rem' aria-hidden='true'></div>")
                        seats = st.columns(2)
                        for seat_offset, person in enumerate(group[row : row + 2]):
                            with seats[seat_offset]:
                                gender = person.get("性別") or "未入力"
                                color = {"男性": "#e8f4fd", "女性": "#fdebed"}.get(gender, "#eeeeee")
                                name = escape(str(person["名前"]))
                                gender_label = escape(str(gender))
                                st.markdown(
                                    f"<div style='background-color:{color}; color:#31333f; "
                                    "padding: 1rem; border-radius: 0.5rem; overflow-wrap: anywhere;'>"
                                    f"席 {row + seat_offset + 1}：{name}<br>"
                                    f"<small>性別：{gender_label}</small></div>",
                                    unsafe_allow_html=True,
                                )
