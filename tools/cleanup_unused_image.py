import logging
import os

from utils import ARTICLE_PATH, IMAGE_PATH, setup_colored_logger

setup_colored_logger()


def get_files(directory, extensions):
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(extensions)
    ]


def read_file_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except (UnicodeDecodeError, OSError) as e:
        logging.error(
            "read file failed, file: %s, err: %s", os.path.basename(file_path), e
        )
        return None


def cleanup_unused_images(article_directory, image_directory):
    article_files = get_files(article_directory, (".md",))
    image_files = get_files(image_directory, (".jpg", ".jpeg", ".png", ".gif", ".svg"))
    used_images = set()

    for article_file in article_files:
        article_content = read_file_content(article_file)
        if article_content:
            for image_file in image_files:
                if os.path.basename(image_file) in article_content:
                    used_images.add(image_file)

    delete_unused_images(image_files, used_images)


def delete_unused_images(image_files, used_images):
    unused_images = set(image_files) - used_images
    for image_file in unused_images:
        logging.info("deleting unused image: %s", os.path.basename(image_file))
        try:
            os.remove(image_file)
        except OSError as e:
            logging.error(
                "delete file failed, file: %s, err: %s", os.path.basename(image_file), e
            )


if __name__ == "__main__":
    logging.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ starting unused image cleanup")
    cleanup_unused_images(ARTICLE_PATH, IMAGE_PATH)
    logging.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ finished unused image cleanup")
