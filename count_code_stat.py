import os

target_exts = [".bat", ".html", ".json", ".md", ".py", ".txt"]
exclude_dirs = {".conda", ".venv"}


def is_source_file(filename):
    return any(filename.endswith(ext) for ext in target_exts)


def count_code_stat(root_dir):
    total_lines = 0
    total_bytes = 0
    file_stats = []
    ext_stats = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in filenames:

            if is_source_file(filename):
                filepath = os.path.join(dirpath, filename)
                relpath = os.path.relpath(filepath, root_dir)
                ext = os.path.splitext(filename)[1]

                try:
                    with open(filepath, "rb") as f:

                        content = f.read()
                        lines = content.count(b"\n") + 1 if content else 0
                        bytes_ = len(content)
                        total_lines += lines
                        total_bytes += bytes_
                        file_stats.append((relpath, ext, lines, bytes_))

                        if ext not in ext_stats:
                            ext_stats[ext] = {
                                "count": 0, "lines": 0, "bytes": 0}

                        ext_stats[ext]["count"] += 1
                        ext_stats[ext]["lines"] += lines
                        ext_stats[ext]["bytes"] += bytes_

                except Exception as e:
                    print(f"无法读取文件: {relpath}，原因: {e}")

    return file_stats, total_lines, total_bytes, ext_stats


def adjust_chinese_width(text, width):
    chinese_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return width - chinese_count


def format_field(text, width):
    chinese_count = sum(1 for c in str(text) if "\u4e00" <= c <= "\u9fff")
    real_width = width - chinese_count
    return f"{text:<{real_width}}"


def format_field_right(text, width):
    chinese_count = sum(1 for c in str(text) if "\u4e00" <= c <= "\u9fff")
    real_width = width - chinese_count
    return f"{text:>{real_width}}"


if __name__ == "__main__":
    root = os.path.dirname(os.path.abspath(__file__))
    file_stats, lines, bytes_, ext_stats = count_code_stat(root)
    header_name = "文件路径"
    header_type = "文件类型"
    header_lines = "行数"
    header_bytes = "字节数"
    header_count = "文件数"
    path_width = 50
    type_width = 8
    lines_width = 8
    bytes_width = 12
    count_width = 8

    print("\n按文件路径统计：")

    print(
        format_field(header_name, path_width) + " "
        + format_field(header_type, type_width) + " "
        + format_field_right(header_lines, lines_width) + " "
        + format_field_right(header_bytes, bytes_width)
    )

    print("-" * (path_width + type_width + lines_width + bytes_width + 3))

    for relpath, ext, l, b in file_stats:
        print(
            format_field(relpath, path_width) + " "
            + format_field(ext, type_width) + " "
            + f"{l:>{lines_width}} "
            + f"{b:>{bytes_width}}"
        )

    print("-" * (path_width + type_width + lines_width + bytes_width + 3))

    # 第二块：按文件类型统计
    print("\n按文件类型统计:")

    print(
        format_field("文件类型", path_width) + " "
        + format_field("文件数", type_width) + " "
        + format_field_right(header_lines, lines_width) + " "
        + format_field_right(header_bytes, bytes_width)
    )

    print("-" * (path_width + type_width + lines_width + bytes_width + 3))

    for ext in sorted(ext_stats.keys()):
        ext_info = ext_stats[ext]
        ext_text = f"{ext} 文件"

        print(
            format_field(ext_text, path_width) + " "
            + format_field(ext_info["count"], type_width) + " "
            + f"{ext_info['lines']:>{lines_width}} "
            + f"{ext_info['bytes']:>{bytes_width}}"
        )

    print("-" * (path_width + type_width + lines_width + bytes_width + 3))

    # 第三块：合计
    total_text = "合计"

    print(
        format_field(total_text, path_width) + " "
        + format_field(len(file_stats), type_width) + " "
        + f"{lines:>{lines_width}} "
        + f"{bytes_:>{bytes_width}}"
    )

    print()
