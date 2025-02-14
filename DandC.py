import os
import json
import subprocess
import csv
import re
import yt_dlp
import gc

def sanitize_filename(text):
    sanitized = re.sub(r'[\\/*?:"<>|]', "", text)
    sanitized = sanitized.strip().replace(" ", "_")
    return sanitized[:50]

def log_progress(video_id, status, progress_file):
    with open(progress_file, 'a', encoding='utf-8') as f:
        f.write(f"{status}: {video_id}\n")

def download_video(video_url, ydl_opts):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return True
    except Exception as e:
        print(f"下載影片時發生錯誤：{e}")
        return False

def cut_segments(input_file, segments, output_dir, video_id, csv_writer):
    start_times = segments['start']
    end_times = segments['end']
    texts = segments['text']
    
    for i, (start, end, seg_text) in enumerate(zip(start_times, end_times, texts)):
        safe_text = sanitize_filename(seg_text)
        output_file = os.path.join(output_dir, f"{video_id}_segment_{i+1}_{safe_text}.mp4")
        csv_writer.writerow([video_id, output_file, seg_text])
        
        # 使用 ffmpeg 重新編碼確保裁剪起始處有完整畫面
        command = [
            "-i", input_file,
            "-ss", str(start),
            "-to", str(end),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            output_file
        ]
        print("執行命令:", " ".join(command))
        subprocess.run(command, check=True)

def process_video(video_id, segments, input_dir, output_dir, progress_file, ydl_opts, csv_writer):
    print(f"開始處理影片: {video_id}")
    log_progress(video_id, "Processing", progress_file)
    
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"開始下載影片: {video_url}")
    if not download_video(video_url, ydl_opts):
        print(f"下載影片 {video_id} 時失敗，跳過此影片")
        return
    
    input_file = os.path.join(input_dir, f"{video_id}.mp4")
    if not os.path.exists(input_file):
        print(f"影片 {video_id} 未下載成功，跳過裁剪")
        return
    
    print(f"影片 {video_id} 下載完成！")
    print(f"開始裁剪影片 {video_id} 的片段...")
    cut_segments(input_file, segments, output_dir, video_id, csv_writer)
    print(f"影片 {video_id} 裁剪完成！\n")
    
    try:
        os.remove(input_file)
        print(f"原始影片 {input_file} 已刪除。")
    except Exception as e:
        print(f"刪除原始影片 {input_file} 時發生錯誤：{e}")
        
    log_progress(video_id, "Completed", progress_file)
    gc.collect()

def main():
    # 設定下載與裁剪的資料夾
    input_dir = r"/home/user/Desktop/CCNIU/HowTo100M/video"
    output_dir = r"/home/user/Desktop/CCNIU/HowTo100M/video"
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # 進度紀錄檔案
    progress_file = os.path.join(output_dir, "progress.txt")
    with open(progress_file, 'w', encoding='utf-8') as f:
        f.write("影片處理進度記錄\n")
        
    # 讀取 JSON 內容 (檔案名稱為 caption1.json)
    with open('caption1.json', 'r', encoding='utf-8') as f:
        segment_data = json.load(f)
        
    # 取出所有影片 ID，不再限制 50 個
    video_ids = list(segment_data.keys())
    
    # yt-dlp 選項：先合併為 MKV，再轉換為 MP4
    ydl_opts = {
        'outtmpl': os.path.join(input_dir, '%(id)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mkv',
        'ignoreerrors': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }
    
    csv_file = os.path.join(output_dir, "segments_mapping.csv")
    with open(csv_file, 'w', encoding='utf-8', newline='') as f_csv:
        csv_writer = csv.writer(f_csv)
        csv_writer.writerow(["VideoID", "SegmentFile", "SegmentText"])
        
        for video_id in video_ids:
            if video_id in segment_data:
                process_video(video_id, segment_data[video_id], input_dir, output_dir, progress_file, ydl_opts, csv_writer)
    
    print(f"CSV 對照表已儲存為 {csv_file}")

if __name__ == '__main__':
    main()
