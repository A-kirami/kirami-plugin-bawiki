from pathlib import Path
from typing import Dict, List

STU_ALIAS = {
    # 真诚感谢所有帮忙贡献学生别名的朋友！！
    "星野": ["ホシノ", "小鸟游星野", "大叔", "粉毛"],
    "星野（泳装）": ["ホシノ（水着）", "泳装星野", "星野泳装", "泳装大叔", "大叔泳装", "水大叔"],
    "阿露": ["アル", "愉悦姐", "社长", "阿鲁", "亚瑠"],
    "日奈": ["ヒナ", "魔王", "老婆", "阳奈"],
    "日奈（泳装）": ["ヒナ（水着）", "泳装日奈", "日奈泳装", "泳装阳奈", "阳奈泳装", "水日奈", "水魔王", "水老婆"],
    "泉": ["イズミ", "老八", "汉堡", "汉堡妹"],
    "泉（泳装）": ["イズミ（水着）", "泳装泉", "泉泳装", "水老八", "水汉堡", "西瓜"],
    "伊织": ["イオリ", "佐仓"],
    "伊织（泳装）": ["イオリ（水着）", "泳装伊织", "伊织泳装", "水佐仓"],
    "晴奈": ["ハルナ", "美食会长", "神秘狙", "羽留奈"],
    "明里": ["アカリ", "牛牛", "吃货", "亚伽里"],
    "睦月": ["ムツキ", "无月", "地雷", "地雷妹"],
    "佳代子": ["カヨコ", "恐惧姐", "佳世子"],
    "枫香": ["フウカ", "料理妹", "风华", "煮饭婆"],
    "淳子": ["ジュンコ", "丸子", "琴里"],
    "春香": ["ハルカ", "遥香"],
    "朱莉": ["ジュリ", "料理姐"],
    "千夏": ["チナツ", "闪避奶"],
    "响": ["ヒビキ", "鲁班", "迫击炮", "響"],
    "艾米": ["エイミ", "拉链", "英美"],
    "菫": ["スミレ", "运动部长", "体委"],
    "花凛": ["カリン", "花梨", "黑皮", "黑皮女仆"],
    "花凛（兔女郎）": ["カリン（バニーガール）", "兔花凛"],
    "尼禄": ["ネル", "妮露", "暴躁姐", "宁瑠"],
    "尼禄（兔女郎）": ["ネル（バニーガール）", "兔尼禄", "兔妮露"],
    "真希": ["マキ", "破甲妹", "彩弹妹", "maki", "真纪"],
    "爱丽丝": ["アリス"],
    "晴": ["ハレ", "emp"],
    "优香": ["ユウカ", "祖冲之", "佑香", "没包人", "半包人"],
    "茜": ["アカネ", "破甲女仆", "朱音"],
    "歌原": ["ウタハ", "炮塔妹", "炮台妹", "咏叶"],
    "小玉": ["コタマ"],
    "柯托莉": ["コトリ", "叠甲妹", "护甲妹", "亚都梨"],
    "明日奈": ["アスナ", "亚丝娜"],
    "明日奈（兔女郎）": ["アスナ（バニーガール）", "兔丝娜"],
    "柚子": ["ユズ"],
    "纱绫": ["サヤ", "鼠妹", "沙耶"],
    "纱绫（私服）": ["サヤ（私服）", "私服老鼠"],
    "瞬": ["シュン", "旬", "教官", "梅花狙", "山海狙"],
    "瞬（幼女）": ["シュン（幼女）", "铜花瞬"],
    "白子": ["シロコ", "xcw", "小仓唯"],
    "白子（骑行）": ["单车唯", "小车唯"],
    "野宫": ["ノノミ", "富婆", "野乃美", "加特林"],
    "芹香": ["セリカ", "茜香", "黑猫"],
    "绫音": ["アヤネ", "书计奶"],
    "真白": ["マシロ", "天台狙", "麻白"],
    "真白（泳装）": ["水真白"],
    "日富美": ["ヒフミ", "日步美", "黄鸡", "肥鸡"],
    "日富美（泳装）": ["水坦克", "水肥鸡"],
    "鹤城": ["ツルギ", "颜艺", "颜艺姐", "弦生"],
    "鹤城（泳装）": ["水鹤城", "水颜艺"],
    "花江": ["ハナエ", "兔子奶", "花绘"],
    "爱莉": ["アイリ", "冰激凌"],
    "莲见": ["ハスミ", "委员长", "莲实"],
    "铃美": ["スズミ", "闪光弹", "闪光妹"],
    "志美子": ["シミコ", "图书妹"],
    "好美": ["ヨシミ", "毛二力", "傲娇", "喜美"],
    "芹娜": ["セリナ", "护士奶", "妈", "芹奈"],
    "泉奈": ["イズナ", "狐狸", "忍忍", "伊树菜"],
    "椿": ["ツバキ", "神秘T", "狗盾"],
    "千世": ["チセ", "雷姆", "知世"],
    "静子": ["シズコ", "餐车"],
    "菲娜": ["フィーナ", "歌舞伎"],
    "切里诺": ["チェリノ", "斯大萝", "斯大林", "洁莉诺"],
    "和香": ["ノドカ", "望远镜", "偷窥狂"],
    "亚津子": ["アツコ", "敦子", "公主", "秤砣子"],
    "巴": ["トモエ", "智惠"],
    "初音未来（联动）": ["ミク", "初音", "初音未来", "miku"],
    "切里诺（温泉）": ["泉大萝"],
    "和香（温泉）": ["老板娘"],
    "忧": ["ウイ"],
    "枫": [],
    "美咲": ["ミサキ"],
    "日和": [],
    "野宫（泳装）": ["水富婆"],
    "纱织": ["サオリ"],
    "桐乃": ["キリノ", "烟雾弹"],
    "绿": ["小绿"],
    "阿露（正月）": ["春社长", "春阿露"],
    "芹香（正月）": ["春黑", "春黑猫"],
    "千寻": ["円香", "円"],
    "玛利娜": ["保洁", "保洁阿姨"],
    "咲": ["导管兔", "拤"],
    "宫子": [],
    "美游": ["垃圾兔", "垃姬兔"],
    "若藻（泳装）": ["水fes", "水若藻"],
    "桃井": ["小桃"],
    "花子": ["ハナコ"],
    "吹雪": ["フブキ"],
    "绫音（泳装）": ["水书记", "直升机"],
    "梓（泳装）": ["水梓"],
    "夏": ["小夏"],
    "亚子": [],
    "千夏（温泉）": [],
    "睦月（正月）": ["春月"],
    "若藻": ["ワカモ", "fes"],
    "濑名": [],
    "三森": [],
    "日向": [],
    "伊吕波": ["天启坦克", "168"],
    "月咏": [],
    "泉奈（泳装）": ["水狐狸", "水泉奈"],
    "千世（泳装）": ["水千世", "水蕾姆"],
    "玛丽": ["修女"],
    "满（泳装）": [],
    "静子（泳装）": [],
    "梓": ["アズサ"],
    "小春": ["虾线"],
}

SCHALE_DB_DIFFERENT = {
    "真纪": "真希",
    "堇": "菫",
    "亚伽里": "明里",
    "遥香": "春香",
    "花绘": "花江",
    "茱莉": "朱莉",
    "白子（单车）": "白子（骑行）",
    "初音未来": "初音未来（联动）",
    "智惠": "巴",
}

EXTRA_L2D_LI: Dict[str, List[str]] = {}

ORIGIN_SCHALE_URL = "https://lonqie.github.io/SchaleDB/"
SCHALE_URL = "http://schale.lgc2333.top/"

SUFFIX_ALIAS = {"泳装": ["水"], "兔女郎": ["兔"], "正月": ["春"], "骑行": ["单车"], "幼女": ["幼", "铜"]}

RES_PATH = Path(__file__).parent / "res"
# RES_FONT = RES_PATH / "SourceHanSansSC-Bold-2.otf"
RES_CALENDER_BANNER = RES_PATH / "calender_banner.png"
RES_SCHALE_BG = RES_PATH / "schale_bg.jpg"
