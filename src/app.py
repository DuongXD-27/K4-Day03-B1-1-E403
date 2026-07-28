"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tools import search_rentals, AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    import re
    
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    # Lịch sử hội thoại bắt đầu với query của người dùng
    history = f"User: {user_query}"
    
    step = 0
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM với lịch sử hiện tại và system prompt
        response = provider.generate(history, system_prompt=REACT_SYSTEM_PROMPT)
        print(response)
        
        # Thêm phản hồi của LLM vào lịch sử
        history += f"\n{response}"
        
        # Kiểm tra xem AI đã chốt câu trả lời chưa
        if "Final Answer:" in response:
            break
            
        # Tìm cú pháp gọi Action bằng Regex
        # Phù hợp dạng: Action: search_rentals["Cầu Giấy", "điều hòa", ...]
        action_match = re.search(r"Action:\s*(\w+)\[(.*)\]", response, re.DOTALL)
        
        if action_match:
            tool_name = action_match.group(1).strip()
            params_str = action_match.group(2).strip()
            
            # Parse tham số thành list Python
            try:
                # Đổi nháy đơn thành nháy kép và None thành null để json.loads xử lý được
                safe_params_str = params_str.replace("'", '"').replace("None", "null")
                params = json.loads(f"[{safe_params_str}]")
            except Exception:
                # Nếu LLM sinh lỗi format, dùng cơ chế tách chuỗi thủ công làm Fallback
                params = [p.strip().strip('"').strip("'") for p in params_str.split(",")]
                for i, p in enumerate(params):
                    if p.lower() in ("null", "none", ""):
                        params[i] = None
                    elif p.isdigit():
                        params[i] = int(p)
                    else:
                        try:
                            params[i] = float(p)
                        except ValueError:
                            pass
                            
            # Thực thi Tool
            if tool_name in AVAILABLE_TOOLS:
                print(f"⚙️ System Executing: {tool_name} with args {params}")
                tool_func = AVAILABLE_TOOLS[tool_name]
                try:
                    obs = tool_func(*params)
                except Exception as e:
                    obs = f"Error: {str(e)}"
            else:
                obs = f"Error: Không tìm thấy công cụ '{tool_name}'."
                
            # In ra và đưa Observation trở lại ngữ cảnh cho bước tiếp theo
            print(f"👁️ Observation: {obs}")
            history += f"\nObservation: {obs}\n"
        else:
            warning = "System Warning: Không tìm thấy lệnh 'Action:'. Hãy đảm bảo bạn dùng đúng định dạng hoặc kết thúc bằng 'Final Answer:'."
            print(f"⚠️ {warning}")
            history += f"\n{warning}\n"
            
    if step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


def run_react_agent_stream(user_query: str, provider):
    """
    Generator yield từng bước của ReAct Agent để đẩy qua Server-Sent Events (SSE).
    """
    import re
    history = f"User: {user_query}"
    step = 0
    while step < MAX_ITERATIONS:
        step += 1
        yield {"type": "step", "content": f"--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---"}
        
        response = provider.generate(history, system_prompt=REACT_SYSTEM_PROMPT)
        history += f"\n{response}"
        
        if "Final Answer:" in response:
            final_ans = response.split("Final Answer:")[-1].strip()
            yield {"type": "final_answer", "content": final_ans, "raw": response}
            break
            
        action_match = re.search(r"Action:\s*(\w+)\[(.*)\]", response, re.DOTALL)
        
        if action_match:
            tool_name = action_match.group(1).strip()
            params_str = action_match.group(2).strip()
            
            # Trích xuất đoạn Thought để hiển thị lên UI
            thought_match = re.search(r"Thought:\s*(.*?)\nAction:", response, re.DOTALL)
            thought_text = thought_match.group(1).strip() if thought_match else "Đang suy nghĩ..."
            yield {"type": "thought", "content": thought_text, "raw": response}
            
            yield {"type": "action", "content": f"Đang gọi công cụ: {tool_name}[{params_str}]"}
            
            try:
                safe_params_str = params_str.replace("'", '"').replace("None", "null")
                params = json.loads(f"[{safe_params_str}]")
            except Exception:
                params = [p.strip().strip('"').strip("'") for p in params_str.split(",")]
                for i, p in enumerate(params):
                    if p.lower() in ("null", "none", ""):
                        params[i] = None
                    elif p.isdigit():
                        params[i] = int(p)
                    else:
                        try:
                            params[i] = float(p)
                        except ValueError:
                            pass
                            
            if tool_name in AVAILABLE_TOOLS:
                tool_func = AVAILABLE_TOOLS[tool_name]
                try:
                    obs = tool_func(*params)
                except Exception as e:
                    obs = f"Error: {str(e)}"
            else:
                obs = f"Error: Không tìm thấy công cụ '{tool_name}'."
                
            yield {"type": "observation", "content": str(obs)}
            history += f"\nObservation: {obs}\n"
        else:
            warning = "System Warning: Không tìm thấy lệnh 'Action:'. Hãy đảm bảo bạn dùng đúng định dạng hoặc kết thúc bằng 'Final Answer:'."
            yield {"type": "warning", "content": warning, "raw": response}
            history += f"\n{warning}\n"
            
    if step >= MAX_ITERATIONS:
        yield {"type": "warning", "content": f"Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!"}

if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Chạy thử câu test số 3
    sample_query = tests[2]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
