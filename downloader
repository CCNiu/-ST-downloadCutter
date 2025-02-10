import yt_dlp

# 定義下載選項
ydl_opts = {
    'outtmpl': '%(title)s.%(ext)s',  # 輸出檔名模板
    'format': 'bestvideo+bestaudio/best',  # 選擇最佳畫質和音訊
    'ffmpeg_location': r'C:\Program Files\FFMPEG\bin',  # 指定 ffmpeg 的安裝路徑
    'merge_output_format': 'mp4',  # 指定合併後的格式為 mp4
    # 若需要自定義其他選項，可參考官方文檔
}

# 影片 URL
video_url = "https://www.youtube.com/watch?v=nVbIUDjzWY4"

# 使用 yt_dlp.YoutubeDL 下載影片
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([video_url])
