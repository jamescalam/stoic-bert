import requests
import re
from bs4 import BeautifulSoup
from typing import Union
import json
import os
import logging


def get_meditations():
    """
    Imports the meditations by Marcus Aurelius.
    """
    # import Meditations by Marcus Aurelius
    response = requests.get('http://classics.mit.edu/Antoninus/meditations.mb.txt')
    data = response.text
    del response

    # remove everything before and including "Translated by George Long"
    data = data.split('Translated by George Long')[1]

    # remove "----" lines
    data = re.sub(r'([-])\1+', '', data)

    # remove "BOOK ..." lines, for this we use regular expressions
    data = re.sub('BOOK [A-Z]+\n', '', data)

    # remove "THE END" and all that follows it
    data = data.split("THE END")[0]

    # splitting by newline characters
    data = data.split('\n\n')

    # remove empty samples
    data = [x for x in data if x.replace('\s+', '') != '']

    # remove final '\n' characters
    data = [x.replace('\n', ' ') for x in data]

    print(f"We have {len(data)} stoic lessons from Marcus Aurelius")

    # strip any other whitespace and return
    data = [x.strip() for x in data]
    return data


def get_letters():
    """
    Imports 'Epistulae Morales Ad Lucilium' by Seneca
    """

    # import page containing links to all of Seneca's letters
    # get web address
    src = "https://en.wikisource.org/wiki/Moral_letters_to_Lucilius"

    html = requests.get(src).text  # pull html as text
    soup = BeautifulSoup(html, "html.parser")  # parse into BeautifulSoup object

    # create function to pull letter from webpage (pulls text within <p> elements
    def pull_letter(http):
        print(f"Pulling {http.split('/')[-1:][0]}")
        # get html from webpage given by 'http'
        html = requests.get(http).text
        # parse into a beautiful soup object
        soup = BeautifulSoup(html, "html.parser")

        # build text contents within all p elements
        txt = '\n'.join([x.text for x in soup.find_all('p')])
        # replace extended whitespace with single space
        txt = txt.replace('  ', ' ')
        # replace webpage references ('[1]', '[2]', etc)
        txt = re.sub('\[[0-9]+\]', '', txt)
        # replace all number bullet points that Seneca uses ('1.', '2.', etc)
        txt = re.sub('[0-9]+. ', '', txt)
        # split by double newlines
        lines = txt.split('\n\n')
        # strip and remove short lines
        lines = [x.strip() for x in lines if len(x.strip()) > 40]
        return lines

    # compile RegEx for finding 'Letter 12', 'Letter 104' etc
    letters_regex = re.compile("^Letter\s+[0-9]{1,3}$")
    # get all links
    links = soup.find_all('a')
    # initalize data
    letters = []
    # loop through all letter pages
    for link in links:
        # confirm we want this data
        if len(link.contents) > 0 and letters_regex.match(str(link.contents[0])):
            title = str(link.contents[0])
            href = link.get('href')
            # get text content from letter
            texts = pull_letter(f"https://en.wikisource.org{href}")
            # now we loop through and append the new texts
            for text in texts:
                letters.append({'title': title, 'href': href, 'text': text})
    return letters


def save(data: Union[list, dict], filepath: str):
    if type(data) is list:
        with open(filepath, 'w', encoding='utf-8') as fp:
            fp.write('\n'.join(data))
    elif type(data) is dict:
        with open(filepath, 'w', encoding='utf-8') as fp:
            json.dump(data, fp, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)
    log.info('Retrieving Meditations')
    meditations = get_meditations()
    log.info('Retrieving Letters')
    letters = get_letters()
    # now we save the data
    with open('stoic-corpus.jsonl', 'w', encoding='utf-8') as fp:
        i = 0
        for line in meditations:
            line = {'id': str(i), 'text': line, 'source': 'meditations'}
            fp.write(json.dumps(line)+'\n')
            i += 1
        for line in letters:
            line = {'id': str(i), 'text': line['text'], 'source': 'letters'}
            fp.write(json.dumps(line)+'\n')
            i += 1