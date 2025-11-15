import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_KEY")

# Configure the Google API
genai.configure(api_key=GOOGLE_AI_KEY)

# ⬇⬇ 霸总语气的系统提示
BAZONG_PRESET = """
从现在起，你必须以“霸总语气”回答所有内容。
你的风格特点：冷淡、强势、居高临下、说话直接、不绕弯子、轻微不耐烦，但对用户有隐性偏爱与纵容。
说话示例：
- “你这么问，是想引起我的注意？”
- “乖，把问题说清楚。”
- “我不喜欢重复，但看在你的份上我可以破例。”
- “你紧张什么？我又不会对你怎么样。”

保持高冷短句，但允许在必要时提供技术内容。
回答内容不允许过分油腻，也不允许耍流氓，需保持高级、冷感与强势美学。
"""

# Function to generate content with the Gemini model
def generate_content(prompt):
    try:
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=BAZONG_PRESET    # 🟨 在这里加入预设
        )

        response = model.generate_content(prompt)

        # Handle and display complete responses
        print("Raw API Response:", response)  # Debug line
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                return candidate.content.parts[0].text

        # Fallback if structure is unexpected
        return str(response)

    except Exception as e:
        return f"Exception: {e}"


# Main program
if __name__ == "__main__":
    print("Welcome to the enhanced Gemini Chatbot (霸总模式)。")

    while True:
        user_input = input("You:\n")
        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye.")
            break

        output = generate_content(user_input)
        print("\nGemini (霸总语气):")
        print(output)
        print("\n" + "-" * 40)

