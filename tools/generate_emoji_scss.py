import logging
import os

from utils import ROOT_DIR, setup_colored_logger

setup_colored_logger()

PROJECT_ROOT = ROOT_DIR
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif")


def generate_emoji_scss(image_dir, scss_dir):
    os.makedirs(scss_dir, exist_ok=True)

    emoji_dirs = []
    generated_files = []
    for name in sorted(os.listdir(image_dir)):
        emoji_dir = os.path.join(image_dir, name)
        if not os.path.isdir(emoji_dir):
            continue

        emoji_dirs.append(name)
        scss_file_name = f"_{name}.scss"
        scss_file_path = os.path.join(scss_dir, scss_file_name)
        generated_files.append(scss_file_name)

        image_files = []
        for root, dirs, files in os.walk(emoji_dir):
            dirs.sort()
            for file_name in sorted(files):
                if file_name.lower().endswith(IMAGE_EXTENSIONS):
                    image_files.append(os.path.join(root, file_name))

        content = []
        for image_file in image_files:
            relative_image_path = os.path.relpath(image_file, image_dir)
            relative_image_path = relative_image_path.replace(os.sep, "/")
            class_name = os.path.splitext(relative_image_path)[0].replace("/", "_")
            content.append(f".{class_name}::before {{")
            content.append(
                f'  background-image: url("#{{$images}}/emoji/{relative_image_path}");'
            )
            content.append("}")
            content.append("")

        with open(scss_file_path, "w", encoding="utf-8") as scss_file:
            scss_file.write("\n".join(content).rstrip() + "\n")

        logging.info(
            "successfully generated emoji scss: %s",
            os.path.relpath(scss_file_path, PROJECT_ROOT),
        )

    index_file_path = os.path.join(scss_dir, "_index.scss")
    with open(index_file_path, "w", encoding="utf-8") as index_file:
        index_file.write('@import "base";\n')
        for name in emoji_dirs:
            index_file.write(f'@import "{name}";\n')
    logging.info(
        "successfully generated emoji scss: %s",
        os.path.relpath(index_file_path, PROJECT_ROOT),
    )

    keep_files = {"_base.scss", "_index.scss"}.union(generated_files)
    for file_name in os.listdir(scss_dir):
        if file_name.endswith(".scss") and file_name not in keep_files:
            file_path = os.path.join(scss_dir, file_name)
            os.remove(file_path)
            logging.info(
                "successfully removed stale emoji scss: %s",
                os.path.relpath(file_path, PROJECT_ROOT),
            )


if __name__ == "__main__":
    emoji_image_dir = os.path.join(PROJECT_ROOT, "assets", "images", "emoji")
    emoji_scss_dir = os.path.join(PROJECT_ROOT, "_sass", "components", "emoji")

    generate_emoji_scss(emoji_image_dir, emoji_scss_dir)
