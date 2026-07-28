import os
import sys
import json
from flask import Flask, request, jsonify, render_template, Response

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from providers import get_llm_provider
from app import run_react_agent_stream

app = Flask(__name__)

# Khởi tạo LLM provider
provider = get_llm_provider()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get('query', '')
    if not user_query:
        return jsonify({"error": "Query cannot be empty"}), 400

    def generate():
        # Dùng generator để stream từng bước (SSE)
        for step_data in run_react_agent_stream(user_query, provider):
            yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"
            
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("🚀 Khởi động Web UI cho ReAct Agent tại http://localhost:5000")
    # Tắt reloader nếu chạy bằng công cụ nội bộ để tránh lỗi cổng
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
