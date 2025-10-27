# markdown-image-packer - Markdown 图片打包工具

一个轻量级 Python 脚本，用于自动收集 Markdown 文档中引用的本地图片，统一打包成便携文件夹与压缩包。
 解决图片路径分散、在其他设备或环境中打开图片缺失的问题。

------

## ✨ 功能特点

- ✅ 自动扫描 `.md` 文件中的所有图片引用：
  - Markdown 语法：`![alt](path/to/image.png)`
  - HTML 语法：`<img src="path/to/image.png" />`
- ✅ 自动复制所有本地图片到 `images/` 文件夹。
- ✅ 自动修正 Markdown 中的路径为相对路径（如 `images/example.png`）。
- ✅ 支持：
  - 含中文或空格的文件名；
  - Windows 绝对路径（含反斜杠）；
  - 网络图片（`http://`、`https://`）保留原链接；
  - 图片重名自动编号防止覆盖。
- ✅ 自动生成同名文件夹与 `.zip` 打包文件，方便分发或提交。

------

## 📁 打包后目录结构示例

运行脚本前：

```
📂 project/
 ├─ report.md
 ├─ assets/
 │   ├─ figure1.png
 │   └─ diagram.jpg
```

运行脚本后：

```
📂 project/
 ├─ md_pack.py
 ├─ report/
 │   ├─ report.md
 │   └─ images/
 │        ├─ figure1.png
 │        └─ diagram.jpg
 └─ report.zip
```

------

## ⚙️ 使用方法：命令行运行

```bash
python md_pack.py
```

然后根据提示输入 `.md` 文件的路径，例如：

```
D:\Docs\report.md
```

脚本会自动在相同目录下生成：

- 同名文件夹（包含新的 `.md` 文件与 `images` 子文件夹）
- 同名 `.zip` 打包文件

------

## 🧱 环境要求

- Python ≥ 3.7
- 无需安装任何第三方库
  （使用标准库：`os`、`re`、`shutil`、`zipfile`、`pathlib`、`urllib`）

------

## 📋 执行结果

运行后，终端会显示类似提示：

```
✅ 完成
📂 目录: D:\Docs\report
🗜 压缩包: D:\Docs\report.zip
→ 现在请用 Typora 打开新目录里的 report.md。
```

------

## ⚠️ 注意事项

- 控制台中若出现：

  ```
  ⚠ 找不到图片文件: ...
  ```

  请检查原图片路径是否存在或是否为网络图片。

- 网络图片不会被复制。

- 同名图片将自动重命名为 `_1`, `_2`, `_3` 以避免覆盖。

------

## 🧩 脚本结构

主要函数说明：

| 函数名                         | 作用                                   |
| ------------------------------ | -------------------------------------- |
| `pack()`                       | 主入口函数，控制整体执行流程           |
| `rewrite_markdown_images()`    | 解析并重写 Markdown 文件内容           |
| `copy_to_images_and_get_rel()` | 复制图片并返回新的相对路径             |
| `normalize_candidate_url()`    | 解析 Markdown 图片语法中的路径与标题   |
| `same_file()`                  | 判断文件内容是否一致，用于处理重名情况 |

------

## 📘 示例命令

```bash
python md_pack.py "C:\Projects\report.md"
```

执行后生成：

```
report/
 ├─ report.md
 └─ images/
     ├─ chart.png
     └─ flow.png
report.zip
```

