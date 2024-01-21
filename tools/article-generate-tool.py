import string
import time

from easygui import multenterbox, msgbox

from utils import *

if __name__ == '__main__':
    need_continue = True
    article_title, article_categories, article_tags = '', '', ''
    while need_continue:
        need_continue = False
        text, title, input_list = '请输入文章的标题、分类以及标签', '博客文章生成器', ['文章标题', '文章分类', '文章标签']
        output = multenterbox(text, title, input_list, [article_title, article_categories, article_tags])
        if output is not None:
            if output[0] == '':
                title = '温馨提示'
                message = '文章标题不允许为空哦！'
                msgbox(msg=message, title=title, ok_button='OK')
            else:
                article_title, article_categories, article_tags = output[0].strip(), output[1].strip(), output[2].strip()
                random_num = ''.join(map(lambda num: random.choice(string.digits), range(8)))
                article_content = ['---', 'layout: post', f'title: {article_title}', f'permalink: /{random_num}', f'categories: [{article_categories}]',
                                   f'tags: [{article_tags}]', time.strftime('date: %Y-%m-%d %H:%M:%S', time.localtime()), '---', '{% include common/toc.html %}']
                article_name = time.strftime(f'%Y-%m-%d-{article_title}', time.localtime())
                article_path = f'{ROOT_DIR}/_posts/{article_name}.md'
                if not os.path.exists(article_path):
                    with open(article_path, mode='w+', encoding='utf-8') as article:
                        article.write('\n'.join(article_content))
                        title = '温馨提示'
                        message = '成功创建了一篇文章【' + article_name + '.md】哦！'
                        msgbox(msg=message, title=title, ok_button='OK')
                        need_continue = True
