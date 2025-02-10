import json
import subprocess
import csv
import re
import yt_dlp
import os

def sanitize_filename(text):
    """
    將文字轉為合法的檔名：
    - 移除非法字符 (例如 \ / * ? : " < > |)
    - 將空白轉為底線
    - 限制長度 (這裡限制為 50 個字元，可依需求調整)
    """
    sanitized = re.sub(r'[\\/*?:"<>|]', "", text)
    sanitized = sanitized.strip().replace(" ", "_")
    return sanitized[:50]

# 讀取 JSON 內容 (假設檔案名稱為 video_segments.json)
with open('video_segments.json', 'r', encoding='utf-8') as f:
    segment_data = json.load(f)

# 取出 JSON 中的所有影片 ID，並限制只處理前 50 個
video_ids = list(segment_data.keys())[:50]

# 用來存放所有裁剪後的片段資訊，將寫入 CSV 對照表
csv_rows = []

# 依序處理每個影片 ID
for video_id in video_ids:
    # 組成影片 URL (例如 https://www.youtube.com/watch?v=nVbIUDjzWY4)
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"開始下載影片: {video_url}")
    
    # yt-dlp 選項：用影片 ID 當作檔名、指定合併後格式為 mp4
    ydl_opts = {
        'outtmpl': '%(id)s.%(ext)s',  # 下載後檔名例如 nVbIUDjzWY4.mp4
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'ignoreerrors': True,  # 當遇到錯誤時跳過該影片
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        print(f"下載影片 {video_id} 時發生錯誤：{e}，跳過此影片")
        continue

    # 檢查檔案是否下載成功
    input_file = f"{video_id}.mp4"
    if not os.path.exists(input_file):
        print(f"影片 {video_id} 未下載成功，跳過裁剪")
        continue

    print(f"影片 {video_id} 下載完成！")
    
    # 取得對應的片段資訊 (開始時間、結束時間、文字)
    segments = segment_data[video_id]
    start_times = segments['start']
    end_times = segments['end']
    texts = segments['text']
    
    # 依序裁剪影片的每個片段
    print(f"開始裁剪影片 {video_id} 的片段...")
    for i, (start, end, seg_text) in enumerate(zip(start_times, end_times, texts)):
        # 以文字建立安全的檔名 (避免非法字元)
        safe_text = sanitize_filename(seg_text)
        # 這裡檔名加入影片 ID、片段編號以及文字 (可自行調整格式)
        output_file = f"{video_id}_segment_{i+1}_{safe_text}.mp4"
        # 將本筆資料存入 CSV 列表
        csv_rows.append([video_id, output_file, seg_text, start, end])
        
        # 使用 ffmpeg 裁剪影片
        # 此處採用：視頻流直接複製；音訊流轉換為 AAC (解決 OPUS 與 MP4 相容性問題)
        command = [
            r"C:\Program Files\FFMPEG\bin\ffmpeg.exe",  # 使用原始字串指定 ffmpeg 的完整路徑
            "-i", input_file,
            "-ss", str(start),
            "-to", str(end),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            output_file
        ]
        print("執行命令:", " ".join(command))
        subprocess.run(command)
    print(f"影片 {video_id} 裁剪完成！\n")

# 將所有片段的資訊寫入 CSV 檔案作為對照表
csv_file = "segments_mapping.csv"
with open(csv_file, 'w', encoding='utf-8', newline='') as f_csv:
    writer = csv.writer(f_csv)
    writer.writerow(["VideoID", "SegmentFile", "SegmentText", "Start", "End"])  # CSV 標題
    writer.writerows(csv_rows)
print(f"CSV 對照表已儲存為 {csv_file}")
