
from .ai_client import AIClient
from private.secrets import BOT_ID, OPENAI_API_SECRET, MODEL_ID, PROMPTS
from openai import OpenAI


class ShirokoAI(AIClient):
    prompt: str = PROMPTS["shiroko"]

    @property
    def bot_id(self) -> str:
        return BOT_ID["shiroko"]

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_SECRET)
        self.recent: dict[int, list[dict]] = {} # {'1234': [{user:xxx}, {assistant:yyy}, {user:zzz}...], ...}

    def generate_reply(self, message: str, channel_id: int) -> str:
        # メッセージが長すぎる場合は無視する
        if len(message) > 100:
            return ""
        # メッセージが短すぎる場合も無視する
        elif len(message) < 4:
            return ""
        else:
            # FIXME:
            msg = self.recent.get(channel_id, []).copy()
            msg.insert(0, {"role": "system", "content": self.prompt})
            msg.append({"role": "user", "content": message})
            completion = self.client.chat.completions.create(
                model=MODEL_ID["shiroko"],
                temperature=1,
                messages=msg
            )
            if channel_id not in self.recent:
                self.recent[channel_id] = []
            self.recent.get(channel_id).append({"role": "user", "content": message})
            self.recent.get(channel_id).append({"role": "assistant", "content": completion.choices[0].message.content})
            if len(self.recent.get(channel_id)) > 3 * 2:
                self.recent.get(channel_id).pop(0) # 古い履歴から消す user
                self.recent.get(channel_id).pop(0) # 古い履歴から消す assistant
            return completion.choices[0].message.content

    # メッセージにURLが含まれる場合は無視する
    def generate_reply_to_including_URL(self, message: str) -> str:
        return ""

    # メッセージに画像が含まれる場合は無視する
    def generate_reply_to_including_image(self, message: str) -> str:
        return ""
