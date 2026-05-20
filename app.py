import os, uuid, glob, subprocess, threading, json
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
jobs = {}

def run_download(job_id, url, format_choice, format_id):
    job = jobs[job_id]
    out_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")
    cmd = ["yt-dlp", "--no-playlist", "-o", out_template]
    if format_choice == "audio":
        cmd += ["-x", "--audio-format", "mp3"]
    elif format_id:
        cmd += ["-f", f"{format_id}+bestaudio/best", "--merge-output-format", "mp4"]
    else:
        cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            job["status"] = "error"
            job["error"] = result.stderr.strip().split("\n")[-1]
            return
        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*"))
        if not files:
            job["status"] = "error"
            job["error"] = "No file created"
            return
        if format_choice == "audio":
            chosen = next((f for f in files if f.endswith(".mp3")), files[0])
        else:
            chosen = next((f for f in files if f.endswith(".mp4")), files[0])
        for f in files:
            if f != chosen:
                try: os.remove(f)
                except: pass
        job["status"] = "done"
        job["file"] = chosen
        title = job.get("title", "").strip()
        if title:
            safe = "".join(c for c in title if c not in r'\/:*?"<>|')[:20]
            ext = os.path.splitext(chosen)[1]
            job["filename"] = f"{safe}{ext}" if safe else os.path.basename(chosen)
        else:
            job["filename"] = os.path.basename(chosen)
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)

@app.route("/api/info", methods=["POST"])
def get_info():
    url = request.json.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL"}), 400
    cmd = ["yt-dlp", "--no-playlist", "-j", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return jsonify({"error": result.stderr.strip().split("\n")[-1]}), 400
        info = json.loads(result.stdout)
        best_by_height = {}
        for f in info.get("formats", []):
            h = f.get("height")
            if h and f.get("vcodec", "none") != "none":
                tbr = f.get("tbr", 0)
                if h not in best_by_height or tbr > best_by_height[h].get("tbr", 0):
                    best_by_height[h] = f
        formats = [{"id": f["format_id"], "label": f"{h}p", "height": h}
                   for h, f in sorted(best_by_height.items(), reverse=True)]
        return jsonify({
            "title": info.get("title", ""),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration"),
            "uploader": info.get("uploader", ""),
            "formats": formats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    format_choice = data.get("format", "video")
    format_id = data.get("format_id")
    title = data.get("title", "")
    if not url:
        return jsonify({"error": "No URL"}), 400
    job_id = uuid.uuid4().hex[:10]
    jobs[job_id] = {"status": "downloading", "url": url, "title": title}
    thread = threading.Thread(target=run_download, args=(job_id, url, format_choice, format_id))
    thread.daemon = True
    thread.start()
    return jsonify({"job_id": job_id})

@app.route("/api/status/<job_id>")
def check_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"status": job["status"], "error": job.get("error"), "filename": job.get("filename")})

@app.route("/api/file/<job_id>")
def download_file(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return jsonify({"error": "File not ready"}), 404
    return send_file(job["file"], as_attachment=True, download_name=job["filename"])