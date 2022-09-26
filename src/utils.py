import datetime
import re
import emoji

import tqdm as tqdm
from bs4 import BeautifulSoup
import bs4
import glob

replace_month = {
    'дек': 'Dec',
    'мая': 'May',
    'фев': 'Feb',
    'янв': 'Jan',
    'сен': 'Sep',
    'мар': 'Mar',
    'ноя': 'Nov',
    'апр': 'Apr',
    'авг': 'Aug',
    'окт': 'Oct',
    'июн': 'Jun',
    'июл': 'Jul'
}


def is_html(x):
    return type(x) != bs4.element.NavigableString


def remove_emoji(x):
    return ''.join(c for c in x if c not in emoji.EMOJI_DATA)


def extract_all_messages_from_html(html):
    html_soup = BeautifulSoup(html, "html.parser")
    b = html_soup.find_all('div', class_="pam _3-95 _2ph- _a6-g uiBoxWhite noborder")
    results = []
    for tag in b:
        try:
            name = tag.find_all('div', class_="_3-95 _2pim _a6-h _a6-i")[0].contents[0]
        except IndexError:
            continue
        date_str = tag.find_all('div', class_="_3-94 _a6-o")[0].contents[0]

        # workaround for strptime and rus dt

        date, time = date_str.split(',')
        for k in replace_month:
            date = date.replace(k, replace_month[k])
        if len(time.split(':')[0]) == 2:
            time = ' 0' + time[1:]
        date_str = ','.join([date, time])

        timestamp = datetime.datetime.strptime(date_str, '%d %b %Y г., %H:%M').timestamp()
        html_content = tag.find_all('div', class_='')
        content = []
        for c in html_content:
            if len(c.find_all('div', class_='')) == 0 and len(c.contents) > 0:
                if not is_html(c.contents[0]) and 'Liked a message' not in repr(c.contents[0]):
                    content.append(remove_emoji(c.contents[0]))
        if len(content) > 1:
            # print(*content, len(content),sep='\n')
            # print('Warning, too many content lines')
            pass
        if len(content) >= 1:
            results.append([timestamp, name, content])

    return results


def glue_neighbours_cut_owner(ls_msg, owner='Artem Wernon', min_length_words=5):
    """

    :param min_length_words: cut msg with less amnt of words
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
            rs = ', '.join(current_message).lower()
            if len(rs.split()) >= min_length_words:
                result.append(rs)
            current_message = []
    return result

def glue_all_but_owner(ls_msg, owner='Artem Wernon', min_length_words=5):
    """

    :param min_length_words: cut msg with less amnt of words
    :param ls_msg: [timestamp, name, content]
    :return: list[str]
    """
    ls_msg.sort()
    result = []
    current_message = []
    for ms in ls_msg:
        if ms[1] != owner:
            current_message += ms[2]
    if len(current_message) != 0:
        rs = ', '.join(current_message).lower()
        if len(rs.split()) >= min_length_words:
            result.append(rs)
    return result

def glue_all(ls_msg, owner='Artem Wernon', min_length_words=5):
    """
    :param min_length_words: cut msg with less amnt of words
    :param ls_msg: [timestamp, name, content]
    :return: list[str]
    """
    ls_msg.sort()
    result = []
    current_message = []
    for ms in ls_msg:
        current_message += ms[2]
    if len(current_message) != 0:
        rs = ', '.join(current_message).lower()
        if len(rs.split()) >= min_length_words:
            result.append(rs)
    return result



if __name__ == '__main__':
    '''html = open('/home/art-bash/Documents/datasets_msg/wernon/messages/inbox/mihailhrusev_lt82ugdf8g/message_1.html',
                'r')
    a = (extract_all_messages_from_html(html))
    glue_neighbours_cut_owner(a)'''

    folder = '/home/art-bash/Documents/datasets_msg/xstore/messages/inbox'
    users = glob.glob(folder + '/*')
    res = []
    for u in tqdm.tqdm(users):
        msg_raw = extract_all_messages_from_html(open(u + '/message_1.html', 'r'))
        messages = glue_all(msg_raw, owner='ТЕЛЕФОНЫ / ГРОЗНЫЙ / АНТИГРАВИЙНАЯ ПЛЕНКА')
        res += messages

    rs_f = open('glue_all.txt', 'w')
    for ms in res:
        ms_filt = ms.replace('\n', ' ')
        rs_f.write(ms_filt + '\n')
    rs_f.close()
