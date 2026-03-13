import streamlit as st
import gpxpy
from PIL import Image, ImageDraw, ImageFont
from datetime import timedelta
import folium
import io

# --- 網頁標題與設定 ---
st.set_page_config(page_title="林道分析", page_icon="🏍️")
st.title("林道軌跡 🏍️")
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
        # --- 網頁顯示區塊 1：超大地圖 (放上面) ---
        # ==========================================
        st.subheader("🗺️ 軌跡地圖")
        my_map = folium.Map(location=[points[0][0], points[0][1]], zoom_start=13)
        folium.PolyLine(points, color="red", weight=5).add_to(my_map)
        
        # 把地圖高度拉高到 600，視覺更滿版
        st.components.v1.html(my_map._repr_html_(), height=600)

        st.divider() # 加一條帥氣的分隔線

        # ==========================================
        # --- 產出 IG 限動去背圖 (PNG) ---
        # ==========================================
        img_w, img_h = 1080, 1920
        img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype("arial.ttf", 45)
            font_value = ImageFont.truetype("arialbd.ttf", 110) 
        except:
            font_title = ImageFont.load_default()
            font_value = ImageFont.load_default()

        def draw_centered_text(y, text, font, color=(255, 255, 255, 255)):
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            x = (img_w - text_w) / 2
            draw.text((x, y), text, fill=color, font=font)

        draw_centered_text(280, "Distance", font_title)
        draw_centered_text(340, f"{dist_km:.2f} km", font_value)
        draw_centered_text(580, "Elevation Gain", font_title)
        draw_centered_text(640, f"{elev_gain:,.0f} m", font_value)
        draw_centered_text(880, "Time", font_title)
        draw_centered_text(940, duration_str, font_value)

        lats, lons = zip(*points)
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        track_area_w, track_area_h = 800, 600
        offset_x = (img_w - track_area_w) / 2
        offset_y = 1200 
        
        lon_range = max_lon - min_lon if max_lon != min_lon else 1
        lat_range = max_lat - min_lat if max_lat != min_lat else 1
        scale = min(track_area_w / lon_range, track_area_h / lat_range)
        
        pixel_points = []
        for lat, lon in points:
            x = offset_x + (lon - min_lon) * scale + (track_area_w - lon_range * scale) / 2
            y = offset_y + track_area_h - (lat - min_lat) * scale - (track_area_h - lat_range * scale) / 2
            pixel_points.append((x, y))
        
        strava_orange = (252, 76, 2, 255)
        draw.line(pixel_points, fill=strava_orange, width=12, joint="round")

        # ==========================================
        # --- 網頁顯示區塊 2：限動紀錄卡 (放下面) ---
        # ==========================================
        st.subheader("📸 紀錄卡")
        
        # 讓圖片自動適應網頁寬度
        st.image(img, use_container_width=True)
        
        # 一鍵下載按鈕
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        st.download_button(
            label="📥 下載高清去背圖",
            data=buf.getvalue(),
            file_name=f"{date_str}_紀錄卡.png",
            mime="image/png"
        )

    else:
        st.error("這份檔案裡面找不到軌跡資料喔！")