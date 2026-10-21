# -*- coding: utf-8 -*-
"""math-doc 的共享常量与外部工具定位。

设计为**叶子模块**：不 import 技能内任何其他模块，也不 import 第三方库。
这样 validator 能与生成侧断言同一套常量，而不必被迫拉起 latex2mathml。

两类消费者的角色相反：

* 生成侧（``latex_to_omml`` / ``mathdoc_cli`` / ``omml_helpers``）—— 产出
* 校验侧（``validator``）—— 断言

规则值集中在这里，改一处不会在两侧漂移；此前 limLoc 规则与字体名在生成侧
和校验侧各写了一份字面量，正是漂移的来源。
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

# --------------------------------------------------------------------- OMML 结构

#: 大算符上下限的排布。∑/∏ 上下叠排（``undOvr``），∫ 走右侧角标（``subSup``）。
#: 生成侧据此设置 ``limLoc``，校验侧据此断言，两侧同源。
NARY_LIM_LOC = {
    '∑': 'undOvr',
    '∏': 'undOvr',
    '∫': 'subSup',
}


def expected_lim_loc(op):
    """返回该大算符应有的 ``limLoc`` 值；未收录的算符返回 ``None``（两侧都跳过）。"""
    return NARY_LIM_LOC.get(op)


# --------------------------------------------------------------------- 字体约定

#: 以下字体为**无 baseline 且用户未要求格式**时的默认值；用户明确要求时以用户要求为准，基于已有文档时以 baseline 为准。
FONT_BODY_CN = '宋体'
FONT_HEADING_CN = '黑体'
FONT_TITLE_CN = '方正小标宋简体'
FONT_LATIN = 'Times New Roman'

#: 表头单元格底纹。validator 断言它，生成侧用它。
TABLE_HEADER_FILL = 'E8EEF5'

#: OOXML 主题字体属性：`w:rFonts` 上只要存在任一 Theme 属性，Word 就按主题字体渲染，
#: 显式 ascii/hAnsi/eastAsia 会被忽略。生成侧设置字体前必须删除，校验侧断言不存在。
THEME_FONT_ATTRS = ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme')

#: 无 baseline 文档时的页面回退预设（英寸）。有 baseline 时以 baseline 为准。
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0
MARGIN_LEFT_IN = 1.0
MARGIN_RIGHT_IN = 1.0
MARGIN_TOP_IN = 0.8
MARGIN_BOTTOM_IN = 0.8

# --------------------------------------------------------------------- 版式字号

#: 以下字号/行距/颜色同样只是**无 baseline 且用户未要求格式**时的回退默认值；
#: 有 baseline 走 baseline，用户明确要求走用户要求。
BODY_SIZE_PT = 11
BODY_LINE_SPACING = 1.35
HEADING_SIZES_PT = {1: 16, 2: 13, 3: 12}
HEADING_LINE_SPACING = 1.15
HEADING_SPACE_BEFORE_PT = {1: 18, 2: 14, 3: 10}
HEADING_SPACE_AFTER_PT = {1: 10, 2: 7, 3: 5}
TITLE_SIZE_PT = 22
META_SIZE_PT = 10

#: 标题颜色（H1/H2 标题蓝，H3 深蓝）；灰色用于模板元信息行。
COLOR_TITLE_BLUE = '2E74B5'
COLOR_DARK_BLUE = '1F4D78'
COLOR_GRAY = '595959'


# --------------------------------------------------------------- 外部工具定位


def _resolve(env_var, candidates, which_names):
    """按「环境变量 → PATH → 候选路径表」定位外部可执行文件。

    与 ``latex_to_omml`` 定位 ``MML2OMML.XSL`` 的模式一致：环境变量最高优先，
    其次查 PATH，最后探测常见安装路径。

    跳过 ``.cmd`` / ``.bat`` 包装器：Windows 上 poppler 常以 ``pdftoppm.cmd``
    形式出现在 PATH 里，该包装器在本环境会报
    ``The system cannot find the path specified``，必须继续找原生 exe。
    """
    env = os.environ.get(env_var)
    if env and Path(env).exists():
        return Path(env)
    for name in which_names:
        found = shutil.which(name)
        if found and Path(found).suffix.lower() not in ('.cmd', '.bat'):
            return Path(found)
    for cand in candidates:
        p = Path(os.path.expandvars(cand))
        if p.exists():
            return p
    return None


def find_soffice():
    """定位 LibreOffice 的 ``soffice``（可用 ``MATHDOC_SOFFICE`` 覆盖）。找不到返回 ``None``。"""
    return _resolve(
        'MATHDOC_SOFFICE',
        [
            r'C:\Program Files\LibreOffice\program\soffice.exe',
            r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
            '/Applications/LibreOffice.app/Contents/MacOS/soffice',
            '/usr/bin/soffice',
            '/usr/local/bin/soffice',
        ],
        ['soffice', 'libreoffice'],
    )


def find_pdftoppm():
    """定位 ``pdftoppm``（可用 ``PDFTOPPM`` 覆盖）。找不到返回 ``None``。"""
    home = Path.home()
    return _resolve(
        'PDFTOPPM',
        [
            # poppler 随 agent skills 环境自带的副本（本机实测可用）
            str(home / '.zcode' / 'dependencies' / 'poppler' / 'Library' / 'bin' / 'pdftoppm.exe'),
            str(home / 'scoop' / 'apps' / 'poppler' / 'current' / 'bin' / 'pdftoppm.exe'),
            str(home / 'AppData' / 'Local' / 'Microsoft' / 'WinGet' / 'Links' / 'pdftoppm.exe'),
            r'C:\Program Files\poppler\Library\bin\pdftoppm.exe',
            '/usr/bin/pdftoppm',
            '/usr/local/bin/pdftoppm',
        ],
        ['pdftoppm'],
    )
