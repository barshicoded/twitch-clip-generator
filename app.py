#!/usr/bin/env python3
"""
Web Interface for Twitch Clip Generator
Flask-based UI for easy clip generation
"""

import os
import sys
import json
import uuid
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename

# Import our clip generator
from clip_generator import TwitchClipGenerator

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 * 1024  # 4GB max file size (Render limit)
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', './uploads')
app.config['CLIP_FOLDER'] = os.environ.get('CLIP_FOLDER', './clips')
app.config['SECRET_KEY'] = os.urandom(24)

# Ensure folders exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['CLIP_FOLDER']).mkdir(exist_ok=True)

# Store job status
jobs = {}

# Initialize generator
generator = TwitchClipGenerator(output_dir=app.config['CLIP_FOLDER'])


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/process', methods=['POST'])
def process_vod():
    """Start processing a VOD"""
    data = request.json
    
    vod_url = data.get('url', '').strip()
    if not vod_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    # Validate URL
    if 'twitch.tv' not in vod_url and 'youtube.com' not in vod_url:
        return jsonify({'error': 'Invalid URL. Must be Twitch or YouTube'}), 400
    
    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'id': job_id,
        'status': 'queued',
        'progress': 0,
        'url': vod_url,
        'clips': [],
        'error': None,
        'created_at': datetime.now().isoformat()
    }
    
    # Start processing in background
    thread = threading.Thread(
        target=process_job,
        args=(job_id, vod_url, data)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'message': 'Processing started'
    })


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Upload and process a local video file"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(filepath)
    
    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'id': job_id,
        'status': 'queued',
        'progress': 0,
        'file': filepath,
        'clips': [],
        'error': None,
        'created_at': datetime.now().isoformat()
    }
    
    # Start processing
    thread = threading.Thread(
        target=process_upload_job,
        args=(job_id, filepath, request.form)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'message': 'Upload successful, processing started'
    })


@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get job status"""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job)


@app.route('/api/download/<job_id>/<int:clip_idx>')
def download_clip(job_id, clip_idx):
    """Download a generated clip"""
    job = jobs.get(job_id)
    if not job or clip_idx >= len(job.get('clips', [])):
        return jsonify({'error': 'Clip not found'}), 404
    
    clip_path = job['clips'][clip_idx]
    if not os.path.exists(clip_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        clip_path,
        as_attachment=True,
        download_name=f"clip_{job_id}_{clip_idx + 1}.mp4"
    )


@app.route('/api/clips/<job_id>')
def list_clips(job_id):
    """List all clips for a job"""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    clips = []
    for idx, clip_path in enumerate(job.get('clips', [])):
        if os.path.exists(clip_path):
            # Get video info
            size = os.path.getsize(clip_path)
            clips.append({
                'index': idx,
                'filename': os.path.basename(clip_path),
                'size_mb': round(size / (1024 * 1024), 2),
                'download_url': url_for('download_clip', job_id=job_id, clip_idx=idx)
            })
    
    return jsonify({
        'job_id': job_id,
        'status': job['status'],
        'clips': clips
    })


def process_job(job_id, vod_url, options):
    """Process a VOD job in background"""
    try:
        jobs[job_id]['status'] = 'downloading'
        jobs[job_id]['progress'] = 10
        
        # Process VOD
        clips = generator.process_vod(
            vod_url,
            clip_duration=(
                options.get('min_duration', 15),
                options.get('max_duration', 60)
            ),
            max_clips=options.get('max_clips', 5)
        )
        
        if clips:
            jobs[job_id]['clips'] = clips
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['progress'] = 100
        else:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = 'No clips generated'
            
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)


def process_upload_job(job_id, filepath, options):
    """Process an uploaded file"""
    try:
        jobs[job_id]['status'] = 'processing'
        jobs[job_id]['progress'] = 20
        
        # Process video file directly
        import tempfile
        
        # Get video duration
        duration = generator._get_video_duration(filepath)
        jobs[job_id]['progress'] = 30
        
        # Transcribe
        transcript = generator.transcribe_audio(filepath)
        jobs[job_id]['progress'] = 60
        
        if not transcript.get("segments"):
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = 'No audio/transcription available'
            return
        
        # Find clips
        clips_info = generator.find_viral_moments(
            transcript,
            min_duration=int(options.get('min_duration', 15)),
            max_duration=int(options.get('max_duration', 60))
        )
        jobs[job_id]['progress'] = 80
        
        # Create clips
        output_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, clip in enumerate(clips_info[:int(options.get('max_clips', 5))], 1):
            output_path = os.path.join(
                app.config['CLIP_FOLDER'],
                f"clip_{job_id}_{i}.mp4"
            )
            
            success = generator.create_vertical_video(
                filepath,
                output_path,
                clip["start"],
                clip["end"],
                clip["segments"],
                add_subtitles=True
            )
            
            if success:
                output_files.append(output_path)
        
        jobs[job_id]['clips'] = output_files
        jobs[job_id]['status'] = 'completed' if output_files else 'failed'
        jobs[job_id]['progress'] = 100
        
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)
            
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        # Clean up on error
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == '__main__':
    print("="*60)
    print("Twitch Clip Generator - Web Interface")
    print("="*60)
    print("\nOpen your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
