from utils import *


def cleanup_unused_images(article_directory, image_directory):
    article_files = [os.path.join(article_directory, f) for f in os.listdir(article_directory) if f.endswith(".md")]
    image_files = [os.path.join(image_directory, f) for f in os.listdir(image_directory) if f.endswith((".jpg", ".jpeg", ".png", ".gif"))]
    used_images = set()
    for article_file in article_files:
        try:
            with open(article_file, 'r', encoding='utf-8') as file:
                article_content = file.read()
                for image_file in image_files:
                    if os.path.basename(image_file) in article_content:
                        used_images.add(image_file)
        except UnicodeDecodeError:
            logging.error(f"reading file error: {os.path.basename(article_file)}")
    delete_unused_images(image_files, used_images)


def delete_unused_images(image_files, used_images):
    for image_file in image_files:
        if image_file not in used_images:
            logging.info(f"deleting unused image: {os.path.basename(image_file)}")
            os.remove(image_file)


if __name__ == "__main__":
    logging.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ unused image cleanup start')
    cleanup_unused_images(ARTICLE_PATH, IMAGE_PATH)
    logging.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ unused image cleanup finish')
