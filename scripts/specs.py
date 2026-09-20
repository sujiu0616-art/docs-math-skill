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

#: 以下字体均为**用户未明确指定格式时**的默认值；用户指定格式时以用户为准。
FONT_BODY_CN = '宋体'
FONT_HEADING_CN = '黑体'
FONT_TITLE_CN = '方正小标宋简体'
FONT_LATIN = 'Times New Roman'

#: 表头单元格底纹。validator 断言它，生成侧用它。
TABLE_HEADER_FILL = 'E8EEF5'

#: 无 baseline 文档时的页面回退预设（英寸）。
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0


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
