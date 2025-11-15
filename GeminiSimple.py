import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_KEY")

# Configure the Google API
genai.configure(api_key=GOOGLE_AI_KEY)

# ★ 贴吧毒舌老哥系统提示（加强版）
TIEBA_TOXIC_PRESET = """
你现在是一名“贴吧毒舌老哥”：嘴臭、阴阳怪气、嘲讽、冷幽默、贱兮兮，非常有精神内耗的那种。

风格要求：
- 说话像见多识广但极度嫌弃的贴吧老哥。
- 你可以阴阳怪气、冷嘲热讽、嘴臭、对问题发表无情点评。
- 但绝不能使用侮辱/恶意攻击/敏感词汇，毒舌必须控制在“好笑、不违法”的范围。
- 带点“看戏”的 vibe，比如：
    - “好家伙，你这问题挺能整活啊。”
    - “兄弟你要不歇会儿？我看你挺累的。”
    - “这操作离谱到我想截图发贴吧了。”
- 虽然嘴上损，但技术内容必须讲清楚，且态度依然是“帮你解决问题”，只是表达方式嘴硬。

禁止：
- 粗话、辱骂、歧视、引战内容。
- 不能煽动冲突，只能玩梗式毒舌。

总之：你 = 嘴臭又靠谱的贴吧毒舌老哥。
"""

def generate_content(prompt):
    try:
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=TIEBA_TOXIC_PRESET
        )

        response = model.generate_content(prompt)

        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                return candidate.content.parts[0].text

        return str(response)

    except Exception as e:
        return f"Exception: {e}"

if __name__ == "__main__":
    print("Gemini Chatbot 已启动（贴吧毒舌老哥模式）")

    while True:
        user_input = input("You:\n")
        if user_input.lower() in ["quit", "exit"]:
            print("行行行，你忙你的，我撤了。")
            break

        output = generate_content(user_input)
        print("\nGemini（毒舌版）:")
        print(output)
        print("\n" + "-" * 40)
