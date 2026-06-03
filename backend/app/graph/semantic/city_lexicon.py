"""国内热门旅行目的地词表（精确名、别名、常见错字、拼音）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CityEntry:
    name: str
    pinyin: str
    aliases: tuple[str, ...] = ()
    typos_confirm: tuple[str, ...] = ()  # 同音/近音错字，需用户确认
    typos_auto: tuple[str, ...] = ()  # 形近错字，高置信自动纠正


# TOP 国内热门目的地 + 常见输入变体
CITY_ENTRIES: tuple[CityEntry, ...] = (
    CityEntry("成都", "chengdu", ("蓉城",), ("程度", "成度", "城都"), ("成督",)),
    CityEntry("杭州", "hangzhou", ("西湖",), (), ("杭洲",)),
    CityEntry("三亚", "sanya", (), ("三亚",), ()),
    CityEntry("北京", "beijing", ("帝都",), ("北景",), ("北就",)),
    CityEntry("上海", "shanghai", ("魔都",), (), ("上诲", "上尚")),
    CityEntry("广州", "guangzhou", ("羊城",), ("广洲",), ("广付",)),
    CityEntry("深圳", "shenzhen", (), ("深川",), ("深正",)),
    CityEntry("重庆", "chongqing", ("山城",), ("重亲", "崇庆"), ("重庆",)),
    CityEntry("西安", "xian", ("长安",), ("西按",), ("西安",)),
    CityEntry("南京", "nanjing", (), ("南精",), ("南就",)),
    CityEntry("武汉", "wuhan", (), ("武汗",), ("武汉",)),
    CityEntry("苏州", "suzhou", (), ("苏洲",), ("苏洲",)),
    CityEntry("厦门", "xiamen", (), ("下门",), ("夏门", "厦们")),
    CityEntry("青岛", "qingdao", (), ("青导",), ("清岛",)),
    CityEntry("大连", "dalian", (), ("大联",), ("大练",)),
    CityEntry("长沙", "changsha", (), ("长杀",), ("常沙",)),
    CityEntry("昆明", "kunming", ("春城",), ("昆名",), ("昆民",)),
    CityEntry("丽江", "lijiang", (), ("力江",), ("丽将",)),
    CityEntry("桂林", "guilin", (), ("桂凌",), ("贵林",)),
    CityEntry("哈尔滨", "haerbin", ("冰城",), ("哈而滨",), ("哈儿滨",)),
    CityEntry("沈阳", "shenyang", (), ("沈洋",), ("审阳",)),
    CityEntry("天津", "tianjin", (), ("天经",), ("天斤",)),
    CityEntry("郑州", "zhengzhou", (), ("郑洲",), ("正州",)),
    CityEntry("福州", "fuzhou", (), ("福洲",), ("付州",)),
    CityEntry("济南", "jinan", (), ("济难",), ("集南",)),
    CityEntry("合肥", "hefei", (), ("合费",), ("河肥",)),
    CityEntry("南昌", "nanchang", (), ("南长",), ("男昌",)),
    CityEntry("贵阳", "guiyang", (), ("桂阳",), ("贵洋",)),
    CityEntry("兰州", "lanzhou", (), ("兰洲",), ("南州",)),
    CityEntry("乌鲁木齐", "wulumuqi", (), ("乌鲁木齐",), ()),
    CityEntry("拉萨", "lasa", (), ("拉撒",), ("啦萨",)),
    CityEntry("香港", "xianggang", (), (), ()),
    CityEntry("澳门", "aomen", ("澳门",), (), ()),
    CityEntry("台北", "taibei", (), ("台被",), ()),
    CityEntry("西双版纳", "xishuangbanna", ("版纳",), ("西双版那",), ("西双版纳",)),
    CityEntry("九寨沟", "jiuzhaigou", ("九寨",), ("九塞沟",), ("九寨沟",)),
    CityEntry("张家界", "zhangjiajie", (), ("张加界",), ("张家界",)),
    CityEntry("黄山", "huangshan", (), ("黄衫",), ("黄山",)),
    CityEntry("威海", "weihai", (), ("威还",), ()),
    CityEntry("烟台", "yantai", (), ("烟台北",), ()),
    CityEntry("珠海", "zhuhai", (), ("珠还",), ()),
    CityEntry("无锡", "wuxi", (), ("无西",), ()),
    CityEntry("宁波", "ningbo", (), ("宁被",), ()),
    CityEntry("温州", "wenzhou", (), ("温洲",), ("温州",)),
    CityEntry("泉州", "quanzhou", (), ("泉洲",), ("泉州",)),
    CityEntry("洛阳", "luoyang", (), ("落阳",), ()),
    CityEntry("大理", "dali", (), ("大里",), ()),
    CityEntry("香格里拉", "xianggelila", (), ("香各里拉",), ()),
    CityEntry("稻城", "daocheng", ("稻城亚丁",), ("稻成",), ()),
    CityEntry("婺源", "wuyuan", (), ("雾源",), ()),
    CityEntry("乌镇", "wuzhen", (), ("乌真",), ()),
    CityEntry("凤凰", "fenghuang", ("凤凰古城",), ("风凰",), ()),
    # --- 扩展：西北 / 西南 ---
    CityEntry("西宁", "xining", (), ("西泞",), ()),
    CityEntry("敦煌", "dunhuang", (), ("燉煌",), ()),
    CityEntry("嘉峪关", "jiayuguan", (), (), ()),
    CityEntry("银川", "yinchuan", (), ("银川",), ()),
    CityEntry("呼和浩特", "hohhot", ("呼市",), ("呼伦浩特",), ()),
    CityEntry("包头", "baotou", (), (), ()),
    CityEntry("喀什", "kashi", (), ("咯什",), ()),
    CityEntry("伊犁", "yili", ("伊宁",), ("伊梨",), ()),
    CityEntry("林芝", "linzhi", (), ("临芝",), ()),
    CityEntry("日喀则", "rikaze", (), ("日客则",), ()),
    CityEntry("克拉玛依", "kelamayi", (), (), ()),
    CityEntry("库尔勒", "kuerle", (), ("库勒",), ()),
    CityEntry("腾冲", "tengchong", (), (), ()),
    CityEntry("乐山", "leshan", ("峨眉山",), ("乐山大佛",), ()),
    CityEntry("绵阳", "mianyang", (), (), ()),
    CityEntry("宜宾", "yibin", (), (), ()),
    CityEntry("遵义", "zunyi", (), (), ()),
    CityEntry("六盘水", "liupanshui", (), (), ()),
    # --- 扩展：华东 / 华南 ---
    CityEntry("秦皇岛", "qinhuangdao", ("北戴河",), (), ()),
    CityEntry("承德", "chengde", ("避暑山庄",), (), ()),
    CityEntry("石家庄", "shijiazhuang", (), ("石家莊",), ()),
    CityEntry("太原", "taiyuan", (), ("太源",), ()),
    CityEntry("扬州", "yangzhou", (), ("杨州",), ()),
    CityEntry("常州", "changzhou", (), ("长州",), ()),
    CityEntry("南通", "nantong", (), (), ()),
    CityEntry("绍兴", "shaoxing", (), ("绍行",), ()),
    CityEntry("嘉兴", "jiaxing", (), (), ()),
    CityEntry("湖州", "huzhou", (), ("湖洲",), ()),
    CityEntry("台州", "taizhou", (), ("台洲",), ()),
    CityEntry("徐州", "xuzhou", (), ("徐洲",), ()),
    CityEntry("连云港", "lianyungang", (), (), ()),
    CityEntry("上饶", "shangrao", ("三清山",), (), ()),
    CityEntry("景德镇", "jingdezhen", ("瓷都",), (), ()),
    CityEntry("海口", "haikou", (), (), ()),
    CityEntry("南宁", "nanning", (), ("南泞",), ()),
    CityEntry("柳州", "liuzhou", (), (), ()),
    CityEntry("北海", "beihai", (), (), ()),
    CityEntry("湛江", "zhanjiang", (), (), ()),
    CityEntry("汕头", "shantou", (), (), ()),
    CityEntry("东莞", "dongguan", (), (), ()),
    CityEntry("佛山", "foshan", (), ("佛三",), ()),
    CityEntry("中山", "zhongshan", (), (), ()),
    CityEntry("惠州", "huizhou", (), ("惠洲",), ()),
    CityEntry("牡丹江", "mudanjiang", (), (), ()),
    CityEntry("延吉", "yanji", (), (), ()),
    CityEntry("漠河", "mohe", (), (), ()),
    # --- 扩展：景点映射依赖的行政目的地 ---
    CityEntry("阿勒泰", "aletai", (), (), ()),
    CityEntry("吐鲁番", "turpan", (), ("吐鲁翻",), ()),
    CityEntry("张掖", "zhangye", (), (), ()),
    CityEntry("天水", "tianshui", (), (), ()),
    CityEntry("中卫", "zhongwei", (), (), ()),
    CityEntry("呼伦贝尔", "hulunbeier", ("呼盟",), (), ()),
    CityEntry("开封", "kaifeng", (), (), ()),
    CityEntry("焦作", "jiaozuo", (), (), ()),
    CityEntry("镇江", "zhenjiang", (), ("镇江",), ()),
    CityEntry("九江", "jiujiang", (), (), ()),
    CityEntry("恩施", "enshi", (), (), ()),
    CityEntry("宜昌", "yichang", (), ("宜昌",), ()),
    CityEntry("十堰", "shiyan", (), (), ()),
    CityEntry("长春", "changchun", (), ("长舂",), ()),
    CityEntry("格尔木", "geermu", (), (), ()),
    CityEntry("湘西", "xiangxi", (), (), ()),
    CityEntry("鹰潭", "yingtan", (), (), ()),
    CityEntry("萍乡", "pingxiang", (), (), ()),
    CityEntry("南平", "nanping", (), (), ()),
    CityEntry("漳州", "zhangzhou", (), ("漳洲",), ()),
    CityEntry("龙岩", "longyan", (), (), ()),
    CityEntry("郴州", "chenzhou", (), ("郴洲",), ()),
    CityEntry("铜仁", "tongren", (), (), ()),
    CityEntry("安顺", "anshun", (), (), ()),
    CityEntry("黔南", "qiannan", (), (), ()),
    CityEntry("黔东南", "qiandongnan", (), (), ()),
    CityEntry("甘南", "gannan", (), (), ()),
    CityEntry("甘孜", "ganzi", (), (), ()),
    CityEntry("阿坝", "aba", (), (), ()),
    CityEntry("兴安盟", "xinganmeng", (), (), ()),
    CityEntry("阿拉善", "alashan", (), (), ()),
    CityEntry("枣庄", "zaozhuang", (), (), ()),
    CityEntry("泰安", "taian", (), ("太安",), ()),
    CityEntry("济宁", "jining", (), ("济寧",), ()),
    CityEntry("延边", "yanbian", (), (), ()),
)

_NAME_INDEX: dict[str, CityEntry] = {}
_ALIAS_INDEX: dict[str, CityEntry] = {}
_TYPO_CONFIRM_INDEX: dict[str, CityEntry] = {}
_TYPO_AUTO_INDEX: dict[str, CityEntry] = {}
_PINYIN_INDEX: dict[str, CityEntry] = {}
_PINYIN_ABBREV_INDEX: dict[str, CityEntry] = {}


def _build_indexes() -> None:
    if _NAME_INDEX:
        return
    for entry in CITY_ENTRIES:
        _NAME_INDEX[entry.name] = entry
        _PINYIN_INDEX[entry.pinyin.lower()] = entry
        for alias in entry.aliases:
            _ALIAS_INDEX[alias] = entry
        for typo in entry.typos_confirm:
            _TYPO_CONFIRM_INDEX[typo] = entry
        for typo in entry.typos_auto:
            _TYPO_AUTO_INDEX[typo] = entry
    for abbr, name in (("bj", "北京"), ("cd", "成都"), ("sh", "上海"), ("gz", "广州"), ("sz", "深圳")):
        entry = _NAME_INDEX.get(name)
        if entry:
            _PINYIN_ABBREV_INDEX[abbr] = entry


def lookup_city(text: str) -> CityEntry | None:
    """精确匹配城市名或别名。"""
    _build_indexes()
    key = text.strip()
    if not key:
        return None
    if key in _NAME_INDEX:
        return _NAME_INDEX[key]
    return _ALIAS_INDEX.get(key)


def lookup_city_by_pinyin(text: str) -> CityEntry | None:
    """匹配完整拼音或常见简写（bj/cd/sh）。"""
    _build_indexes()
    key = text.strip().lower()
    if not key:
        return None
    if key in _PINYIN_ABBREV_INDEX:
        return _PINYIN_ABBREV_INDEX[key]
    return _PINYIN_INDEX.get(key)


def all_city_names() -> list[str]:
    _build_indexes()
    names = list(_NAME_INDEX.keys())
    names.extend(_ALIAS_INDEX.keys())
    return names


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


@dataclass(frozen=True, slots=True)
class CityMatch:
    city: str
    confidence: float
    source: str
    needs_confirm: bool


def match_cities(text: str, *, limit: int = 3) -> list[CityMatch]:
    """对输入做城市匹配，按置信度降序。"""
    _build_indexes()
    raw = text.strip()
    if not raw or len(raw) > 8:
        return []

    exact = lookup_city(raw)
    if exact:
        return [CityMatch(exact.name, 1.0, "exact", False)]

    if raw in _TYPO_AUTO_INDEX:
        entry = _TYPO_AUTO_INDEX[raw]
        return [CityMatch(entry.name, 0.92, "typo_auto", False)]

    if raw in _TYPO_CONFIRM_INDEX:
        entry = _TYPO_CONFIRM_INDEX[raw]
        return [CityMatch(entry.name, 0.88, "typo_confirm", True)]

    results: list[CityMatch] = []
    for entry in CITY_ENTRIES:
        dist = _levenshtein(raw, entry.name)
        max_len = max(len(raw), len(entry.name))
        if max_len == 0:
            continue
        similarity = 1.0 - dist / max_len
        if dist == 1 and len(raw) == len(entry.name):
            # 同长度单字差（如 西藏/西安）必须用户确认，禁止自动采纳
            results.append(CityMatch(entry.name, 0.86, "fuzzy", True))
        elif dist == 1 and similarity >= 0.66:
            results.append(CityMatch(entry.name, 0.72, "fuzzy", True))

    results.sort(key=lambda m: (-m.confidence, m.city))
    deduped: list[CityMatch] = []
    seen: set[str] = set()
    for item in results:
        if item.city in seen:
            continue
        seen.add(item.city)
        deduped.append(item)
    return deduped[:limit]
