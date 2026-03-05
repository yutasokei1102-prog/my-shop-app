import streamlit as st
import pandas as pd
import os

# --- ファイル保存・読み込み用の設定 ---
COURSE_FILE = "course_data.csv"
SUBSTITUTE_FILE = "substitute_data.csv"

def load_data():
    """CSVからデータを読み込む"""
    if os.path.exists(COURSE_FILE):
        df = pd.read_csv(COURSE_FILE)
        # 文字列として保存されたリストを復元
        df['allergens'] = df['allergens'].apply(eval)
        df['meats'] = df['meats'].apply(eval)
        st.session_state.course_data = df.to_dict('records')
    else:
        st.session_state.course_data = []

    if os.path.exists(SUBSTITUTE_FILE):
        df_sub = pd.read_csv(SUBSTITUTE_FILE)
        df_sub['allergens'] = df_sub['allergens'].apply(eval)
        df_sub['meats'] = df_sub['meats'].apply(eval)
        st.session_state.substitute_data = df_sub.to_dict('records')
    else:
        st.session_state.substitute_data = []

def save_data():
    """現在のデータをCSVに保存する"""
    pd.DataFrame(st.session_state.course_data).to_csv(COURSE_FILE, index=False)
    pd.DataFrame(st.session_state.substitute_data).to_csv(SUBSTITUTE_FILE, index=False)

# セッション状態の初期化
if 'course_data' not in st.session_state:
    load_data()

# マスターデータ（選択肢）
ALLERGENS = ["なし", "小麦", "卵", "乳", "そば", "落花生", "えび", "かに"]
MEAT_TYPES = ["なし", "豚肉", "牛肉", "鶏肉", "羊肉"]
DISH_TYPES = ["前菜", "スープ", "魚料理", "肉料理", "デザート", "その他"]

st.title("店舗管理・判定システム (自動保存版)")

tabs = st.tabs(["①コース登録", "③代案登録", "④判定ページ"])

# --- ①コース登録 ---
with tabs[0]:
    st.header("コース情報の登録")
    
    with st.form("course_form", clear_on_submit=True):
        course_name = st.text_input("コース商品名")
        dish_name = st.text_input("料理名")
        dish_type = st.selectbox("料理の種類", DISH_TYPES)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("アレルゲン選択")
            selected_allergens = [st.selectbox(f"アレルゲン{i+1}", ALLERGENS, key=f"alg_{i}") for i in range(6)]
        with col2:
            st.write("肉の種類選択")
            selected_meats = [st.selectbox(f"肉{i+1}", MEAT_TYPES, key=f"meat_{i}") for i in range(6)]
            
        submitted = st.form_submit_button("コース情報を保存")
        
        if submitted:
            algs = list(set([a for a in selected_allergens if a != "なし"]))
            meats = list(set([m for m in selected_meats if m != "なし"]))
            
            new_data = {
                "course_name": course_name,
                "dish_name": dish_name,
                "dish_type": dish_type,
                "allergens": algs,
                "meats": meats
            }
            st.session_state.course_data.append(new_data)
            save_data() # CSVに即時保存
            st.success(f"「{course_name}」を保存しました。データはCSVに蓄積されました。")

    st.write("### 登録済みコース一覧")
    for i, data in enumerate(st.session_state.course_data):
        with st.expander(f"コース: {data['course_name']} (料理: {data['dish_name']})"):
            st.write(f"**種類:** {data['dish_type']} / **アレルゲン:** {', '.join(data['allergens'])} / **肉:** {', '.join(data['meats'])}")
            if st.button("削除", key=f"del_c_{i}"):
                st.session_state.course_data.pop(i)
                save_data()
                st.rerun()

# --- ③代案登録 ---
with tabs[1]:
    st.header("代案商品の登録")
    with st.form("sub_form", clear_on_submit=True):
        sub_name = st.text_input("代案商品名")
        sub_type = st.selectbox("対応する料理の種類", DISH_TYPES)
        sub_allergens = st.multiselect("含まれるアレルゲン", ALLERGENS)
        sub_meats = st.multiselect("含まれる肉の種類", MEAT_TYPES)
        
        if st.form_submit_button("代案を保存"):
            st.session_state.substitute_data.append({
                "name": sub_name, "type": sub_type, "allergens": sub_allergens, "meats": sub_meats
            })
            save_data() # CSVに即時保存
            st.success("代案を保存しました。")

    if st.button("登録済みの代案を表示"):
        if st.session_state.substitute_data:
            st.table(pd.DataFrame(st.session_state.substitute_data))

# --- ④判定ページ ---
with tabs[2]:
    st.header("アレルゲン・肉 判定")
    if not st.session_state.course_data:
        st.warning("登録データがありません。")
    else:
        target_course = st.selectbox("判定するコースを選択", list(set([d['course_name'] for d in st.session_state.course_data])))
        c1, c2 = st.columns(2)
        check_alg = c1.selectbox("除外アレルゲン", ALLERGENS)
        check_meat = c2.selectbox("除外肉種類", MEAT_TYPES)
        
        if st.button("判定開始"):
            relevant_dishes = [d for d in st.session_state.course_data if d['course_name'] == target_course]
            text_output = f"判定結果: {target_course}\n"
            
            for dish in relevant_dishes:
                is_hit = (check_alg != "なし" and check_alg in dish['allergens']) or \
                         (check_meat != "なし" and check_meat in dish['meats'])
                
                if is_hit:
                    st.error(f"【NG】{dish['dish_name']}")
                    # 代案検索
                    subs = [s for s in st.session_state.substitute_data if s['type'] == dish['dish_type'] 
                            and (check_alg not in s['allergens']) and (check_meat not in s['meats'])]
                    for s in subs:
                        st.info(f" └ 代案候補: {s['name']}")
                        text_output += f"・{dish['dish_name']} → 代案: {s['name']}\n"
                else:
                    st.success(f"【OK】{dish['dish_name']}")
            
            st.download_button("結果をテキスト保存", text_output, file_name="result.txt")