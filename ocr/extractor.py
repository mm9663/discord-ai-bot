import sys, re, glob, os
import pyocr
from PIL import Image
import cv2
from openai import OpenAI

# ほんまごめん、
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from private.secrets import BOT_ID, OPENAI_API_SECRET, MODEL_ID, PROMPTS



is_reply = re.compile(r'"@[0-9a-zA-Z_]+\s')

# js フォーマットから文字列のみ抜き出す
def cleanse(text: str) -> str:
    # ツイートのみを取り出す
    ret = text.replace('"full_text" : ', '')
    ret = re.search(r'"(.*)"', ret).group() + "\n"

    # リプライなら @ を先頭から削除していく
    while re.match(is_reply, ret):
        ret = re.sub(is_reply, '"', ret)

    # 改行と二重引用符を全角スペースと一重引用符に置換する
    ret = re.sub(r'\\n', '　', ret)
    ret = re.sub(r'\\"', "'", ret)

    # バックスラッシュは jsonl だとフォーマットエラーになるので消す
    ret = re.sub(r'\\', "＼", ret)

    # 先頭の空白を全て消す
    ret = re.sub(r'"[\s　]+', '"', ret)
    return ret[1:-1] + "\n"

class OCRTool():
    def __init__(self, tesseract_cmd, lang="jpn"):
        pyocr.tesseract.TESSERACT_CMD = tesseract_cmd
        tools = pyocr.get_available_tools()
        self.tool = tools[0]
        self.lang = lang

    def read(self, imgpath: str) -> str:
        # image = Image.open(imgpath)   #画像ファイルを読み込む

        img = cv2.imread(imgpath, cv2.IMREAD_GRAYSCALE) # グレイスケールで読み込むおまじない
        h = img.shape[0]
        w = img.shape[1]
        if h == 1640 and w == 2360: # iPadAir4生スクショのときはトリミングしてみる
            img = img[150:1570, 500:2119]
        elif w == 2360:
            img = img[:,500:2119]
        elif h == 828 and w == 1792:
            img = img[100:770,450:1480]
        #binaryThreshold = 190
        #ret, img = cv2.threshold(img, binaryThreshold, 255, cv2.THRESH_BINARY_INV)
        image = Image.fromarray(img) # PIL形式になおす

        text = self.tool.image_to_string(image, lang=self.lang, builder=pyocr.builders.TextBuilder(tesseract_layout=6))    #画像の文字を抽出
        return text

    def cleanse(self, ocr_result) -> str:
        ret = ocr_result
            # 改行と二重引用符を全角スペースと一重引用符に置換する
        ret = re.sub(r'\\n', '　', ret)
        ret = re.sub(r'\\"', "'", ret)

        ret = re.sub(r'\\n\\n', r'\\n', ret)
        ret = re.sub(r' ', r'', ret)
        return ret + "\n"



def has_urls(text: str) -> bool:
    return "http" in text


def is_retweet(text: str) -> bool:
    return "RT @" in text

# path で与えられたファイルを開き、ツイートを収拾する
# めちゃくちゃ適当に特定の年以降のものだけ抽出するように実装した
def extract_from_tweets_js(path: str, time: int) -> list[str]:
    results = []
    target: bool = False
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if "created_at" in line:
                inner_target = False
                for year in range(time, 2025):
                    if str(year) in line:
                        inner_target = True
                        break
                target = inner_target
            if target and "full_text" in line and not has_urls(line) and not is_retweet(line):
                tweet_text = cleanse(line)
                if '@' in line and (not '@' in tweet_text) and len(tweet_text) > 1:
                    results.append(tweet_text)
    return results

def extract_from_screenshots(input_path: str) -> list[str]:
    results = []
    files = []
    ocr = OCRTool(tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    files += glob.glob(os.path.join(input_path, r'.\**\*.png'))
    print(files)

    for file in files:
        ocr_result = ocr.read(file)
        result = ocr.cleanse(ocr_result)
        results.append(result)

    return results


def main():
    if len(sys.argv) <= 1:
        print("no argument. you must specify input folder path.")
        return

    input_path = sys.argv[1]
    results = extract_from_screenshots(input_path)
    with open("output_junk.txt", "w", encoding="utf-8") as f:
        f.writelines(results)
    '''
    prompt: str = PROMPTS['ocr']
    client = OpenAI(api_key=OPENAI_API_SECRET)
    compeletion = client.chat.completions.create(
        model=MODEL_ID['ocr'],
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": PROMPTS['ocr']}
        ]
    )
    trimmed = compeletion.choices[0].message.content
    with open("output_aiu.txt", "w", encoding="utf-8") as f:
        f.writelines(trimmed)
    '''

if __name__ == "__main__":
    main()
