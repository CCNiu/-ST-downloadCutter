import json
import subprocess
import csv
import re

# 假設 JSON 內容存放在 'video_segments.json' 文件中
with open('video_segments.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
print("open finish.")

video_id = list(data.keys())[0]  # 這裡取得第一個影片ID，例如 "nVbIUDjzWY4"
segments = data[video_id]

start_times = segments['start']
end_times = segments['end']
texts = segments['text']  # 可用來作為檔名的一部分或參考

# 假設下載好的影片檔名為 video_id.mp4
input_file = f"{video_id}.mp4"

# 準備建立 CSV 對照表
csv_rows = []  # 用來存放每筆資料：檔名、原始文字、start、end

for i, (start, end, seg_text) in enumerate(zip(start_times, end_times, texts)):
    # output_file = f"{video_id}_segment_{i+1}.mp4"
    output_file = f"{video_id}_segment_{i+1}_{seg_text}.mp4"
    
    csv_rows.append([output_file, seg_text, start, end])
    
    # 使用 ffmpeg 命令剪輯影片
    command = [
        r"C:\Program Files\FFMPEG\bin\ffmpeg.exe",
        "-i", input_file,
        "-ss", str(start),
        "-to", str(end),
        "-c:v", "copy",
        "-c:a", "aac",    # 音訊流轉換為 AAC
        "-b:a", "128k",   # 設定音訊比特率為 128 kbps
        output_file
    ]
    print("執行命令:", " ".join(command))
    subprocess.run(command)
print("影片裁剪完成！")

# 將 CSV 對照表寫入檔案，例如 "segments_mapping.csv"
csv_file = "segments_mapping.csv"
with open(csv_file, 'w', encoding='utf-8', newline='') as f_csv:
    writer = csv.writer(f_csv)
    writer.writerow(["FileName", "SegmentText", "Start", "End"])  # CSV 標題
    writer.writerows(csv_rows)
print(f"CSV 對照表已儲存為 {csv_file}")
