import streamlit as st
from openai import OpenAI
import json
import itertools
import math

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="AI 경로 네비게이션 앱",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ AI 최적 경로 네비게이션")
st.markdown("목적지를 여러 개 입력하면 **최적 이동 동선**을 계산해드립니다.")

# =========================
# OpenAI 클라이언트 설정
# =========================
if "OPENAI_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 OPENAI_API_KEY를 설정하세요.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =========================
# 거리 계산 함수 (유클리드 거리)
# =========================
def calculate_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def find_optimal_route(locations):
    """
    단순 완전탐색 (목적지 8개 이하 권장)
    """
    min_distance = float("inf")
    best_route = None

    for perm in itertools.permutations(locations):
        total_dist = 0
        for i in range(len(perm) - 1):
            total_dist += calculate_distance(perm[i][1], perm[i + 1][1])
        if total_dist < min_distance:
            min_distance = total_dist
            best_route = perm

    return best_route, min_distance

# =========================
# GPT 위치 좌표 생성
# =========================
def get_coordinates_from_gpt(place_names):
    prompt = f"""
    다음 장소들의 위도와 경도를 JSON 형식으로 반환하세요.
    형식:
    [
        {{"name": "장소명", "lat": 위도, "lon": 경도}}
    ]

    장소 목록:
    {", ".join(place_names)}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "정확한 좌표를 JSON으로 반환하세요."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        data = json.loads(content)
        return data
    except:
        st.error("GPT 응답 파싱 실패. 다시 시도하세요.")
        return None

# =========================
# UI 입력 영역
# =========================
st.subheader("📍 목적지 입력")

place_input = st.text_area(
    "여러 목적지를 한 줄에 하나씩 입력하세요 (최대 8개 권장)",
    height=150
)

if st.button("🚀 최적 경로 계산하기"):

    if not place_input.strip():
        st.warning("목적지를 입력하세요.")
        st.stop()

    place_names = [p.strip() for p in place_input.split("\n") if p.strip()]

    if len(place_names) < 2:
        st.warning("최소 2개 이상의 목적지를 입력하세요.")
        st.stop()

    if len(place_names) > 8:
        st.warning("목적지는 8개 이하로 입력하세요.")
        st.stop()

    with st.spinner("📡 위치 정보 분석 중..."):

        coordinates = get_coordinates_from_gpt(place_names)

        if not coordinates:
            st.stop()

        locations = []
        for item in coordinates:
            locations.append(
                (
                    item["name"],
                    (float(item["lat"]), float(item["lon"]))
                )
            )

        best_route, total_distance = find_optimal_route(locations)

    st.success("✅ 최적 경로 계산 완료!")

    st.subheader("📌 추천 방문 순서")

    for i, loc in enumerate(best_route, 1):
        st.write(f"{i}. {loc[0]}")

    st.subheader("📏 총 이동 거리 (직선 기준)")
    st.write(f"{total_distance:.4f} 단위")

    # 지도 표시
    st.subheader("🗺️ 지도 시각화")

    map_data = [
        {"lat": loc[1][0], "lon": loc[1][1]}
        for loc in best_route
    ]

    st.map(map_data)
