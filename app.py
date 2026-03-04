import streamlit as st
import pandas as pd
import os

# --- 設定 ---
FILE_NAME = 'menu_data.csv'
ALL_ALLERGENS = ["小麦", "卵", "乳", "そば", "落花生", "海老", "蟹", "大豆", "豚肉", "鶏肉", "牛肉"]

st.set_page_config(page_title="店舗用アレルゲン判定システム", layout="wide")

# --- データ読み込み関数 ---
def load_data():
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME)
    else:
        # 初期データ（空のデータフレーム）
        return pd.DataFrame(columns=['コース名', '料理名', '原価', 'アレルゲン', '代案'])

# --- メイン処理 ---
df = load_data()

st.title("👨‍🍳 アレルゲン判定・コース管理システム")

# タブで「判定画面」と「編集画面」を分ける
tab1, tab2 = st.tabs(["🔍 アレルゲン判定", "⚙️ メニュー編集・登録"])

# --- タブ1：判定画面 ---
with tab1:
    if df.empty:
        st.info("まずは「メニュー編集」タブから料理を登録してください。")
    else:
        st.sidebar.header("1. 条件を選択")
        course_list = df['コース名'].unique()
        selected_course = st.sidebar.selectbox("コースを選択", course_list)
        
        selected_allergens = st.sidebar.multiselect("除外するアレルゲンを選択", ALL_ALLERGENS)

        st.subheader(f"📋 判定結果: {selected_course}")
        
        # 選択コースの抽出
        items = df[df['コース名'] == selected_course]
        total_cost = 0
        
        # 3列で表示
        cols = st.columns(3)
        for i, (idx, row) in enumerate(items.iterrows()):
            with cols[i % 3]:
                # アレルゲンチェック
                # 文字列として扱い、選択されたアレルゲンが含まれているか判定
                matched = [a for a in selected_allergens if a in str(row['アレルゲン'])]
                
                if matched:
                    st.error(f"⚠️ **{row['料理名']}**")
                    st.write(f"該当: {', '.join(matched)}")
                    st.warning(f"💡 **代案: {row['代案']}**")
                else:
                    st.success(f"✅ **{row['料理名']}**")
                    st.write("そのまま提供可能")
                
                st.caption(f"単体原価: {row['原価']}円")
                total_cost += int(row['原価'])

        st.divider()
        st.metric(label="コース合計原価", value=f"{total_cost}円")

# --- タブ2：編集画面 ---
with tab2:
    st.subheader("📝 新しい料理の登録")
    with st.form("add_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        new_course = c1.text_input("コース名 (例: Aコース)")
        new_dish = c2.text_input("料理名")
        new_cost = c3.number_input("原価", min_value=0, step=10)
        
        c4, c5 = st.columns(2)
        new_allergens = c4.multiselect("含まれるアレルゲン", ALL_ALLERGENS)
        new_alt = c5.text_input("代案 (例: 味噌汁)")
        
        submit = st.form_submit_button("データを登録する")
        
        if submit and new_course and new_dish:
            new_data = pd.DataFrame([[new_course, new_dish, new_cost, ",".join(new_allergens), new_alt]], 
                                    columns=df.columns)
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(FILE_NAME, index=False)
            st.success(f"「{new_dish}」を登録しました！再読み込みします...")
            st.rerun()

    st.divider()
    st.subheader("🗑️ 登録済みデータの一覧・削除")
    if not df.empty:
        st.write("一覧表（ここから内容の確認ができます）")
        st.dataframe(df, use_container_width=True)
        
        del_idx = st.number_input("削除したい行番号を入力してください", min_value=0, max_value=len(df)-1, step=1)
        if st.button("選択した行を削除"):
            df = df.drop(df.index[del_idx])
            df.to_csv(FILE_NAME, index=False)
            st.warning("データを削除しました。")
            st.rerun()