import asyncio
import json
import random
import time
from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List, Optional, TypedDict, Union, cast

from anyio import open_file
from nonebot import logger
from nonebot.adapters.onebot.v11 import MessageSegment
from pil_utils import BuildImage, Text2Image

from ..config import config
from ..resource import (
    DATA_PATH,
    RES_CALENDER_BANNER,
    RES_GACHA_BG,
    RES_GACHA_BG_OLD,
    RES_GACHA_CARD_BG,
    RES_GACHA_CARD_MASK,
    RES_GACHA_NEW,
    RES_GACHA_PICKUP,
    RES_GACHA_STAR,
    RES_GACHA_STU_ERR,
)
from ..util import split_list
from .schaledb import schale_get, schale_get_stu_dict

GACHA_DATA_PATH = DATA_PATH / "gacha.json"
if not GACHA_DATA_PATH.exists():
    GACHA_DATA_PATH.write_text("{}")


DEFAULT_GACHA_DATA: "GachaData" = {"collected": []}
COOL_DOWN_DICT: Dict[str, float] = {}


class GachaData(TypedDict):
    collected: List[int]


@dataclass()
class GachaStudent:
    id: int  # noqa: A003
    name: str
    star: int
    new: bool
    pickup: bool
    count: int


@dataclass()
class RegularGachaInfo:
    student: GachaStudent
    counts: List[int]


def get_gacha_cool_down(
    user: Union[str, int],
    group: Optional[Union[str, int]] = None,
) -> int:
    key = f"{group}.{user}" if group else f"{user}"
    now = time.time()

    if last := COOL_DOWN_DICT.get(key):
        remain = config.ba_gacha_cool_down - round(now - last)
        return remain if remain >= 0 else 0

    return 0


def set_gacha_cool_down(user: Union[str, int], group: Optional[Union[str, int]] = None):
    key = f"{group}.{user}" if group else f"{user}"
    COOL_DOWN_DICT[key] = time.time()


async def set_gacha_data(qq: str, data: GachaData):
    async with await open_file(GACHA_DATA_PATH, "r+", encoding="u8") as f:
        j = json.loads(await f.read())
        j[qq] = data

        await f.seek(0)
        await f.truncate()

        await f.write(json.dumps(j))


async def get_gacha_data(qq: str) -> GachaData:
    async with await open_file(GACHA_DATA_PATH, encoding="u8") as f:
        j = await f.read()

    data: Dict[str, GachaData] = json.loads(j)
    if not (user_data := data.get(qq)):
        user_data = DEFAULT_GACHA_DATA.copy()
        await set_gacha_data(qq, user_data)

    return user_data


def format_count(count: int) -> str:
    trans_dict = {1: "st", 2: "nd", 3: "rd"}
    default_suffix = "th"

    if count % 100 in (10 + x for x in trans_dict):
        return f"{count}{default_suffix}"

    return f"{count}{trans_dict.get(count % 10, default_suffix)}"


async def get_student_icon(student_id: int) -> BuildImage:
    try:
        stu_img = await schale_get(
            f"images/student/icon/{student_id}.webp",
            raw=True,
        )
        stu_img = BuildImage.open(BytesIO(stu_img))
    except Exception:
        logger.exception(f"学生数据获取失败 {student_id}")
        stu_img = RES_GACHA_STU_ERR

    return stu_img.resize((64, 64), keep_ratio=True).circle()


async def get_student_card(
    student: GachaStudent,
    draw_count: bool = True,
) -> BuildImage:
    bg = RES_GACHA_CARD_BG.copy()

    try:
        stu_img = await schale_get(
            f"images/student/collection/{student.id}.webp",
            raw=True,
        )
        stu_img = BuildImage.open(BytesIO(stu_img))
    except Exception:
        logger.exception(f"学生数据获取失败 {student.id}")
        stu_img = RES_GACHA_STU_ERR

    card_img = BuildImage.new("RGBA", RES_GACHA_CARD_MASK.size, (0, 0, 0, 0))
    card_img.image.paste(
        stu_img.resize(RES_GACHA_CARD_MASK.size, keep_ratio=True).image,
        mask=RES_GACHA_CARD_MASK.image,
    )

    bg = bg.paste(card_img, (26, 13), alpha=True)

    star_x_offset = int(26 + (159 - 30 * student.star) / 2)
    star_y_offset = 198
    for i in range(student.star):
        bg = bg.paste(
            RES_GACHA_STAR,
            (star_x_offset + i * 30, star_y_offset),
            alpha=True,
        )

    font_x_offset = 45
    font_y_offset = 2

    if student.new:
        bg = bg.paste(RES_GACHA_NEW, (font_x_offset, font_y_offset), alpha=True)
        font_x_offset -= 2
        font_y_offset += 29

    if student.pickup:
        font_x_offset -= 4
        font_y_offset -= 4
        bg = bg.paste(RES_GACHA_PICKUP, (font_x_offset, font_y_offset), alpha=True)

    if draw_count:
        bg.draw_text(
            (29, 195),
            format_count(student.count),
            fontsize=16,
            style="italic",
            fill="white",
        )

    return bg


def collect_regular_info(
    regular_students: List[GachaStudent],
) -> List[RegularGachaInfo]:
    students: Dict[int, List[GachaStudent]] = {}
    for stu in regular_students:
        if stu.id not in students:
            students[stu.id] = []
        students[stu.id].append(stu)

    return [
        RegularGachaInfo(student=stu[0], counts=[x.count for x in stu])
        for stu in students.values()
    ]


async def draw_summary_gacha_img(result: List[GachaStudent]) -> BuildImage:
    important_result: List[GachaStudent] = []
    regular_result: List[GachaStudent] = []
    for res in result:
        if res.star >= 3:
            important_result.append(res)
        else:
            regular_result.append(res)

    regular_collected = collect_regular_info(regular_result)

    regular_collected.sort(key=lambda x: len(x.counts), reverse=True)
    regular_collected.sort(key=lambda x: x.student.new, reverse=True)
    regular_collected.sort(key=lambda x: x.student.star, reverse=True)
    regular_collected.sort(key=lambda x: x.student.pickup, reverse=True)

    important_pics: List[List[BuildImage]] = split_list(
        await asyncio.gather(*[get_student_card(x) for x in important_result]),
        5,
    )
    regular_icons: List[BuildImage] = await asyncio.gather(
        *[get_student_icon(x.student.id) for x in regular_collected],
    )

    padding = 50
    part_width = 256 * 5 + padding * 2
    img_width = part_width + padding * 2

    def gen_important() -> BuildImage:
        img_size = 256
        title_txt = Text2Image.from_text(
            f"3★学生（共计{len(important_result)}次）",
            80,
            weight="bold",
            fill="black",
        )
        title_height = title_txt.height

        if not important_pics:
            empty_txt = Text2Image.from_text(
                "诶~老师怎么一个3★学生都没招募到？真是杂鱼呢~",
                40,
                fill="black",
            )
            bg = BuildImage.new(
                "RGBA",
                (
                    part_width,
                    title_height + padding + empty_txt.height + padding * 2,
                ),
                (255, 255, 255, 70),
            )
            title_txt.draw_on_image(bg.image, (padding, padding))
            empty_txt.draw_on_image(bg.image, (padding, padding * 2 + title_height))
            return bg

        # else:
        bg = BuildImage.new(
            "RGBA",
            (
                part_width,
                (img_size * len(important_pics)) + title_height + padding * 3,
            ),
            (255, 255, 255, 70),
        )
        title_txt.draw_on_image(bg.image, (padding, padding))
        for i, row in enumerate(important_pics):
            for j, pic in enumerate(row):
                bg = bg.paste(
                    pic,
                    (
                        padding + j * pic.width,
                        padding * 2 + title_height + i * img_size,
                    ),
                )
        return bg

    def gen_regular() -> BuildImage:
        gap_size = 10
        img_size = 64

        title_txt = Text2Image.from_text(
            f"3★以下学生（共计{len(regular_result)}次）",
            80,
            weight="bold",
            fill="black",
        )
        title_height = title_txt.height

        bg = BuildImage.new(
            "RGBA",
            (
                part_width,
                (
                    ((img_size + gap_size) * len(regular_collected) - gap_size)
                    + title_height
                    + padding * 3
                ),
            ),
            (255, 255, 255, 70),
        )
        title_txt.draw_on_image(bg.image, (padding, padding))

        for i, icon in enumerate(regular_icons):
            bg = bg.paste(
                icon,
                (padding, padding * 2 + title_height + i * (img_size + gap_size)),
            )
        for i, info in enumerate(regular_collected):
            student = info.student
            info_tip = f"{student.name} ({student.star}★) x{len(info.counts)}"
            if student.pickup:
                info_tip = f"[UP!]{info_tip}"
            if student.new:
                info_tip = f"[New]{info_tip}"
            info_txt = Text2Image.from_text(info_tip, 40, fill="black")
            info_txt.draw_on_image(
                bg.image,
                (
                    padding + img_size + gap_size,
                    (
                        padding * 2
                        + title_height
                        + i * (img_size + gap_size)
                        + (img_size - info_txt.height)
                    ),
                ),
            )

        return bg

    important_img = gen_important()
    regular_img = gen_regular()

    banner_h = 150
    return (
        RES_GACHA_BG.copy()
        .resize(
            (
                img_width,
                banner_h + important_img.height + regular_img.height + padding * 3,
            ),
            keep_ratio=True,
        )
        .paste(RES_CALENDER_BANNER.copy().resize((img_width, banner_h)))
        .draw_text(
            (50, 0, 1480, 150),
            "招募总结",
            max_fontsize=100,
            weight="bold",
            fill="#ffffff",
            halign="left",
        )
        .paste(important_img, (padding, banner_h + padding))
        .paste(
            regular_img,
            (padding, banner_h + padding + important_img.height + padding),
        )
    )


async def draw_classic_gacha_img(students: List[GachaStudent]) -> BuildImage:
    line_limit = 5
    card_w, card_h = (256, 256)

    stu_cards: List[List[BuildImage]] = split_list(
        await asyncio.gather(
            *(get_student_card(student, draw_count=False) for student in students),
        ),
        line_limit,
    )
    bg = RES_GACHA_BG_OLD.copy()

    x_gap = 10
    y_gap = 80
    y_offset = int((bg.height - (len(stu_cards) * (y_gap + card_h) - y_gap)) / 2)
    for line in stu_cards:
        x_offset = int((bg.width - (len(line) * (x_gap + card_w) - x_gap)) / 2)
        for card in line:
            bg = bg.paste(card, (x_offset, y_offset), alpha=True)
            x_offset += card_w + x_gap
        y_offset += card_h + y_gap

    return bg.draw_text(
        (1678, 841, 1888, 885),
        "BAWiki",
        max_fontsize=30,
        weight="bold",
        fill=(36, 90, 126),
    ).draw_text(
        (1643, 885, 1890, 935),
        "经典抽卡样式",
        max_fontsize=30,
        weight="bold",
        fill=(255, 255, 255),
    )


async def do_gacha(
    qq: str,
    times: int,
    gacha_data_json: dict,
    up_pool: Optional[List[int]] = None,
):
    # 屎山代码 别骂了别骂了
    # 如果有大佬指点指点怎么优化或者愿意发个PR就真的太感激了

    if not up_pool:
        up_pool = []

    stu_li = await schale_get_stu_dict("Id")
    up_3_li, up_2_li = [
        [x for x in up_pool if x in stu_li and stu_li[x]["StarGrade"] == y]
        for y in [3, 2]
    ]

    base_char: dict = gacha_data_json["base"]
    for up in up_pool:
        for li in cast(List[List[int]], base_char.values()):
            if up in li:
                li.remove(up)

    star_3_base, star_2_base, star_1_base = [base_char[x] for x in ["3", "2", "1"]]
    star_3_chance, star_2_chance, star_1_chance = [
        x["chance"] for x in [star_3_base, star_2_base, star_1_base]
    ]

    up_3_chance = 0
    up_2_chance = 0
    if up_3_li:
        up_3_chance = gacha_data_json["up"]["3"]["chance"]
        star_3_chance -= up_3_chance
    if up_2_li:
        up_2_chance = gacha_data_json["up"]["2"]["chance"]
        star_2_chance -= up_2_chance

    gacha_data = await get_gacha_data(qq)
    gacha_result: List[GachaStudent] = []

    for i in range(1, times + 1):
        pool_and_weight = [
            (up_3_li, up_3_chance),
            (up_2_li, up_2_chance),
            (star_3_base["char"], star_3_chance),
            (star_2_base["char"], star_2_chance),
        ]
        if i % 10 != 0:
            pool_and_weight.append((star_1_base["char"], star_1_chance))

        pool_and_weight = [x for x in pool_and_weight if x[0]]
        pool = [x[0] for x in pool_and_weight]
        weight = [x[1] for x in pool_and_weight]

        await asyncio.sleep(0.05)
        random.seed()
        char = random.choice(random.choices(pool, weights=weight, k=1)[0])

        is_3star_pickup = char in up_3_li
        is_pickup = is_3star_pickup or (char in up_2_li)
        is_new = char not in gacha_data["collected"]
        char_info = stu_li[char]
        gacha_result.append(
            GachaStudent(
                id=char,
                name=char_info["Name"],
                star=char_info["StarGrade"],
                pickup=is_pickup,
                new=is_new,
                count=i,
            ),
        )

        if is_new:
            gacha_data["collected"].append(char)

    await set_gacha_data(qq, gacha_data)
    return gacha_result


async def gacha(
    qq: str,
    times: int,
    gacha_data_json: dict,
    up_pool: Optional[List[int]] = None,
) -> MessageSegment:
    result = await do_gacha(qq, times, gacha_data_json, up_pool)
    img = (
        (await draw_summary_gacha_img(result))
        if (times > 10) or (config.ba_disable_classic_gacha)
        else (await draw_classic_gacha_img(result))
    )
    img_bytes = img.convert("RGB").save_jpg()
    return MessageSegment.image(img_bytes)
