import functools
import json
import re
import binascii
import PySimpleGUI as sg
import requests
import numpy as np
import get_id
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords
import nltk
nltk.download('stopwords')


def check_error(func):
    """This decorator handles errors"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(e)
            if type(e).__name__ == "FileNotFoundError":
                print("Oops, I can't find files of these task.")
                print("Please, check that the first letter of the file name is the number of the task")
            elif type(e).__name__ == "JSONDecodeError":
                print("I can't read it. Please, use ipynb format")
            elif type(e).__name__ == "ZeroDivisionError":
                print("The number of words in the file must be greater than "
                      "the shingles length")
            else:
                print(type(e).__name__)

    return wrapper


def download_file_from_google_drive(id):
    """
    this function fownloads file with certain id from drive
    :param id: str, id of file
    :return: text and code of student work
    """
    URL = "https://docs.google.com/uc?export=download"

    with requests.Session() as s:
        response = s.get(URL, params={'id': id}).json()
        py_source = '\n'
        markdown = '\n'
        for x in response['cells']:
            if x['cell_type'] == 'code':
                for x2 in x['source']:
                    if x2[:6] != 'import' and x2[:4] != 'from' and x2[0] != '#':
                        py_source = py_source + x2
                    if x2[-1] != '\n':
                        py_source = py_source + '\n'
            if x['cell_type'] == 'markdown':
                for x2 in x['source']:
                    markdown = markdown + x2
                    if x2[-1] != '\n':
                        markdown = markdown + '\n'
        return py_source, markdown


def read_jupiter(link):
    """
    This functions read file from computer
    :param link: str, link to file
    :return: text and code of student work
    """
    with open(link, 'r', encoding='utf-8', errors='ignore') as file:
        source = file.read()
        y = json.loads(source)
        py_source = '\n'
        markdown = '\n'
        for x in y['cells']:
            if x['cell_type'] == 'code':
                for x2 in x['source']:
                    if x2[:6] != 'import' and x2[:4] != 'from' and x2[0] != '#':
                        py_source = py_source + x2
                    if x2[-1] != '\n':
                        py_source = py_source + '\n'
            if x['cell_type'] == 'markdown':
                for x2 in x['source']:
                    markdown = markdown + x2
                    if x2[-1] != '\n':
                        markdown = markdown + '\n'
    return py_source, markdown


def get_dict_id(number_of_task):
    """
    This function matches id and names of files
    :param number_of_task: str
    :return: dict with names and ids of students works from drive
    """
    student_works = {}
    with open(number_of_task + '_idToFilesGoogleDrive.txt') as id_file:
        for line in id_file:
            id, name = re.split("\t", line)
            student_works[name] = id
    return student_works


def get_markdowns_and_codes(link):
    """
    This functions gets all needed texts and codes from student works
    :param link: link to the work needed to check
    :return: text and code of the work needed to check, and dict of students works from drive
    """
    number_of_task = re.split("/", link)[-1][0]
    student_works = get_dict_id(number_of_task)
    original_work = read_jupiter(link)
    for work_name, work_id in student_works.items():
        student_works[work_name] = download_file_from_google_drive(work_id)
    return original_work, student_works


def stemming(word, language='russian'):
    """
    This function deletes common ending
    :param word: str
    :return: str
    """
    stemmer = SnowballStemmer(language, ignore_stopwords=True)
    word = stemmer.stem(word)
    return word


def delete_stop_words(text, language='russian'):
    """
    This function deletes stop words
    :param text: list
    :return: list
    """
    stop_words = set(stopwords.words(language))
    clear_text = [stemming(word) for word in text if word not in stop_words]
    return clear_text


def get_hashed_shingle(text, shingle_length=4):
    """
    This function divides the text into shingles
     and calculate check sums with CRC32
    :param text: list
    :param shingle_length: int, shingle length from 3 to 10, the shorter the
    length, the more accurate the test result
    :return: list
    """
    shingles_check_sum = []  # list of shingles
    for i in range(len(text) - shingle_length + 1):
        shingle = text[i: i + shingle_length]
        string_shingle = ' '.join(shingle)
        shingles_check_sum.append(binascii.crc32(string_shingle.encode('utf-8')))
    return shingles_check_sum


def compare_markdowns(*markdowns, shingle_length):
    """
    This function compares text files and shows parameters of similarity
    :param markdowns: list of two markdowns
    :param shingle_length: int
    """
    shingles = []
    for markdown in markdowns:
        text = delete_stop_words(re.split(r'\W+', markdown.lower()))
        shingles_from_text = get_hashed_shingle(text, shingle_length=shingle_length)
        shingles.append(shingles_from_text)
    count = 0
    for i in range(len(shingles[0])):
        if shingles[0][i] in shingles[1]:
            count += 1
    return count / len(shingles[0]) * 100


def get_fingerprint(code, k=3, t=5):
    """
    :param code: list
    :param k: int, length of substring, k-grams
    :param t: int, guarantee threshold
    :return: tuple of hashes
    """
    number_of_tokens = int(len(code) / k)
    tokens = np.zeros(number_of_tokens)
    for i in range(number_of_tokens):
        token = code[i * k: i * k + k]
        string_token = ' '.join(token)
        tokens[i] = binascii.crc32(string_token.encode('utf-8'))
    w = t - k + 1
    number_of_hashes = number_of_tokens - w + 1
    hash_mins = []
    for i in range(number_of_hashes):
        window = tokens[i:i + w]
        minimum = np.min(window)
        if minimum not in hash_mins:
            hash_mins.append(minimum)
    return tuple(hash_mins)


def compare_codes(*codes, k=3, t=5):
    """
    This function compares codes using the fingerprint algorithm
    :param codes: list
    :param k: int, length of substring, k-grams
    :param t: int, guarantee threshold
    :return: int, similarity
    """
    fingerprints = []
    for code in codes:
        fingerprint = get_fingerprint(re.split(r'\W+', code.lower()), k, t)
        fingerprints.append(fingerprint)
    count = 0
    for i in range(len(fingerprints[0])):
        if fingerprints[0][i] in fingerprints[1]:
            count += 1
    return count / len(fingerprints[0]) * 100


@check_error
def compare(link, k, t, shingle_length, sort_parameter):
    """
    This function combines all methods
    :param link: str, link to file
    :param k: int, length of substring, k-grams
    :param t: int, guarantee threshold
    :param shingle_length: int
    :param sort_parameter: 0 (sort by code similarity) or 1 (sort by text similarity)
    """
    print(f"Current Work: {link}")
    original_work, student_works = get_markdowns_and_codes(link)
    code_text_name = []
    for work_name, work_code_text in student_works.items():
        code_sim = round(compare_codes(original_work[0], work_code_text[0], k=k, t=t), 2)
        text_sim = round(compare_markdowns(original_work[1], work_code_text[1], shingle_length=shingle_length), 2)
        code_text_name.append([code_sim, text_sim, work_name[:-7]])
    code_text_name.sort(key=lambda code_text_name: code_text_name[sort_parameter], reverse=True)
    print("Comparison:")
    for i in range(3):
        if i < len(code_text_name):
            code_sim = code_text_name[i][0]
            text_sim = code_text_name[i][1]
            work_name = code_text_name[i][2]
            print(f"Work Name: {work_name}")
            print(f"Code Similarity: {code_sim}\t Text Similarity: {text_sim}\n")


@check_error
def dialog():
    """
    This function is to start a dialogue with a user
    """
    sg.theme('DarkTeal9')

    # ------ Menu Definition ------ #
    menu_def = [['&Help', '&About...'], ]

    layout = [
        [sg.Menu(menu_def, tearoff=True)],
        [sg.Frame(layout=[
            [sg.Radio('code', default=True, key='code', group_id='sp'),
             sg.Radio('text', key='text', group_id='sp'),
             sg.Text('sort parameter', font='Helvetica 12', tooltip='Choose by which parameter to sort'),
             ],
            [sg.Slider(range=(1, 10), orientation='h', default_value=4,
                       font='Helvetica 12', key='shingle', tooltip='Set shingles length'),
             sg.Text('shingles length', font='Helvetica 12')],
            [sg.Slider(range=(1, 10), orientation='h', default_value=3,
                       font='Helvetica 12', key='k'),
             sg.Text('length of substring', font='Helvetica 12')],
            [sg.Slider(range=(1, 10), orientation='h', default_value=5,
                       font='Helvetica 12', key='t'),
             sg.Text('guarantee threshold', font='Helvetica 12')]],
            title='Options', relief=sg.RELIEF_SUNKEN,
            tooltip='Use these to customize the comparison')],
        [sg.Text('Current Homework'), sg.InputText('File Link', key='link'),
         sg.FileBrowse()],
        [sg.Output(size=(50, 20))],
        [sg.Submit(tooltip='Click to submit this form'), sg.Cancel(tooltip='Click to stop working'),
         sg.Button(button_text="Get ID", tooltip='Click to get IDs from the drive')]]

    window = sg.Window('Finding Clones', layout, default_element_size=(40, 1))

    # Event Loop
    while True:
        event, values = window.read()
        if event in (None, 'Exit', 'Cancel'):
            break
        if event == 'About...':
            print("About plagiarism, you can read this:")
            print("https://en.wikipedia.org/wiki/Plagiarism")
            print("\n")
            print("About shingle algorithm, you can read this:")
            print("http://rcdl2007.pereslavl.ru/papers/paper_65_v1.pdf")
            print("\n")
            print("About hash functions, you can read this:")
            print("https://en.wikipedia.org/wiki/Hash_function")
            print("\n")
            print("About fingerprinting, you can read this:")
            print("https://www.researchgate.net/publication/2840981_Winnowing_Local_Algorithms_for_Document_Fingerprinting")
            print("\n")

        if event == 'Submit':
            if not (values['code'] or values['text']):
                print('You should choose the sort parameter')
            if values['code']:
                compare(link=values['link'], k=int(values['k']), t=int(values['t']),
                        shingle_length=int(values['shingle']), sort_parameter=0)
            elif values['text']:
                compare(link=values['link'], k=int(values['k']), t=int(values['t']),
                        shingle_length=int(values['shingle']), sort_parameter=1)
        if event == 'Get ID':
            get_id.get_id()
    window.close()


if __name__ == '__main__':
    dialog()
