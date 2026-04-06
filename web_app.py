import streamlit as st
import gpxpy
from PIL import Image, ImageDraw, ImageFont
from datetime import timedelta
import folium
import io
import urllib.request
import os

# --- 網頁標題與設定 ---
st.set_page_config(page_title="阿福林道分析器", page_icon="🏍️")
st.title("阿福林道軌跡分析器 🏍️")
st.write("把你的 GPX 檔案傳上來，一秒產出 IG 限動專屬紀錄卡！")

# --- 1. 檔案上傳區 ---
uploaded_file = st.file_uploader("點擊這裡上傳 GPX 檔案", type=["gpx"])

if uploaded_file is not None:
    st.success("✅ 檔案讀取成功！正在產生圖表...")
    
    gpx = gpxpy.parse(uploaded_file)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for p in segment.points:
                points.append((p.latitude, p.longitude))

    if points:
        dist_km = gpx.length_2d() / 1000
        uphill, downhill = gpx.get_uphill_downhill()
        elev_gain = uphill if uphill is not None else 0
        
        start_time, end_time = gpx.get_time_bounds()
        date_str = start_time.strftime("%Y-%m-%d") if start_time else "未知日期"
        duration = (end_time - start_time) if (start_time and end_time) else timedelta(0)
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        duration_str = f"{hours}h {minutes}m"

        # ==========================================
        # --- 網頁顯示區塊 1：超大地圖 ---
        # ==========================================
        st.subheader("🗺️ 軌跡地圖")
        my_map = folium.Map(location=[points[0][0], points[0][1]], zoom_start=13)
        folium.PolyLine(points, color="red", weight=5).add_to(my_map)
        st.components.v1.html(my_map._repr_html_(), height=600)

        st.divider()

        # ==========================================
        # --- 產出 IG 限動去背圖 (PNG) ---
        # ==========================================
        SCALE_FACTOR = 2
        base_w, base_h = 1080, 1920
        high_res_w = base_w * SCALE_FACTOR
        high_res_h = base_h * SCALE_FACTOR
        
        high_res_img = Image.new("RGBA", (high_res_w, high_res_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(high_res_img)

        # ==========================================
        # --- 【字體神救援】自動下載 Google 高畫質字體 ---
        # ==========================================
        font_path = "Roboto-Bold.ttf"
        # 如果發現沒有字體，就自動下載！
        if not os.path.exists(font_path):
            font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
            urllib.request.urlretrieve(font_url, font_path)

        title_size = 45 * SCALE_FACTOR
        value_size = 110 * SCALE_FACTOR
        
        # 霸氣直接使用載下來的高畫質字體！
        font_title = ImageFont.truetype(font_path, title_size)
        font_value = ImageFont.truetype(font_path, value_size)

        def draw_centered_text(y_base, text, font, color=(255, 255, 255, 255)):
            y_high_res = y_base * SCALE_FACTOR
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            x_high_res = (high_res_w - text_w) / 2
            draw.text((x_high_res, y_high_res), text, fill=color, font=font)

        draw_centered_text(280, "Distance", font_title)
        draw_centered_text(340, f"{dist_km:.2f} km", font_value)
        draw_centered_text(580, "Elevation Gain", font_title)
        draw_centered_text(640, f"{elev_gain:,.0f} m", font_value)
        draw_centered_text(880, "Time", font_title)
        draw_centered_text(940, duration_str, font_value)

        lats, lons = zip(*points)
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        base_area_w, base_area_h = 800, 600
        high_res_area_w = base_area_w * SCALE_FACTOR
        high_res_area_h = base_area_h * SCALE_FACTOR
        
        offset_x = (high_res_w - high_res_area_w) / 2
        offset_y = 1200 * SCALE_FACTOR
        
        lon_range = max_lon - min_lon if max_lon != min_lon else 1
        lat_range = max_lat - min_lat if max_lat != min_lat else 1
        scale = min(high_res_area_w / lon_range, high_res_area_h / lat_range)
        
        pixel_points = []
        for lat, lon in points:
            x = offset_x + (lon - min_lon) * scale + (high_res_area_w - lon_range * scale) / 2
            y = offset_y + high_res_area_h - (lat - min_lat) * scale - (high_res_area_h - lat_range * scale) / 2
            pixel_points.append((x, y))
        
        strava_orange = (252, 76, 2, 255)
        draw.line(pixel_points, fill=strava_orange, width=12 * SCALE_FACTOR, joint="round")

        # --- 高品質縮小 (抗鋸齒魔法) ---
        img_final = high_res_img.resize((base_w, base_h), Image.Resampling.LANCZOS)

        # ==========================================
        # --- 網頁顯示區塊 2：限動紀錄卡 ---
        # ==========================================
        st.subheader("📸 限動紀錄卡")
        st.image(img_final, use_container_width=True)
        
        buf = io.BytesIO()
        img_final.save(buf, format="PNG")
        st.download_button(
            label="📥 下載高清去背圖",
            data=buf.getvalue(),
            file_name=f"{date_str}_阿福限動.png",
            mime="image/png"
        )

    else:
        st.error("這份檔案裡面找不到軌跡資料喔！")