# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from bs4 import BeautifulSoup


def add_elem_to_dict_list(dict, key, value):
    if key in dict:
        dict[key] += value
    else:
        dict[key] = value


def extract_all_messages_from_html(html):
    a = BeautifulSoup(html, "html.parser")
    b = a.find_all('div', class_="pam _3-95 _2ph- _a6-g uiBoxWhite noborder")
    results = {}
    for tag in b:
        name = tag.find_all('div', class_="_3-95 _2pim _a6-h _a6-i")[0].contents[0]
        print(name)
        html_content = tag.find_all('div', class_='')
        content = []
        for c in html_content:
            if len(c.find_all('div', class_='')) == 0 and len(c.contents) > 0:
                content.append(c.contents[0])
        if len(content) != 1:
            print(*content, sep='\n')
            print('Warning, many content lines')
        add_elem_to_dict_list(results, key=name, value=content)
    return results

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    html = open('/home/art-bash/Documents/datasets_msg/wernon/messages/inbox/mihailhrusev_lt82ugdf8g/message_1.html', 'r')
    print(extract_all_messages_from_html(html))


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
