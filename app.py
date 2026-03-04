import streamlit as st
import pandas as pd
import os

# --- 設定・ファイルパス ---
COURSE_FILE = 'course_list.csv'
ALT_FILE = 'alternative_list.csv'
MASTER_FILE = 'master_config.csv'

# --- データの読み込み・保存関数 ---
def save_data(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

def load_data(filename, columns):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=columns)

# --- セッション状態の初期化 ---
if 'master_dish_types' not in st.session_state:
    df_m = load_data(MASTER_FILE, ['type', 'value'])
    st.session_state.master_dish_types = df_m[df_m['type']=='dish']['value'].tolist() or ["麺料理", "汁物", "炒め物"]
    st.session_state.master_meat_types = df_m[df_m['type']=='meat']['value'].tolist() or ["なし", "豚肉", "牛肉", "鶏肉"]

if 'courses' not in st.session_state:
    # 簡易的にリストで管理（本来はJSONやDBが望ましいですが、一旦リストで保持）
    st.session_state.courses = []

if 'alternatives' not in st.session_state:
    # 小麦アレルギー代替品として味噌汁を提案する設定
    st.session_state.alternatives = [
        {"name": "味噌汁", "type": "汁物", "meat": "なし", "seasoning": "カツオ出汁・味噌"}
    ]

st.set_page_config(page_title="コース料理判定システム", layout="wide")
st.title("コース料理判定システム")

tab1, tab2, tab3, tab4 = st.tabs(["①コース登録", "②詳細(マスタ)登録", "③代案登録", "④判定ページ"])

# ②詳細登録 (マスタ)
with tab2:
    st.header("②詳細登録・編集 (マスタ)")
    col1, col2 = st.columns(2)
    with col1:
        new_dish = st.text_input("料理の種類を追加")
        if st.button("料理種別を追加") and new_dish:
            st.session_state.master_dish_types.append(new_dish)
            st.rerun()
    with col2:
        new_meat = st.text_input("肉の種類を追加")
        if st.button("肉種別を追加") and new_meat:
            st.session_state.master_meat_types.append(new_meat)
            st.rerun()

# ①コース登録 (簡略版)
with tab1:
    st.header("①コース商品登録")
    c_name = st.text_input("コース商品名")
    if 'temp_items' not in st.session_state: st.session_state.temp_items = []
    
    if st.button("+ 料理枠を追加"):
        st.session_state.temp_items.append({"name": "", "type": st.session_state.master_dish_types[0], "allergen": "", "meat": st.session_state.master_meat_types[0]})
    
    for i, item in enumerate(st.session_state.temp_items):
        with st.expander(f"料理 {i+1}"):
            item['name'] = st.text_input(f"料理名 {i+1}", key=f"name_{i}")
            item['type'] = st.selectbox(f"種類 {i+1}", st.session_state.master_dish_types, key=f"type_{i}")
            item['allergen'] = st.text_input(f"アレルゲン {i+1}", key=f"all_{i}", help="小麦、卵など")
            item['meat'] = st.selectbox(f"肉 {i+1}", st.session_state.master_meat_types, key=f"meat_{i}")

    if st.button("コース全体を保存"):
        st.session_state.courses.append({"name": c_name, "items": st.session_state.temp_items})
        st.success(f"コース「{c_name}」を保存しました")

# ③代案登録
with tab3:
    st.header("③代案商品登録")
    with st.form("alt_form"):
        alt_n = st.text_input("代案商品名")
        alt_t = st.selectbox("対象となる料理の種類", st.session_state.master_dish_types)
        alt_m = st.selectbox("肉の種類", st.session_state.master_meat_types)
        alt_s = st.text_input("調味料(味付け)")
        if st.form_submit_button("代案を登録"):
            st.session_state.alternatives.append({"name": alt_n, "type": alt_t, "meat": alt_m, "seasoning": alt_s})
            st.success("代案を登録しました")

# ④判定ページ
with tab4:
    st.header("④判定ページ")
    course_list = [c['name'] for c in st.session_state.courses]
    selected_c = st.selectbox("コース選択", course_list)
    target = st.text_input("判定したいキーワード（小麦、豚肉など）")
    
    if st.button("判定開始"):
        course = next((c for c in st.session_state.courses if c['name'] == selected_c), None)
        if course:
            hit_flag = False
            for dish in course['items']:
                # 小麦アレルギー等の成分判定
                is_hit = (target in dish['allergen']) or (target == dish['meat'])
                color = "red" if is_hit else "black"
                st.markdown(f"<span style='color:{color}; font-weight:bold;'>・{dish['name']}</span>", unsafe_allow_html=True)
                if is_hit: hit_flag = True
            
            if hit_flag:
                if st.button("代案しますか？"):
                    st.subheader("代案リスト")
                    for dish in course['items']:
                        is_hit = (target in dish['allergen']) or (target == dish['meat'])
                        if is_hit:
                            alt = next((a for a in st.session_state.alternatives if a['type'] == dish['type']), None)
                            if alt: st.success(f"【代案】{alt['name']} (味付: {alt['seasoning']})")
                            else: st.warning(f"{dish['name']} の代案が見つかりません")
                        else: st.text(f"・{dish['name']}")