import os
import json
import subprocess
import csv
import re
import yt_dlp
import gc
import logging
from multiprocessing import Pool, Lock

# 定義 po token
PO_TOKEN = "MlvBR-hjU7IVU8F_T56lpxhYy_2P2eeafyDmeugoSmJv9PRKcUNOfzL-fneecAn-c_vBIksKwl0K4EWhH1Fl0ECN9EmGHAZwntDpFby6TgFpVW94BYoBVtdFXK9G"

# 設定 logging，記錄 INFO 等級以上的訊息
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 全域設定
INPUT_DIR = r"/home/user/Desktop/CCNIU/HowTo100M/video"
Pro_DIR = r"/home/user/Desktop/CCNIU/HowTo100M"
OUTPUT_DIR = r"/home/user/Desktop/SCLAB_NAS/Dataset/Howto100M"
PROGRESS_FILE = os.path.join(Pro_DIR, "progress.txt")

# yt-dlp 選項ls
YDL_OPTS = {
    'outtmpl': os.path.join(INPUT_DIR, '%(id)s.%(ext)s'),
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'merge_output_format': 'mkv',
    'ignoreerrors': True,
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
    }],
    'verbose': True,
    # 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'cookiesfrombrowser': ('chrome',),  # Match --cookies-from-browser chrome
    'extractor_args': {
        'youtube': {
            'po_token': ['web.gvs+MltZuO5XYRaft1mASaqXA5K8UwKJ7dU-9cR-he4ceMblEGy1d3d827ga5oiYRDta-R9Z3U0-8PmABN1eGWVXdMppbLaN1Dg4Udu6iRLlmifFllpa0psjffHiJ05J']
        }
    }
}


# 多進程寫進度時使用的鎖
progress_lock = Lock()

def sanitize_filename(text):
    sanitized = re.sub(r'[\\/*?:"<>|]', "", text)
    sanitized = sanitized.strip().replace(" ", "_")
    return sanitized[:50]

def log_progress(video_id, status):
    with progress_lock:
        with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{status}: {video_id}\n")
    logging.info(f"{status}: {video_id}")

def download_video(video_url, retries=2):
    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                logging.info(f"下載影片: {video_url} (嘗試 {attempt+1} 次)")
                ydl.download([video_url])
            return True
        except Exception as e:
            logging.error(f"下載影片 {video_url} 發生錯誤：{e} (嘗試 {attempt+1} 次)", exc_info=True)
    return False

def cut_segments(input_file, segments, video_id):
    rows = []
    start_times = segments['start']
    end_times = segments['end']
    texts = segments['text']
    for i, (start, end, seg_text) in enumerate(zip(start_times, end_times, texts)):
        safe_text = sanitize_filename(seg_text)
        output_file = os.path.join(OUTPUT_DIR, f"{video_id}_segment_{i+1}_{safe_text}.mp4")
        rows.append([video_id, output_file, seg_text])
        # 注意：命令列表第一個項目必須是 ffmpeg 執行檔
        command = [
            "ffmpeg",
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
        logging.info(f"執行命令: {' '.join(command)}")
        try:
            subprocess.run(command, check=True, timeout=600)
        except subprocess.TimeoutExpired:
            logging.error(f"裁剪影片 {video_id} 片段 {i+1} 超時")
        except subprocess.CalledProcessError as e:
            logging.error(f"裁剪影片 {video_id} 片段 {i+1} 失敗: {e}")
    return rows

def process_video_worker(args):
    video_id, segments = args
    log_progress(video_id, "Processing")
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    logging.info(f"開始下載影片: {video_url}")
    if not download_video(video_url):
        logging.error(f"下載影片 {video_id} 時失敗，跳過")
        return []  # 回傳空的 CSV 列表
    input_file = os.path.join(INPUT_DIR, f"{video_id}.mp4")
    if not os.path.exists(input_file):
        logging.error(f"影片 {video_id} 未下載成功，跳過裁剪")
        return []
    logging.info(f"影片 {video_id} 下載完成！開始裁剪...")
    try:
        rows = cut_segments(input_file, segments, video_id)
    except Exception as e:
        logging.error(f"裁剪影片 {video_id} 時發生錯誤: {e}")
        rows = []
    try:
        os.remove(input_file)
        logging.info(f"原始影片 {input_file} 已刪除。")
    except Exception as e:
        logging.error(f"刪除原始影片 {input_file} 時發生錯誤：{e}")
    log_progress(video_id, "Completed")
    gc.collect()
    return rows

def get_completed_video_ids():
    """讀取已完成的影片 ID（從進度檔中）"""
    completed = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("Completed:"):
                    # 格式 "Completed: video_id"
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        vid = parts[1].strip()
                        completed.add(vid)
    return completed

def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # 初始化進度記錄檔
    if not os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            f.write("影片處理進度記錄\n")
    
    # 讀取 JSON 內容 (檔名為 caption1.json)
    with open('caption1.json', 'r', encoding='utf-8') as f:
        segment_data = json.load(f)
    
    # 取得已完成的影片 ID，跳過這些項目
    completed_ids = get_completed_video_ids()
    logging.info(f"已完成影片: {completed_ids}")
    
    video_ids = list(segment_data.keys())
    # 過濾已完成的影片
    tasks = [(video_id, segment_data[video_id]) for video_id in video_ids if video_id not in completed_ids]
    logging.info(f"待處理影片數量: {len(tasks)}")
    
    csv_rows = []
    logging.info("開始多進程處理影片")
    try:
        # 限制同時處理的進程數為 1
        with Pool(processes=1) as pool:
            for result in pool.imap_unordered(process_video_worker, tasks):
                csv_rows.extend(result)
    except KeyboardInterrupt:
        logging.error("收到 KeyboardInterrupt，終止多進程池")
    
    csv_file = os.path.join(OUTPUT_DIR, "segments_mapping.csv")
    with open(csv_file, 'w', encoding='utf-8', newline='') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["VideoID", "SegmentFile", "SegmentText"])
        writer.writerows(csv_rows)
    logging.info(f"CSV 對照表已儲存為 {csv_file}")

if __name__ == '__main__':
    main()
    # test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    # download_video(test_url)
