import os
import re
import shutil
import zipfile
from pathlib import Path
from urllib.parse import unquote

# 允许路径里出现空格、中文、反斜杠、冒号等
# 思路：匹配括号里的整段，然后再手动拆出url和可选"title"
MD_IMG_RE = re.compile(
    r'!\[(?P<alt>[^\]]*)\]'        # ![alt]
    r'\('
    r'(?P<inner>[^)]*)'           # 括号里的整段，不急着拆
    r'\)'
)

# <img src="..."> 继续保留
HTML_IMG_RE = re.compile(
    r'<img\s+[^>]*?src=["\'](?P<src>[^"\']+)["\'](?P<rest>[^>]*)>',
    flags=re.IGNORECASE
)

def same_file(a: Path, b: Path) -> bool:
    if not a.exists() or not b.exists():
        return False
    if a.stat().st_size != b.stat().st_size:
        return False
    with open(a, "rb") as fa, open(b, "rb") as fb:
        return fa.read() == fb.read()

def normalize_candidate_url(inner: str):
    """
    inner 可能是:
      C:\foo bar\图像 1.png "说明"
      ./images/x.png "title"
      images/x.png
    我们要把真正的路径拿出来，和可选title分开
    规则：
    - 如果 inner 里有引号，则最后一个引号开始的是 title
      e.g.  path/to/file.png "some title"
    - 否则全是路径
    """
    inner = inner.strip()

    # 如果有未转义的 "xxx"
    # 我们找第一个双引号，把它后面的当成 title
    if '"' in inner:
        first_quote = inner.find('"')
        url_part = inner[:first_quote].strip()
        title_part = inner[first_quote:].strip()
        # 去掉首尾引号 "..."
        if title_part.startswith('"') and title_part.endswith('"') and len(title_part) >= 2:
            title_part = title_part[1:-1]
    else:
        url_part = inner.strip()
        title_part = ""

    # 去掉可能包在url外层的引号
    url_part = url_part.strip().strip('"').strip("'")
    return url_part, title_part

def copy_to_images_and_get_rel(md_dir: Path, dest_root: Path, images_dir: Path, original_path_str: str):
    """
    把 original_path_str 指向的图片复制到 images_dir，
    返回 'images/文件名'；如果是网络图或找不到则返回 None
    """
    raw = original_path_str.strip()
    raw = unquote(raw)

    # 网络图直接跳过
    lower = raw.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        return None

    # Windows 路径里可能有反斜杠，我们不强行改，但 Path() 会接受
    candidate = Path(raw)

    # 如果不是绝对路径，就当它是相对原md所在目录的
    if not candidate.is_absolute():
        candidate = (md_dir / raw).resolve()

    if not candidate.exists():
        print(f"⚠ 找不到图片文件: {raw}")
        return None

    # 冲突解决：same_file()不同就 _1 _2 ...
    dest_name = candidate.name
    dest_path = images_dir / dest_name
    idx = 1
    while dest_path.exists() and not same_file(candidate, dest_path):
        stem = candidate.stem
        suf = candidate.suffix
        dest_name = f"{stem}_{idx}{suf}"
        dest_path = images_dir / dest_name
        idx += 1

    shutil.copy(candidate, dest_path)

    return f"images/{dest_name}"

def rewrite_markdown_images(md_text: str, md_dir: Path, new_root: Path, images_dir: Path) -> str:
    # ------- 第一轮：处理 ![](...) -------
    out_parts = []
    last_idx = 0

    for m in MD_IMG_RE.finditer(md_text):
        out_parts.append(md_text[last_idx:m.start()])

        alt = m.group("alt") or ""
        inner = m.group("inner") or ""

        # 把 inner 拆成 路径 + 可选title
        url_part, title_part = normalize_candidate_url(inner)

        new_rel = copy_to_images_and_get_rel(
            md_dir=md_dir,
            dest_root=new_root,
            images_dir=images_dir,
            original_path_str=url_part
        )

        if new_rel is None:
            # 复制失败/网络图 -> 原样保留
            out_parts.append(m.group(0))
        else:
            if title_part:
                new_chunk = f'![{alt}]({new_rel} "{title_part}")'
            else:
                new_chunk = f'![{alt}]({new_rel})'
            out_parts.append(new_chunk)

        last_idx = m.end()

    out_parts.append(md_text[last_idx:])
    tmp_text = "".join(out_parts)

    # ------- 第二轮：处理 <img src="..."> -------
    out_parts = []
    last_idx = 0

    for m in HTML_IMG_RE.finditer(tmp_text):
        out_parts.append(tmp_text[last_idx:m.start()])

        src = m.group("src") or ""
        rest = m.group("rest") or ""

        new_rel = copy_to_images_and_get_rel(
            md_dir=md_dir,
            dest_root=new_root,
            images_dir=images_dir,
            original_path_str=src
        )

        if new_rel is None:
            out_parts.append(m.group(0))
        else:
            new_tag = f'<img src="{new_rel}"{rest}>'
            out_parts.append(new_tag)

        last_idx = m.end()

    out_parts.append(tmp_text[last_idx:])
    final_text = "".join(out_parts)

    return final_text

def pack(md_file_path: str):
    md_path = Path(md_file_path).resolve()
    md_dir = md_path.parent

    # 输出目录：跟原md同名（无扩展名）
    base_name_no_ext = md_path.stem
    new_root = md_dir / base_name_no_ext
    images_dir = new_root / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    original_md = md_path.read_text(encoding="utf-8")

    # 重写 markdown（并在过程中把图复制过去）
    new_md_text = rewrite_markdown_images(
        md_text=original_md,
        md_dir=md_dir,
        new_root=new_root,
        images_dir=images_dir
    )

    # 写新的 md（保持原文件名，包括后缀）
    new_md_path = new_root / md_path.name
    new_md_path.write_text(new_md_text, encoding="utf-8")

    # 顺手打个 zip，方便直接交
    zip_path = md_dir / f"{base_name_no_ext}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(new_root):
            for f in files:
                full_fp = Path(root) / f
                # zip里保持相对 md_dir 的层级：
                arcname = full_fp.relative_to(md_dir)
                z.write(full_fp, arcname=str(arcname))

    print("✅ 完成")
    print(f"📂 目录: {new_root}")
    print(f"🗜 压缩包: {zip_path}")
    print("→ 现在请用 Typora 打开新目录里的同名 .md 文件。")

if __name__ == "__main__":
    md_file = input("请输入你的 Markdown 文件路径: ").strip().strip('"')
    pack(md_file)
