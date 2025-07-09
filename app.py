import streamlit as st
import pandas as pd
import numpy as np

# --- ページ設定とデザイン ---
st.set_page_config(layout="wide", page_title="スマスロ モンスターハンターライズ 設定判別ツール")

# 背景画像のCSS (GitHubに画像を配置した場合のパスを想定)
# **あなたのGitHubユーザー名とリポジトリ名に合わせてURLが記述されています**
background_image_css = """
<style>
/* 基本的なHTML/Bodyスタイルをリセットし、オーバーフローをstAppに任せる */
html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%; /* 高さを100%に設定 */
    overflow: hidden; /* body自体のスクロールは禁止し、stAppがスクロールを制御 */
}

/* Streamlitアプリ全体のコンテナ */
.stApp {
    background-image: url("https://raw.githubusercontent.com/0221Yoshinari/karakuri-setting-tool/main/images/monster_hunter_rise_bg.png"); /* モンハンライズの画像パスに修正済み */
    background-size: cover; /* 画面全体を覆う */
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed; /* 背景は固定のまま、スクロールしても常に画像が見える */
    min-height: 100vh; /* アプリ全体の最小高さをビューポートの高さに合わせる */
    height: 100%; /* stAppの高さを親要素（body）に合わせる */
    overflow-y: auto; /* ★stAppコンテナ自体が縦方向にスクロールできるように設定★ */
    position: relative; /* z-indexのために必要 */
    display: flex;
    flex-direction: column; /* 子要素を縦に並べる */
}

/* 背景画像の上に重ねるオーバーレイ */
.stApp::before {
    content: "";
    position: fixed; /* オーバーレイも固定 */
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.1); /* 透明度を0.1に設定 */
    z-index: 1;
    pointer-events: none; /* ★★★オーバーレイがクリックやスクロールをブロックしないようにする★★★ */
}

/* メインコンテンツブロック（入力項目などがある部分） */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    z-index: 2; /* コンテンツが背景画像より手前に来るように */
    position: relative; /* z-indexのために必要 */
    background-color: rgba(0, 0, 0, 0.7); /* コンテンツエリアの背景色を半透明に */
    border-radius: 10px;
    padding: 30px;
    flex-grow: 1; /* コンテンツブロックが利用可能なスペースを埋めるように成長 */
}

/* その他のスタイル調整（色など） */
h1, h2, h3, h4, h5, h6, p, label, .st-ck, .st-bj, .st-bq {
    color: white !important;
}
.stSelectbox div[data-baseweb="select"] {
    background-color: #333 !important;
    color: white !important;
}
.stSelectbox div[data-baseweb="select"] div[data-testid="stSelectboxDropdown"] {
    background-color: #333 !important;
    color: white !important;
}
.stTextInput > div > div > input {
    background-color: #333 !important;
    color: white !important;
}
.stButton>button {
    background-color: #D35400; /* ボタンの背景色 */
    color: white; /* ボタンの文字色 */
    border-radius: 5px;
    border: none;
    padding: 10px 20px;
}
.stButton>button:hover {
    background-color: #E67E22;
}
.css-1r6dm7f { /* markdown text color */
    color: white;
}
</style>
"""
st.markdown(background_image_css, unsafe_allow_html=True)

# ヘッダー
st.title("スマスロ モンスターハンターライズ 設定判別ツール")
st.markdown("---")

# --- 設定示唆の基準値 (私の裁量で設定。実際の解析値と異なる場合があります) ---
# 各設定の基礎スコア（初期値）
# 設定Lは考慮しない
initial_setting_scores = {
    '設定1': 100, '設定2': 110, '設定3': 120, '設定4': 150, '設定5': 180, '設定6': 200
}

# ボーナス（AT）初当たり確率（一撃より）
# 設定1:1/356.5, 設定2:1/343.3, 設定3:1/327.3, 設定4:1/309.8, 設定5:1/289.4, 設定6:1/257.6
at_probability_scores = {
    '設定1': {'min_rate': 380, 'max_rate': 320, 'score_adjust': 20},
    '設定2': {'min_rate': 340, 'max_rate': 300, 'score_adjust': 10},
    '設定3': {'min_rate': 320, 'max_rate': 290, 'score_adjust': 5},
    '設定4': {'min_rate': 300, 'max_rate': 270, 'score_adjust': 15},
    '設定5': {'min_rate': 280, 'max_rate': 240, 'score_adjust': 25},
    '設定6': {'min_rate': 250, 'max_rate': 200, 'score_adjust': 40},
}

# ライズゾーン当選率 (弱チェリー・スイカ) - 画像9枚目
# 設定1:25.0%, 設定2:25.4%, 設定3:28.1%, 設定4:30.5%, 設定5:34.4%, 設定6:35.2%
rise_zone_rates = {
    '設定1': 0.250, '設定2': 0.254, '設定3': 0.281, '設定4': 0.305, '設定5': 0.344, '設定6': 0.352
}
rise_zone_score_adjust = 30 # 高ければ高設定に30加点

# 3枚ベルからの高確移行率 - 画像8枚目
# 設定1:6.25%, 設定2:6.64%, 設定3:7.03%, 設定4:7.81%, 設定5:8.59%, 設定6:9.38%
high_probability_transition_rates = {
    '設定1': 0.0625, '設定2': 0.0664, '設定3': 0.0703, '設定4': 0.0781, '設定5': 0.0859, '設定6': 0.0938
}
high_prob_trans_score_adjust = 20 # 高ければ高設定に20加点

# アイルーだるま落とし当選までの規定リプレイ回数振り分け - 画像7枚目
# 40回, 80回, 120回, 160回, 200回
ailu_replay_dist = {
    '設定1': {40: 0.125, 80: 0.125, 120: 0.250, 160: 0.250, 200: 0.250},
    '設定2': {40: 0.133, 80: 0.133, 120: 0.242, 160: 0.246, 200: 0.246},
    '設定3': {40: 0.156, 80: 0.156, 120: 0.219, 160: 0.234, 200: 0.234},
    '設定4': {40: 0.195, 80: 0.195, 120: 0.203, 160: 0.203, 200: 0.203},
    '設定5': {40: 0.219, 80: 0.219, 120: 0.195, 160: 0.184, 200: 0.184},
    '設定6': {40: 0.227, 80: 0.227, 120: 0.188, 160: 0.180, 200: 0.180},
}
# 40回, 80回当選は高設定優遇, 120回以上は低設定優遇

# CZ（クエスト）当選周期 / 天国移行 - 画像10枚目
# 設定5・6の天国移行率: 約47.3% (9/19)
# 1周期当選は天国とみなす
period_score_weights = {
    '1周期': {'設定1': -10, '設定2': -5, '設定3': -5, '設定4': 10, '設定5': 20, '設定6': 30}, # 天国示唆
    '2周期': {'設定1': 5, '設定2': 5, '設定3': 5, '設定4': 0, '設定5': 0, '設定6': 0}, # 中間
    '3周期': {'設定1': 5, '設定2': 5, '設定3': 10, '設定4': 0, '設定5': -5, '設定6': -5}, # 低設定/中間寄り
    '4周期': {'設定1': 10, '設定2': 10, '設定3': 5, '設定4': -5, '設定5': -10, '設定6': -15},
    '5周期': {'設定1': 15, '設定2': 10, '設定3': 5, '設定4': -10, '設定5': -15, '設定6': -20},
    '6周期以上': {'設定1': 20, '設定2': 15, '設定3': 10, '設定4': -15, '設定5': -20, '設定6': -25}, # 深い周期は低設定示唆
}


# ボーナス確定画面・示唆内容 - 画像1枚目
bonus_kakutei_display = {
    'MG-減-ワドウ丸': '奇数設定示唆',
    'ルーク': '奇数設定示唆',
    'HARUTO': '奇数設定示唆',
    'アッシュ': '偶数設定示唆',
    'Mimi☆chan': '偶数設定示唆',
    'つばき': '偶数設定示唆',
    'YOU': '高設定示唆',
    'Lara&ミランダ&隊長': '設定4以上濃厚',
}
bonus_kakutei_scores = {
    'MG-減-ワドウ丸':      {'設定1': 10, '設定2': 0, '設定3': 5, '設定4': 0, '設定5': 5, '設定6': 0},
    'ルーク':             {'設定1': 10, '設定2': 0, '設定3': 5, '設定4': 0, '設定5': 5, '設定6': 0},
    'HARUTO':             {'設定1': 10, '設定2': 0, '設定3': 5, '設定4': 0, '設定5': 5, '設定6': 0},
    'アッシュ':            {'設定1': 0, '設定2': 10, '設定3': 0, '設定4': 5, '設定5': 0, '設定6': 5},
    'Mimi☆chan':          {'設定1': 0, '設定2': 10, '設定3': 0, '設定4': 5, '設定5': 0, '設定6': 5},
    'つばき':              {'設定1': 0, '設定2': 10, '設定3': 0, '設定4': 5, '設定5': 0, '設定6': 5},
    'YOU':                {'設定1': -10, '設定2': -5, '設定3': 0, '設定4': 10, '設定5': 10, '設定6': 10},
    'Lara&ミランダ&隊長': {'設定1': -100, '設定2': -100, '設定3': -100, '設定4': 100, '設定5': 100, '設定6': 100}, # 設定4以上濃厚
}

# ボーナス終了画面・示唆内容 - 画像2枚目
bonus_end_display = {
    'MG-減-ワドウ丸': '奇数設定示唆', 'ルーク': '奇数設定示唆', 'HARUTO': '奇数設定示唆',
    'アッシュ': '偶数設定示唆', 'Mimi☆chan': '偶数設定示唆', 'つばき': '偶数設定示唆',
    'YOU&オトモ': '高設定示唆 [弱]', 'Lara&ミランダ&隊長 (装備有り)': '高設定示唆 [強]',
    'イオリ&ヨモギ': '設定2否定', 'ウツシ&フゲン': '設定3否定',
    '全員集合': '設定5以上濃厚', 'ヒノエ&ミノト&エンタライオン': '設定6濃厚',
    'ルーク&HARUTO&Mimi (インナー)': '天国期待度約50%', 'ワドウ丸&アッシュ&つばき (インナー)': '天国期待度約80%',
    'Lara&ミランダ&隊長 (インナー)': '天国濃厚'
}
bonus_end_scores = {
    'MG-減-ワドウ丸':             {'設定1': 10, '設定2': 0, '設定3': 5, '設定4': 0, '設定5': 5, '設定6': 0},
    'ルーク':                    {'設定1': 10, '設定2': 0, '設定3': 5, '設定4': 0, '設定5': 5, '設定6': 0},
    'HARUTO':                    {'設定1': 10, '設定2': 0, '設定3': 5, '設定4': 0, '設定5': 5, '設定6': 0},
    'アッシュ':                   {'設定1': 0, '設定2': 10, '設定3': 0, '設定4': 5, '設定5': 0, '設定6': 5},
    'Mimi☆chan':                 {'設定1': 0, '設定2': 10, '設定3': 0, '設定4': 5, '設定5': 0, '設定6': 5},
    'つばき':                     {'設定1': 0, '設定2': 10, '設定3': 0, '設定4': 5, '設定5': 0, '設定6': 5},
    'YOU&オトモ':                 {'設定1': -5, '設定2': 0, '設定3': 0, '設定4': 5, '設定5': 5, '設定6': 5},
    'Lara&ミランダ&隊長 (装備有り)':{'設定1': -10, '設定2': -5, '設定3': 0, '設定4': 15, '設定5': 15, '設定6': 15},
    'イオリ&ヨモギ':              {'設定1': 10, '設定2': -1000, '設定3': 10, '設定4': 0, '設定5': 0, '設定6': 0}, # 設定2否定
    'ウツシ&フゲン':              {'設定1': 10, '設定2': 10, '設定3': -1000, '設定4': 0, '設定5': 0, '設定6': 0}, # 設定3否定
    '全員集合':                  {'設定1': -100, '設定2': -100, '設定3': -100, '設定4': 50, '設定5': 150, '設定6': 150}, # 設定5以上濃厚
    'ヒノエ&ミノト&エンタライオン': {'設定1': -1000, '設定2': -1000, '設定3': -1000, '設定4': -1000, '設定5': -1000, '設定6': 500}, # 設定6濃厚
    'ルーク&HARUTO&Mimi (インナー)':  {'設定1': -5, '設定2': 0, '設定3': 0, '設定4': 5, '設定5': 5, '設定6': 5}, # 天国期待度約50% (高設定示唆に寄せる)
    'ワドウ丸&アッシュ&つばき (インナー)':{'設定1': -10, '設定2': -5, '設定3': 0, '設定4': 10, '設定5': 10, '設定6': 10}, # 天国期待度約80% (高設定示唆に寄せる)
    'Lara&ミランダ&隊長 (インナー)': {'設定1': -20, '設定2': -10, '設定3': -5, '設定4': 15, '設定5': 15, '設定6': 15}, # 天国濃厚 (高設定示唆に寄せる)
}


# エンタトロフィー・示唆内容 - 画像3枚目
entaro_display = {
    '銅': '設定2以上濃厚', '銀': '設定3以上濃厚', '金': '設定4以上濃厚',
    '紅葉柄': '設定5以上濃厚', '虹': '設定6濃厚'
}
entaro_scores = {
    '銅':    {'設定1': -100, '設定2': 50, '設定3': 50, '設定4': 50, '設定5': 50, '設定6': 50},
    '銀':    {'設定1': -100, '設定2': -100, '設定3': 100, '設定4': 100, '設定5': 100, '設定6': 100},
    '金':    {'設定1': -100, '設定2': -100, '設定3': -100, '設定4': 150, '設定5': 150, '設定6': 150},
    '紅葉柄': {'設定1': -100, '設定2': -100, '設定3': -100, '設定4': -100, '設定5': 200, '設定6': 200},
    '虹':    {'設定1': -1000, '設定2': -1000, '設定3': -1000, '設定4': -1000, '設定5': -1000, '設定6': 1000}
}

# エンディング中のおみくじの色・示唆内容 - 画像4枚目
omikuji_display = {
    '青': '奇数設定示唆', '緑': '偶数設定示唆', '赤': '高設定示唆 [強]',
    '銅': '設定2以上濃厚', '銀': '設定3以上濃厚', '金': '設定4以上濃厚',
    '紅葉柄': '設定5以上濃厚', '虹': '設定6濃厚'
}
omikuji_scores = {
    '青':  {'設定1': 10, '設定2': -5, '設定3': 5, '設定4': -5, '設定5': 5, '設定6': 0},
    '緑':  {'設定1': -5, '設定2': 10, '設定3': -5, '設定4': 5, '設定5': 0, '設定6': 5},
    '赤':  {'設定1': -10, '設定2': 0, '設定3': 0, '設定4': 10, '設定5': 10, '設定6': 10},
    '銅':  {'設定1': -50, '設定2': 50, '設定3': 50, '設定4': 50, '設定5': 50, '設定6': 50},
    '銀':  {'設定1': -100, '設定2': -50, '設定3': 100, '設定4': 100, '設定5': 100, '設定6': 100},
    '金':  {'設定1': -100, '設定2': -100, '設定3': -50, '設定4': 150, '設定5': 150, '設定6': 150},
    '紅葉柄': {'設定1': -100, '設定2': -100, '設定3': -100, '設定4': -100, '設定5': 200, '設定6': 200},
    '虹':  {'設定1': -1000, '設定2': -1000, '設定3': -1000, '設定4': -1000, '設定5': -1000, '設定6': 1000}
}


# ボーナス図柄揃い時のボイス・示唆内容 - 画像5枚目上段
bonus_voice_display = {
    '紫7の1確ボイスがエンタライオン': '設定6濃厚',
    '仲間ボイスがウツシ': '設定5以上',
    '仲間ボイスがヒノエ': '設定6濃厚'
}
bonus_voice_scores = {
    '紫7の1確ボイスがエンタライオン': {'設定1': -1000, '設定2': -1000, '設定3': -1000, '設定4': -1000, '設定5': -1000, '設定6': 500},
    '仲間ボイスがウツシ':           {'設定1': -100, '設定2': -100, '設定3': -100, '設定4': -100, '設定5': 200, '設定6': 200},
    '仲間ボイスがヒノエ':           {'設定1': -1000, '設定2': -1000, '設定3': -1000, '設定4': -1000, '設定5': -1000, '設定6': 500}
}

# ウツシとヒノエのボイス - 画像5枚目中段（示唆内容なしだが高設定示唆とする）
utsushi_hinoe_voice_scores = {
    'うおおおおおぉおぉ！→愛弟子とのスロット!!→最高〜!!!': {'設定1': -5, '設定2': 0, '設定3': 5, '設定4': 10, '設定5': 15, '設定6': 20}, # ウツシボイス
    'うふふふ♪このことは〜→ミノトに内緒ですよ': {'設定1': -5, '設定2': 0, '設定3': 5, '設定4': 10, '設定5': 15, '設定6': 20} # ヒノエボイス
}

# ボーナス入賞後のボイス・設定4以上濃厚パターン - 画像5枚目下段
bonus_nyusho_scores = {
    'ボイスのハンターがボーナス中に参戦しない': {'設定1': -50, '設定2': -50, '設定3': -50, '設定4': 50, '設定5': 50, '設定6': 50}, # 設定4以上濃厚
    '当該モンスターが得意ではないハンターのボイスが発生': {'設定1': -50, '設定2': -50, '設定3': -50, '設定4': 50, '設定5': 50, '設定6': 50}, # 設定4以上濃厚
}


# 共通ベルからのAT直撃当選率（一撃より）- 画像6枚目
# 設定1: 1/13909.6, 設定2: 1/12869.4, 設定3: 1/12030.7, 設定4: 1/10574.6, 設定5: 1/9102.3, 設定6: 1/7360.7
direct_hit_prob_thresholds = {
    '設定1': 13909.6, '設定2': 12869.4, '設定3': 12030.7, '設定4': 10574.6, '設定5': 9102.3, '設定6': 7360.7
}
direct_hit_score_per_hit = {'設定4': 50, '設定5': 70, '設定6': 100} # 1回あたりの加点

# --- A. 台の挙動に関する入力 ---
st.header("A. 台の挙動に関する入力")

col1, col2 = st.columns(2)
with col1:
    total_games = st.number_input("1. 総ゲーム数", min_value=0, value=0, step=100)
with col2:
    at_first_hit_count = st.number_input("2. ボーナス(AT)初当たり回数", min_value=0, value=0)

# 3. CZ（クエスト）当選周期
st.subheader("3. CZ（クエスト）当選周期 (複数入力可)")
st.info("💡 何周期目で当選したかを入力してください。1周期当選は天国示唆です。")
if 'quest_periods' not in st.session_state:
    st.session_state.quest_periods = []

def add_quest_period_entry():
    st.session_state.quest_periods.append({'period': ''}) # is_cz_successは不要

def remove_quest_period_entry(index):
    st.session_state.quest_periods.pop(index)

st.button("周期当選履歴を追加", on_click=add_quest_period_entry)

for i, quest_entry in enumerate(st.session_state.quest_periods):
    period_cols = st.columns([0.8, 0.2])
    with period_cols[0]:
        # '選択なし'を初期値にできないので、periodが空の場合はデフォルト値を設定
        initial_value = quest_entry['period'] if quest_entry['period'] != '' else 1
        st.session_state.quest_periods[i]['period'] = st.number_input(f"CZ {i+1}回目: 当選周期 (例: 1, 2, 3...) ", min_value=1, value=initial_value, step=1, key=f"quest_period_{i}")
    with period_cols[1]:
        st.button("削除", key=f"remove_quest_period_{i}", on_click=remove_quest_period_entry, args=(i,))

# 4. ライズゾーン当選率 (弱チェリー・スイカ)
st.subheader("4. ライズゾーン当選率 (弱チェリー・スイカ)")
rz_weak_trigger_count = st.number_input("弱チェリー・スイカからのライズゾーン当選回数", min_value=0, value=0)
rz_weak_trigger_total = st.number_input("弱チェリー・スイカの総成立回数", min_value=0, value=0)

# 5. 3枚ベルからの高確移行率
st.subheader("5. 3枚ベルからの高確移行率")
bell_high_prob_trans_count = st.number_input("3枚ベルからの高確移行回数", min_value=0, value=0)
bell_total_count = st.number_input("3枚ベルの総成立回数", min_value=0, value=0)

# 6. アイルーだるま落とし当選までの規定リプレイ回数
st.subheader("6. アイルーだるま落とし当選までの規定リプレイ回数 (複数入力可)")
if 'ailu_replay_data' not in st.session_state:
    st.session_state.ailu_replay_data = []

def add_ailu_replay_entry():
    st.session_state.ailu_replay_data.append({'replays': '選択なし'})

def remove_ailu_replay_entry(index):
    st.session_state.ailu_replay_data.pop(index)

st.button("アイルーだるま落とし当選履歴を追加", on_click=add_ailu_replay_entry)
ailu_replay_options = ['選択なし', '40回', '80回', '120回', '160回', '200回']

for i, entry in enumerate(st.session_state.ailu_replay_data):
    ailu_cols = st.columns([0.8, 0.2])
    with ailu_cols[0]:
        st.session_state.ailu_replay_data[i]['replays'] = st.selectbox(f"当選リプレイ回数 {i+1}回目", options=ailu_replay_options, index=ailu_replay_options.index(entry['replays']), key=f"ailu_replay_{i}")
    with ailu_cols[1]:
        st.button("削除", key=f"remove_ailu_replay_{i}", on_click=remove_ailu_replay_entry, args=(i,))

# 7. ボーナス確定画面
st.subheader("7. ボーナス確定画面")
selected_bonus_kakutei = st.multiselect(
    "出現したボーナス確定画面を全て選択してください",
    options=list(bonus_kakutei_display.keys()),
    default=[]
)
bonus_kakutei_counts = {}
for screen in selected_bonus_kakutei:
    bonus_kakutei_counts[screen] = st.number_input(f"{screen} の出現回数", min_value=0, value=0, key=f"bonus_kakutei_count_{screen}")

# 8. ボーナス終了画面
st.subheader("8. ボーナス終了画面")
selected_bonus_end = st.multiselect(
    "出現したボーナス終了画面を全て選択してください",
    options=list(bonus_end_display.keys()),
    default=[]
)
bonus_end_counts = {}
for screen in selected_bonus_end:
    bonus_end_counts[screen] = st.number_input(f"{screen} の出現回数", min_value=0, value=0, key=f"bonus_end_count_{screen}")

# 9. エンタトロフィー
st.subheader("9. エンタトロフィー")
entaro_color = st.selectbox(
    "エンタトロフィーの色を選択してください",
    options=['選択なし'] + list(entaro_display.keys())
)

# 10. エンディング中のおみくじの色
st.subheader("10. エンディング中のおみくじの色")
omikuji_color = st.selectbox(
    "エンディング中のおみくじの色を選択してください",
    options=['選択なし'] + list(omikuji_display.keys())
)

# 11. ボーナス図柄揃い時のボイス
st.subheader("11. ボーナス図柄揃い時のボイス")
selected_bonus_voice = st.multiselect(
    "出現したボーナス図柄揃い時のボイスを全て選択してください",
    options=list(bonus_voice_display.keys()),
    default=[]
)
bonus_voice_counts = {}
for voice in selected_bonus_voice:
    bonus_voice_counts[voice] = st.number_input(f"「{voice}」の出現回数", min_value=0, value=0, key=f"bonus_voice_count_{voice}")

# 12. ウツシとヒノエのボイス
st.subheader("12. ウツシとヒノエのボイス")
selected_utsushi_hinoe_voice = st.multiselect(
    "出現したウツシとヒノエのボイスを全て選択してください",
    options=list(utsushi_hinoe_voice_scores.keys()),
    default=[]
)
utsushi_hinoe_voice_counts = {}
for voice in selected_utsushi_hinoe_voice:
    utsushi_hinoe_voice_counts[voice] = st.number_input(f"「{voice}」の出現回数", min_value=0, value=0, key=f"utsushi_hinoe_voice_count_{voice}")


# 13. ボーナス入賞後のボイス（設定4以上濃厚パターン）
st.subheader("13. ボーナス入賞後のボイス（設定4以上濃厚パターン）")
selected_bonus_nyusho = st.multiselect(
    "出現したボーナス入賞後のボイスパターンを全て選択してください",
    options=list(bonus_nyusho_scores.keys()),
    default=[]
)
bonus_nyusho_counts = {}
for pattern in selected_bonus_nyusho:
    bonus_nyusho_counts[pattern] = st.number_input(f"「{pattern}」の出現回数", min_value=0, value=0, key=f"bonus_nyusho_count_{pattern}")

# 14. 共通ベルからのAT直撃
st.subheader("14. 共通ベルからのAT直撃")
direct_hit_count = st.number_input("共通ベルからのAT直撃回数", min_value=0, value=0)
common_bell_total_count = st.number_input("共通ベルの総成立回数 (不明な場合は0)", min_value=0, value=0)


# --- B. 店舗・外部要因に関する入力 (任意入力) ---
st.header("B. 店舗・外部要因に関する入力 (任意)")
st.info("💡 こちらの項目は任意です。入力するとより実戦的な判断が可能です。")

# ホール全体のモンハンライズ設定投入傾向
st.subheader("1. ホール全体のモンハンライズ設定投入傾向")
hall_mh_tendency = st.radio(
    "当ホールはモンハンライズに普段から設定を入れる傾向がありますか？",
    options=['選択しない', '高い', '普通', '低い'],
    index=0, horizontal=True
)

# モンハンライズはホールの主力機種か
st.subheader("2. モンハンライズはホールの主力機種か")
is_main_machine = st.radio(
    "モンハンライズはホールの主力機種（高稼働・人気機種）ですか？",
    options=['選択しない', 'はい', 'いいえ'],
    index=0, horizontal=True
)

# 遊技日は特定イベント日か
st.subheader("3. 遊技日は特定イベント日か")
event_day_type = st.radio(
    "本日は特定イベント日ですか？",
    options=['選択しない', '強いイベント日 (例: 周年、全台系示唆)', '弱いイベント日 (例: 特定機種示唆)', 'イベントなし'],
    index=0, horizontal=True
)

# モンハンライズ関連の取材・広告の有無
st.subheader("4. モンハンライズ関連の取材・広告の有無")
mh_coverage = st.radio(
    "モンハンライズ関連の取材や広告は入っていますか？",
    options=['選択しない', 'ある', 'ない'],
    index=0, horizontal=True
)

# 高設定投入示唆系の取材・広告の有無
st.subheader("5. 高設定投入示唆系の取材・広告の有無")
high_setting_coverage = st.radio(
    "ホール全体で高設定投入を示唆する取材や広告は入っていますか？",
    options=['選択しない', 'ある', 'ない'],
    index=0, horizontal=True
)

# 遊技日は通常の営業日か
st.subheader("6. 遊技日は通常の営業日か")
is_normal_day = st.radio(
    "本日は通常の営業日ですか？ (イベント日などを考慮)",
    options=['選択しない', 'はい', 'いいえ'],
    index=0, horizontal=True
)

# モンハンライズ得意演者の来店有無
st.subheader("7. モンハンライズを得意とする来店演者はいますか？")
performer_presence = st.radio(
    "モンハンライズを得意とする来店演者はいますか？",
    options=['選択しない', 'いる', 'いない'],
    index=0, horizontal=True
)

# 過去に当ホールでモンハンライズ設定6確定経験の有無
st.subheader("8. 過去に当ホールでモンハンライズ設定6確定経験の有無")
seen_setting6_in_hall = st.radio(
    "当ホールで過去にモンハンライズの設定6確定画面を見たことがありますか？",
    options=['選択しない', 'ある', 'ない'],
    index=0, horizontal=True
)

# 当ホールの設定6使用傾向
st.subheader("9. 当ホールの設定6使用傾向")
hall_setting6_tendency = st.radio(
    "当ホールは普段から設定6を使う傾向がありますか？",
    options=['選択しない', '高い', '普通', '低い'],
    index=0, horizontal=True
)

# 他の台の状況 (自由記述)
st.subheader("10. 他の台の状況")
other_machine_status = st.text_area(
    "周囲の台（同じ機種や他の機種）の状況を簡潔に入力してください。"
)

# --- 判別実行ボタン ---
st.markdown("---")
if st.button("設定を判別する", key="run_analysis"):
    st.subheader("### 判別結果")
    st.write("---")

    # 各設定の可能性スコアを初期化
    setting_likelihood_scores = initial_setting_scores.copy()

    # --- A. 台の挙動に関する評価 ---

    # ボーナス(AT)初当たり確率
    at_first_hit_rate = 0
    if total_games > 0 and at_first_hit_count > 0:
        at_first_hit_rate = total_games / at_first_hit_count
        st.write(f"**ボーナス(AT)初当たり確率: 1/{at_first_hit_rate:.2f}**")
        for s in at_probability_scores.keys():
            # 理論値の範囲に収まるか、またはそれを超えるかでスコア調整
            if at_first_hit_rate <= at_probability_scores[s]['min_rate'] and at_first_hit_rate >= at_probability_scores[s]['max_rate']:
                setting_likelihood_scores[s] += at_probability_scores[s]['score_adjust']
            elif at_first_hit_rate < at_probability_scores[s]['max_rate'] and s == '設定6': # 設定6より良い
                setting_likelihood_scores[s] += at_probability_scores[s]['score_adjust'] * 1.5
            elif at_first_hit_rate > at_probability_scores[s]['min_rate'] and s == '設定1': # 設定1より悪い
                setting_likelihood_scores[s] += at_probability_scores[s]['score_adjust'] * 1.5
            # その他の設定へのペナルティ
            elif at_first_hit_rate < at_probability_scores[s]['max_rate']: # 特定の設定の範囲より良すぎる場合（他設定を減点）
                 setting_likelihood_scores[s] -= at_probability_scores[s]['score_adjust'] * 0.5
            elif at_first_hit_rate > at_probability_scores[s]['min_rate']: # 特定の設定の範囲より悪すぎる場合（他設定を減点）
                 setting_likelihood_scores[s] -= at_probability_scores[s]['score_adjust'] * 0.5
    else:
        st.write("**ボーナス(AT)初当たり情報は入力されていません。**")

    # CZ（クエスト）当選周期
    if st.session_state.quest_periods:
        st.write("**CZ（クエスト）当選周期:**")
        for i, entry in enumerate(st.session_state.quest_periods):
            period = entry['period']
            if period == 1:
                st.write(f"- {i+1}回目: {period}周期目当選 → 天国示唆！")
                for s in period_score_weights['1周期'].keys():
                    setting_likelihood_scores[s] += period_score_weights['1周期'][s]
            elif period in [2,3,4,5]: # 2周期から5周期
                st.write(f"- {i+1}回目: {period}周期目当選")
                for s in period_score_weights[f'{period}周期'].keys():
                    setting_likelihood_scores[s] += period_score_weights[f'{period}周期'][s]
            elif period >= 6: # 6周期以上
                st.write(f"- {i+1}回目: {period}周期目当選 (6周期以上)")
                for s in period_score_weights['6周期以上'].keys():
                    setting_likelihood_scores[s] += period_score_weights['6周期以上'][s]
            
            # 設定5・6の挙動（画像10枚目）を基準に評価を強化
            # 1周期当選が多ければ高設定寄りに大きく加点
            if period <= 1:
                setting_likelihood_scores['設定4'] += 5
                setting_likelihood_scores['設定5'] += 10
                setting_likelihood_scores['設定6'] += 15
                setting_likelihood_scores['設定1'] -= 5
                setting_likelihood_scores['設定2'] -= 5
                setting_likelihood_scores['設定3'] -= 5
            elif period >= 4: # 4周期以上は低設定寄りに減点
                setting_likelihood_scores['設定1'] += 5
                setting_likelihood_scores['設定2'] += 5
                setting_likelihood_scores['設定3'] += 5
                setting_likelihood_scores['設定4'] -= 5
                setting_likelihood_scores['設定5'] -= 10
                setting_likelihood_scores['設定6'] -= 15
    else:
        st.write("**CZ（クエスト）当選周期は入力されていません。**")

    # ライズゾーン当選率 (弱チェリー・スイカ)
    rz_rate_observed = 0
    if rz_weak_trigger_total > 0:
        rz_rate_observed = rz_weak_trigger_count / rz_weak_trigger_total
        st.write(f"**ライズゾーン当選率 (弱チェリー・スイカ): {rz_rate_observed:.2%} ({rz_weak_trigger_count}/{rz_weak_trigger_total})**")
        for s in rise_zone_rates.keys():
            # 実際の当選率が理論値に近いほど加点、離れるほど減点
            diff = abs(rz_rate_observed - rise_zone_rates[s])
            score_change = (0.05 - diff) * rise_zone_score_adjust * 100 # 差が小さいほどプラス、大きいほどマイナス
            setting_likelihood_scores[s] += score_change
            
    else:
        st.write("**ライズゾーン当選率情報は入力されていません。**")

    # 3枚ベルからの高確移行率
    bell_trans_rate_observed = 0
    if bell_total_count > 0:
        bell_trans_rate_observed = bell_high_prob_trans_count / bell_total_count
        st.write(f"**3枚ベルからの高確移行率: {bell_trans_rate_observed:.2%} ({bell_high_prob_trans_count}/{bell_total_count})**")
        for s in high_probability_transition_rates.keys():
            diff = abs(bell_trans_rate_observed - high_probability_transition_rates[s])
            score_change = (0.02 - diff) * high_prob_trans_score_adjust * 100 # 差が小さいほどプラス、大きいほどマイナス
            setting_likelihood_scores[s] += score_change
    else:
        st.write("**3枚ベルからの高確移行率情報は入力されていません。**")

    # アイルーだるま落とし当選までの規定リプレイ回数
    if st.session_state.ailu_replay_data:
        st.write("**アイルーだるま落とし当選規定リプレイ回数履歴:**")
        for i, entry in enumerate(st.session_state.ailu_replay_data):
            replays_str = entry['replays']
            if replays_str != '選択なし':
                replays = int(replays_str.replace('回', ''))
                st.write(f"- {i+1}回目: {replays}回で当選")
                # 各設定の振り分け率に基づいてスコアを調整
                for s in ailu_replay_dist.keys():
                    if replays in ailu_replay_dist[s]:
                        # 当選回数がその設定の優遇レンジなら加点、そうでないなら減点
                        current_prob = ailu_replay_dist[s][replays]
                        # 短いリプレイ回数ほど高設定は加点、長いリプレイ回数ほど低設定は加点
                        if replays <= 80: # 40回 or 80回
                            setting_likelihood_scores[s] += current_prob * 100 # 優遇度に応じて加点
                        else: # 120回以上
                            setting_likelihood_scores[s] -= current_prob * 50 # 低設定寄りなら減点
            else:
                st.write(f"- {i+1}回目: (入力なし)")
    else:
        st.write("**アイルーだるま落とし当選履歴は入力されていません。**")

    strong_fixed_setting = None # 確定示唆を追跡

    # ボーナス確定画面
    if selected_bonus_kakutei:
        st.write("**ボーナス確定画面:**")
        for screen, count in bonus_kakutei_counts.items():
            if count > 0:
                indication_text = bonus_kakutei_display.get(screen, '特定示唆なし')
                st.write(f"- {screen} ({count}回出現) → **{indication_text}**")
                for s in setting_likelihood_scores.keys():
                    if screen in bonus_kakutei_scores and s in bonus_kakutei_scores[screen]:
                        setting_likelihood_scores[s] += bonus_kakutei_scores[screen][s] * count
                # 確定示唆の処理
                if "設定4以上濃厚" in indication_text:
                    if not strong_fixed_setting or strong_fixed_setting == '設定3以上' or strong_fixed_setting == '設定2以上':
                        strong_fixed_setting = '設定4以上'
    else:
        st.write("**ボーナス確定画面は入力されていません。**")

    # ボーナス終了画面
    if selected_bonus_end:
        st.write("**ボーナス終了画面:**")
        for screen, count in bonus_end_counts.items():
            if count > 0:
                indication_text = bonus_end_display.get(screen, '特定示唆なし')
                st.write(f"- {screen} ({count}回出現) → **{indication_text}**")
                for s in setting_likelihood_scores.keys():
                    if screen in bonus_end_scores and s in bonus_end_scores[screen]:
                        setting_likelihood_scores[s] += bonus_end_scores[screen][s] * count
                # 確定示唆の処理
                if "設定6濃厚" in indication_text:
                    strong_fixed_setting = '設定6'
                elif "設定5以上濃厚" in indication_text:
                    if not strong_fixed_setting or (strong_fixed_setting != '設定6'):
                        strong_fixed_setting = '設定5以上'
                elif "設定4以上濃厚" in indication_text:
                     if not strong_fixed_setting or (strong_fixed_setting != '設定6' and strong_fixed_setting != '設定5以上'):
                        strong_fixed_setting = '設定4以上'
                elif "設定3否定" in indication_text:
                    setting_likelihood_scores['設定3'] = -10000 # 強力に否定
                elif "設定2否定" in indication_text:
                    setting_likelihood_scores['設定2'] = -10000 # 強力に否定
    else:
        st.write("**ボーナス終了画面は入力されていません。**")

    # エンタトロフィー
    if entaro_color != '選択なし':
        st.write(f"**エンタトロフィー: {entaro_color}**")
        for s in setting_likelihood_scores.keys():
            if entaro_color in entaro_scores and s in entaro_scores[entaro_color]:
                setting_likelihood_scores[s] += entaro_scores[entaro_color][s]
        # 確定示唆の処理
        if entaro_color == '虹': strong_fixed_setting = '設定6'
        elif entaro_color == '紅葉柄': 
            if not strong_fixed_setting or (strong_fixed_setting != '設定6'): strong_fixed_setting = '設定5以上'
        elif entaro_color == '金': 
            if not strong_fixed_setting or (strong_fixed_setting != '設定6' and strong_fixed_setting != '設定5以上'): strong_fixed_setting = '設定4以上'
        elif entaro_color == '銀':
            if not strong_fixed_setting or (strong_fixed_setting != '設定6' and strong_fixed_setting != '設定5以上' and strong_fixed_setting != '設定4以上'): strong_fixed_setting = '設定3以上'
        elif entaro_color == '銅':
            if not strong_fixed_setting or (strong_fixed_setting != '設定6' and strong_fixed_setting != '設定5以上' and strong_fixed_setting != '設定4以上' and strong_fixed_setting != '設定3以上'): strong_fixed_setting = '設定2以上'
    else:
        st.write("**エンタトロフィーは入力されていません。**")

    # エンディング中のおみくじの色
    if omikuji_color != '選択なし':
        st.write(f"**エンディング中のおみくじの色: {omikuji_color}**")
        for s in setting_likelihood_scores.keys():
            if omikuji_color in omikuji_scores and s in omikuji_scores[omikuji_color]:
                setting_likelihood_scores[s] += omikuji_scores[omikuji_color][s]
        # 確定示唆の処理
        if omikuji_color == '虹': strong_fixed_setting = '設定6'
        elif omikuji_color == '紅葉柄': 
            if not strong_fixed_setting or (strong_fixed_setting != '設定6'): strong_fixed_setting = '設定5以上'
        elif omikuji_color == '金': 
            if not strong_fixed_setting or (strong_fixed_setting != '設定6' and strong_fixed_setting != '設定5以上'): strong_fixed_setting = '設定4以上'
        elif omikuji_color == '銀':
            if not strong_fixed_setting or (strong_fixed_setting != '設定6' and strong_fixed_setting != '設定5以上' and strong_fixed_setting != '設定4以上'): strong_fixed_setting = '設定3以上'
        elif omikuji_color == '銅':
            if not strong_fixed_setting or (strong_fixed_setting != '設定6' and strong_fixed_setting != '設定5以上' and strong_fixed_setting != '設定4以上' and strong_fixed_setting != '設定3以上'): strong_fixed_setting = '設定2以上'
    else:
        st.write("**エンディング中のおみくじの色は入力されていません。**")

    # ボーナス図柄揃い時のボイス
    if selected_bonus_voice:
        st.write("**ボーナス図柄揃い時のボイス:**")
        for voice, count in bonus_voice_counts.items():
            if count > 0:
                st.write(f"- 「{voice}」({count}回出現)")
                for s in setting_likelihood_scores.keys():
                    if voice in bonus_voice_scores and s in bonus_voice_scores[voice]:
                        setting_likelihood_scores[s] += bonus_voice_scores[voice][s] * count
                # 確定示唆の処理
                if '設定6濃厚' in bonus_voice_display.get(voice, ''):
                    strong_fixed_setting = '設定6'
                elif '設定5以上' in bonus_voice_display.get(voice, ''):
                    if not strong_fixed_setting or (strong_fixed_setting != '設定6'):
                        strong_fixed_setting = '設定5以上'
    else:
        st.write("**ボーナス図柄揃い時のボイスは入力されていません。**")

    # ウツシとヒノエのボイス
    if selected_utsushi_hinoe_voice:
        st.write("**ウツシとヒノエのボイス:**")
        for voice, count in utsushi_hinoe_voice_counts.items():
            if count > 0:
                st.write(f"- 「{voice}」({count}回出現)")
                for s in setting_likelihood_scores.keys():
                    if voice in utsushi_hinoe_voice_scores and s in utsushi_hinoe_voice_scores[voice]:
                        setting_likelihood_scores[s] += utsushi_hinoe_voice_scores[voice][s] * count
    else:
        st.write("**ウツシとヒノエのボイスは入力されていません。**")

    # ボーナス入賞後のボイス（設定4以上濃厚パターン）
    if selected_bonus_nyusho:
        st.write("**ボーナス入賞後のボイス（設定4以上濃厚パターン）:**")
        for pattern, count in bonus_nyusho_counts.items():
            if count > 0:
                st.write(f"- 「{pattern}」({count}回出現) → 設定4以上濃厚！")
                for s in setting_likelihood_scores.keys():
                    if pattern in bonus_nyusho_scores and s in bonus_nyusho_scores[pattern]:
                        setting_likelihood_scores[s] += bonus_nyusho_scores[pattern][s] * count
                if not strong_fixed_setting or (strong_fixed_setting != '設定6' and strong_fixed_setting != '設定5以上'):
                    strong_fixed_setting = '設定4以上'
    else:
        st.write("**ボーナス入賞後のボイスは入力されていません。**")
        
    # 共通ベルからのAT直撃
    if direct_hit_count > 0:
        st.write(f"**共通ベルからのAT直撃回数: {direct_hit_count}回**")
        for s in direct_hit_score_per_hit.keys():
            setting_likelihood_scores[s] += direct_hit_score_per_hit[s] * direct_hit_count
        if common_bell_total_count > 0:
            direct_hit_rate_observed = common_bell_total_count / direct_hit_count
            st.write(f"共通ベルからの直撃確率: 1/{direct_hit_rate_observed:.2f} ({direct_hit_count}/{common_bell_total_count})")
            # 確率の閾値と比較してスコア調整
            for s, threshold in direct_hit_prob_thresholds.items():
                if s in setting_likelihood_scores:
                    diff_ratio = (direct_hit_rate_observed - threshold) / threshold # どのくらい離れているか
                    if direct_hit_rate_observed <= threshold: # 理論値より良い（直撃しやすい）
                        setting_likelihood_scores[s] += 20 * abs(diff_ratio) # 差分が大きいほど加点
                    else: # 理論値より悪い（直撃しにくい）
                        setting_likelihood_scores[s] -= 10 * abs(diff_ratio) # 差分が大きいほど減点
            
        if direct_hit_count >= 1: # 1回でもあれば高設定示唆を強化
            if not strong_fixed_setting or (strong_fixed_setting != '設定6' and strong_fixed_setting != '設定5以上'):
                 strong_fixed_setting = '設定4以上'
    else:
        st.write("**共通ベルからのAT直撃は入力されていません。**")


    # --- B. 店舗・外部要因に関する評価 (スコアリング) ---
    st.markdown("---")
    st.subheader("### 店舗・外部要因からの評価")
    
    external_score_multiplier = 0 # 外部要因の総合的な影響度

    external_score_map = {
        'hall_mh_tendency': {'高い': 0.10, '普通': 0, '低い': -0.10, '選択しない': 0}, # 倍率として影響
        'is_main_machine': {'はい': 0.05, 'いいえ': 0, '選択しない': 0},
        'event_day_type': {'強いイベント日 (例: 周年、全台系示唆)': 0.20, '弱いイベント日 (例: 特定機種示唆)': 0.10, 'イベントなし': -0.05, '選択しない': 0},
        'mh_coverage': {'ある': 0.05, 'ない': 0, '選択しない': 0},
        'high_setting_coverage': {'ある': 0.15, 'ない': 0, '選択しない': 0},
        'performer_presence': {'いる': 0.10, 'いない': 0, '選択しない': 0},
        'seen_setting6_in_hall': {'ある': 0.25, 'ない': -0.10, '選択しない': 0}, # 過去の実績は非常に重要
        'hall_setting6_tendency': {'高い': 0.15, '普通': 0, '低い': -0.15, '選択しない': 0},
    }

    # 各外部要因の倍率を計算
    external_score_multiplier += external_score_map['hall_mh_tendency'].get(hall_mh_tendency, 0)
    external_score_multiplier += external_score_map['is_main_machine'].get(is_main_machine, 0)
    external_score_multiplier += external_score_map['event_day_type'].get(event_day_type, 0)
    external_score_multiplier += external_score_map['mh_coverage'].get(mh_coverage, 0)
    external_score_multiplier += external_score_map['high_setting_coverage'].get(high_setting_coverage, 0)
    external_score_multiplier += external_score_map['performer_presence'].get(performer_presence, 0)
    external_score_multiplier += external_score_map['seen_setting6_in_hall'].get(seen_setting6_in_hall, 0)
    external_score_multiplier += external_score_map['hall_setting6_tendency'].get(hall_setting6_tendency, 0)

    # 各設定スコアに外部要因の倍率を適用（高設定に有利に働くように）
    # ただし、低設定への影響は小さくする
    for s in setting_likelihood_scores.keys():
        if s in ['設定4', '設定5', '設定6']:
            setting_likelihood_scores[s] *= (1 + external_score_multiplier)
        elif s in ['設定1', '設定2', '設定3']: # 設定3も低設定側に含める
            setting_likelihood_scores[s] *= (1 - external_score_multiplier * 0.5) # 高設定寄りなら低設定は少し下がる
        setting_likelihood_scores[s] = max(1, setting_likelihood_scores[s]) # スコアが0以下にならないように最低1を設定

    if other_machine_status:
        st.write(f"**その他の台の状況:** {other_machine_status}")


    # --- 総合判定（各設定の可能性と高設定期待度） ---
    st.markdown("---")
    st.subheader("### 総合判定")

    # 確定示唆によるフィルタリングとスコアの強制
    if strong_fixed_setting:
        st.success(f"**🎉 {strong_fixed_setting}確定レベルの強力な示唆が確認されました！ 🎉**")
        for s in list(setting_likelihood_scores.keys()): # dictionary size might change during iteration
            if strong_fixed_setting == '設定6':
                if s != '設定6': setting_likelihood_scores[s] = 0
            elif strong_fixed_setting == '設定5以上':
                if s in ['設定1', '設定2', '設定3', '設定4']: setting_likelihood_scores[s] = 0
            elif strong_fixed_setting == '設定4以上':
                if s in ['設定1', '設定2', '設定3']: setting_likelihood_scores[s] = 0
            elif strong_fixed_setting == '設定3以上':
                if s in ['設定1', '設定2']: setting_likelihood_scores[s] = 0
            elif strong_fixed_setting == '設定2以上':
                if s == '設定1': setting_likelihood_scores[s] = 0
        
        # 確定示唆が出た場合のスコア調整（設定6を極端に高くする等）
        if strong_fixed_setting == '設定6':
            setting_likelihood_scores['設定6'] = 1000000 # 圧倒的に高く
            # 他の設定は0にする（既にされているが念のため）
            for s in setting_likelihood_scores:
                if s != '設定6':
                    setting_likelihood_scores[s] = 0.0001 # 完全に0だと割り算で問題が出るので微小な値
        elif strong_fixed_setting == '設定5以上':
            for s in ['設定5', '設定6']: setting_likelihood_scores[s] = max(1000, setting_likelihood_scores[s] * 2)
        elif strong_fixed_setting == '設定4以上':
            for s in ['設定4', '設定5', '設定6']: setting_likelihood_scores[s] = max(1000, setting_likelihood_scores[s] * 2)
        elif strong_fixed_setting == '設定3以上':
            for s in ['設定3', '設定4', '設定5', '設定6']: setting_likelihood_scores[s] = max(500, setting_likelihood_scores[s] * 1.5)
        elif strong_fixed_setting == '設定2以上':
            for s in ['設定2', '設定3', '設定4', '設定5', '設定6']: setting_likelihood_scores[s] = max(500, setting_likelihood_scores[s] * 1.5)

    # 全てのスコアが0の場合の処理 (微小な値を入れたので不要になる可能性あり)
    total_score_sum = sum(setting_likelihood_scores.values())
    if total_score_sum == 0 or total_score_sum < 0.01: # ほぼ0の場合も考慮
        st.info("現時点では判断できる材料が少ないか、相殺する要素が多いです。")
        st.write("各設定の可能性:")
        for s in setting_likelihood_scores.keys():
            st.write(f"- {s}: 0.00%")
        st.write("**高設定期待度: 0.00%**")
    else:
        # 各設定の可能性パーセンテージを計算
        st.write("**各設定の可能性 (私の裁量による目安):**")
        probabilities = {}
        for s, score in setting_likelihood_scores.items():
            prob = (score / total_score_sum) * 100
            probabilities[s] = prob
            st.write(f"- **{s}: {prob:.2f}%**")

        # 高設定期待度（設定4,5,6の合計）
        high_setting_prob = probabilities.get('設定4', 0) + probabilities.get('設定5', 0) + probabilities.get('設定6', 0)
        st.markdown(f"**### 高設定期待度: {high_setting_prob:.2f}%**")

        # 総合的なメッセージ
        if high_setting_prob >= 80:
            st.success("🎉 高設定（特に設定6）である可能性が非常に高いです！🎉")
        elif high_setting_prob >= 60:
            st.success("✨ 高設定である可能性が高いです！✨")
        elif high_setting_prob >= 40:
            st.warning("👍 中間設定以上、または高設定に期待できる要素があります。")
        else:
            st.error("👎 低設定である可能性が高いか、高設定を否定する要素が見られます。")

    st.markdown("---")
    st.write("**詳細な示唆内容:**")
    # 各示唆内容をまとめる処理
    final_indications = []
    
    # AT初当たり
    if total_games > 0 and at_first_hit_count > 0:
        final_indications.append(f"ボーナス(AT)初当たり確率: 1/{at_first_hit_rate:.2f}")

    # CZ当選周期
    if st.session_state.quest_periods:
        for entry in st.session_state.quest_periods:
            period = entry['period']
            if period == 1: final_indications.append(f"{period}周期目当選（天国示唆）。")
            else: final_indications.append(f"{period}周期目当選。")

    # ライズゾーン当選率
    if rz_weak_trigger_total > 0:
        final_indications.append(f"ライズゾーン当選率(弱チェ・スイカ): {rz_rate_observed:.2%}")

    # 3枚ベルからの高確移行率
    if bell_total_count > 0:
        final_indications.append(f"3枚ベルからの高確移行率: {bell_trans_rate_observed:.2%}")

    # アイルーだるま落とし
    if st.session_state.ailu_replay_data:
        for entry in st.session_state.ailu_replay_data:
            if entry['replays'] != '選択なし': final_indications.append(f"アイルーだるま落とし{entry['replays']}回で当選。")

    # ボーナス確定画面
    for screen, count in bonus_kakutei_counts.items():
        if count > 0: final_indications.append(f"確定画面「{screen}」({count}回)。")

    # ボーナス終了画面
    for screen, count in bonus_end_counts.items():
        if count > 0: final_indications.append(f"終了画面「{screen}」({count}回)。")

    # エンタトロフィー
    if entaro_color != '選択なし': final_indications.append(f"エンタトロフィー「{entaro_color}」。")

    # おみくじ
    if omikuji_color != '選択なし': final_indications.append(f"おみくじの色「{omikuji_color}」。")

    # ボーナスボイス
    for voice, count in bonus_voice_counts.items():
        if count > 0: final_indications.append(f"図柄揃いボイス「{voice}」({count}回)。")

    # ウツシヒノエボイス
    for voice, count in utsushi_hinoe_voice_counts.items():
        if count > 0: final_indications.append(f"ウツシ/ヒノエボイス「{voice}」({count}回)。")

    # ボーナス入賞後ボイス
    for pattern, count in bonus_nyusho_counts.items():
        if count > 0: final_indications.append(f"入賞後ボイス「{pattern}」({count}回)。")
    
    # AT直撃
    if direct_hit_count > 0: final_indications.append(f"共通ベル直撃({direct_hit_count}回)。")

    # 外部要因
    if external_score_multiplier > 0.05: final_indications.append("店舗・外部要因で期待度増加。")
    elif external_score_multiplier < -0.05: final_indications.append("店舗・外部要因で期待度減少。")
    if other_machine_status: final_indications.append(f"その他: {other_machine_status}")


    if final_indications:
        for ind in final_indications:
            st.write(f"- {ind}")
    else:
        st.write("現時点では特段の示唆はありません。")

    st.write("\n_※表示される数値は、提供された情報と私の裁量による重み付けに基づいた「可能性の目安」です。実際の統計的な確率ではありませんので、最終的な判断はご自身の責任で行ってください。_")