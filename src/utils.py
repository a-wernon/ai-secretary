import datetime
import glob

import bs4
import emoji
import gensim.downloader as api
import nltk
import pymorphy2
import tqdm
from bs4 import BeautifulSoup
from Levenshtein import distance as lev
from transliterate import translit


info = api.info()  # show info about available models/datasets
model = api.load("word2vec-ruscorpora-300")

entire_vocab = model.key_to_index

nltk.download('stopwords')
# pymorphy2 анализатор
morph = pymorphy2.MorphAnalyzer()
# стоп слова из nltk
stops = nltk.corpus.stopwords.words('russian')

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

convert = {
    'A': 'ADJ',
    'ADV': 'ADV',
    'ADVPRO': 'ADV',
    'ANUM': 'ADJ',
    'APRO': 'DET',
    'COM': 'ADJ',
    'CONJ': 'SCONJ',
    'INTJ': 'INTJ',
    'NONLEX': 'X',
    'NUM': 'NUM',
    'PART': 'PART',
    'PR': 'ADP',
    'S': 'NOUN',
    'SPRO': 'PRON',
    'UNKN': 'X',
    'V': 'VERB'
}

block_list_for_words = [
    'ассалам',
    'мяло',
    'ху',
    'ял',
    'ез',
    'юй',
    'ааа',
    'мах',
    'ала',
    'аз',
    'aa',
    'ца',
    'ло',
    'хала',
    'дар',
    'сага',
    'хум',
    'аш',
    'дик',
    'ду',
    'ху',
    'мел',
]  # if word is in the msg, then it is dropped


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
                if not is_html(c.contents[0]):
                    content.append(remove_emoji(c.contents[0]))
        if len(content) >= 1:
            results.append([timestamp, name, content])

    # results of format list([timestamp, name, content])

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


def is_same(x, y):
    if len(x) <= 3:
        return x == y
    else:
        return lev(x, y) <= 3


def filt_message(msg, enable_normalise=True, enable_translit=True, try_to_voc=True, force_voc=True):
    block_list_for_msg = [
        '@xstore95',
        'video',
        'started',
        'ended',
        'group'
    ]  # if word is in the msg, then entire msg is ignored
    words = msg.split()
    if enable_translit:
        words = [translit(x, 'ru')for x in words]
    if enable_normalise:
        words = [normalise_text(x) for x in words]
    orig_words = msg.split()
    new_msg = ''
    assert len(words) == len(orig_words)
    for i, word in enumerate(words):
        if orig_words[i] in block_list_for_words or len(word) <= 3:
            continue
        if orig_words[i] in block_list_for_msg:
            return ''
        res = get_top_closest_in_vocab_and_tag(word)
        if try_to_voc:
            if is_same(word, res[0][0][1].split('_')[0]):
                new_msg += res[0][0][1].split('_')[0] + ' '
            else:
                if not force_voc:
                    new_msg += word + ' '
        else:
            new_msg += word + ' '
    return new_msg


def norm_and_filt(results):
    # results of format [[ts, name, content]]
    for res in results:

        content_list = res[2]
        new_content_list = []
        for msg_text in content_list:
            new_msg_text = filt_message(msg_text.lower())
            if new_msg_text != '':
                new_content_list.append(new_msg_text)
        res[2] = new_content_list
    return results

tag_cache = {

}


def tag(word='пожар', pohui_flag=True):
    if pohui_flag:
        return word, 'NOUN'
    else:
        if word in tag_cache:
            return tag_cache[word]
        from pymystem3 import Mystem
        stemmer = Mystem()
        processed = stemmer.analyze(word)[0]
        lemma = processed["analysis"][0]["lex"].lower().strip()
        pos = processed["analysis"][0]["gr"].split(',')[0]
        pos = pos.split('=')[0].strip()
        pos = convert[pos]
        tagged = lemma + '_' + pos
        tag_cache[word] = (lemma, pos)
        return lemma, pos


baddest_words = []

cache = {

}


def get_top_closest_in_vocab_and_tag(word):
    results = []  # list of (dist, word)
    try:
        word = ''.join([c for c in word if c.isalpha()])
        n_word, pos = tag(word)
    except:
        baddest_words.append(word)
        return [[100000, ':(']], word, ''
    if n_word in cache:
        cut_res = cache[n_word]
    else:
        if n_word + '_' + pos in entire_vocab:
            cut_res = [[0, n_word]]
        else:
            return [[100000, ':(']], word, ''
            print(n_word, '-----------', sep='\n')
            for c in entire_vocab:
                key, key_pos = c.split('_')
                dist = lev(key, n_word)
                results.append([dist, c])

            cut_res = sorted(results)[:10]
    return cut_res, n_word, pos


def normalise_text(txt):
    words = [''.join(c for c in x if c.isalpha()) for x in txt.split()]
    words = [x for x in [morph.normal_forms(word)[0] for word in words] \
             if x not in stops]
    return ' '.join(words)


if __name__ == '__main__':
    '''html = open('/home/art-bash/Documents/datasets_msg/wernon/messages/inbox/mihailhrusev_lt82ugdf8g/message_1.html',
                'r')
    a = (extract_all_messages_from_html(html))
    glue_neighbours_cut_owner(a)'''

    print(norm_and_filt([['','',['автомобильная зарядка тото за 2 ял вариант юй?, ассаламу 1алайкум, ваа1алейкум ассалам, за 2200₽ лур ю брат), дел рез хил!, до ск работаете?, до 19 по любому будем в магазине дала мукъ лахь']]]))

    raise IndexError

    folder = '/home/art-bash/Documents/datasets_msg/xstore/messages/inbox'
    users = glob.glob(folder + '/*')

    extracts = {
        'glue_all': glue_all,
        'glue_all_but_owner': glue_all_but_owner,
        'glue_split_owner': glue_neighbours_cut_owner
    }

    extracts = {
        'glue_all_but_owner': glue_all_but_owner
    }

    for extr in extracts:
        res = []
        for u in tqdm.tqdm(users):
            msg_raw = extract_all_messages_from_html(open(u + '/message_1.html', 'r'))

            '''
            filtering stuff mostly happens here
            '''

            messages_raw = extracts[extr](msg_raw, owner='ТЕЛЕФОНЫ / ГРОЗНЫЙ / АНТИГРАВИЙНАЯ ПЛЕНКА')

            msg_filt = norm_and_filt(msg_raw)

            messages = extracts[extr](msg_filt, owner='ТЕЛЕФОНЫ / ГРОЗНЫЙ / АНТИГРАВИЙНАЯ ПЛЕНКА')

            res += messages

        rs_f = open('../dat/' + extr + '.txt', 'w')
        for ms in res:
            ms_filt = ms.replace('\n', ' ')
            ms_filt = ms_filt.replace(';', ',')
            rs_f.write(ms_filt + '\n')
        rs_f.close()
