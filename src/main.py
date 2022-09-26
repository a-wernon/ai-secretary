import datetime

from bs4 import BeautifulSoup
from glob import glob


def extract_all_messages_from_html(html):
    a = BeautifulSoup(html, "html.parser")
    b = a.find_all('div', class_="pam _3-95 _2ph- _a6-g uiBoxWhite noborder")
    results = []
    for tag in b:
        name = tag.find_all('div', class_="_3-95 _2pim _a6-h _a6-i")[0].contents[0]
        date_str = tag.find_all('div', class_="_3-94 _a6-o")[0].contents[0]

        # workaround for strptime
        date, year, time = date_str.split(',')
        if len(time.split(':')[0]) == 2:
            time = ' 0' + time[1:]
        date_str = ','.join([date, year, time])

        timestamp = datetime.datetime.strptime(date_str, '%b %d, %Y, %I:%M %p').timestamp()
        html_content = tag.find_all('div', class_='')
        content = []
        for c in html_content:
            if len(c.find_all('div', class_='')) == 0 and len(c.contents) > 0:
                content.append(c.contents[0])
        if len(content) != 1:
            print(*content, sep='\n')
            print('Warning, too many content lines')
        results.append([timestamp, name, content])

    return results


def glue_neighbours_cut_owner(ls_msg, owner='Artem Wernon'):
    """

    :param ls_msg: [timestamp, name, content]
    :return: list[str]
    """
    ls_msg.sort()
    result = []
    current_message = []
    for ms in ls_msg:
        if ms[1] != owner:
            current_message += ms[2]
        elif len(current_message) != 0:
            result.append(', '.join(current_message))
            current_message = []
    return result



if __name__ == '__main__':
    html = open('/home/art-bash/Documents/datasets_msg/wernon/messages/inbox/mihailhrusev_lt82ugdf8g/message_1.html',
                'r')
    a = (extract_all_messages_from_html(html))
    glue_neighbours_cut_owner(a)