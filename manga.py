import base64
import json
import os
import urllib2
import glob
import time

from bs4 import BeautifulSoup


class Mangas(object):
    def __init__(self, mangas):
        self.mangas = mangas

    def find_manga(self, name):
        manga_list = []
        for manga_name in self.mangas.keys():
            if name.lower() in manga_name.lower():
                manga_list.append(manga_name)

        return manga_list

    def get_manga(self, name):
        return Manga(name, self.mangas[name])

    def get_manga_b64(self, b64_name):
        name = base64.urlsafe_b64decode(b64_name)
        return Manga(name, self.mangas[name])


class Manga(object):
    def __init__(self, name, url):
        self.name = name
        self.b64name = base64.urlsafe_b64encode(name)
        self.url = url
        self.manga_path = os.path.join('media', 'download', self.name)
        self.chapters_path = os.path.join(self.manga_path, 'chapters.json')

    def get_chapters(self):
        chapters = []
        with open(self.chapters_path) as f:
            chapters = json.load(f)
        return chapters

    def update(self):
        try:
            os.stat(self.manga_path)
        except OSError:
            os.mkdir(self.manga_path)

        print 'retrieving chapter list...'
        chapters = []
        html = fetch_html(self.url)
        soup = BeautifulSoup(html)
        ul = soup.select('.detail_list > ul')
        for link in ul[0].find_all('a'):
            name = link.get_text().strip()
            url = link.get('href')
            chapters.append((name, url))

        chapters.reverse()

        with open(self.chapters_path, 'w') as f:
            json.dump(chapters, f)

        print 'there are %d chapter' % len(chapters)

    def total_chapters(self):
        with open(self.chapters_path) as f:
            chapters = json.load(f)

        return len(chapters)

    def total_pages(self, chapter):
        chapter_path = os.path.join(self.manga_path, str(chapter))
        file_list = []
        for item in os.listdir(chapter_path):
            if os.path.isfile(os.path.join(chapter_path, item)):
                file_list.append(item)
        return len(file_list)

    def get_pages(self, chapter):
        chapter_path = os.path.join(self.manga_path, str(chapter))
        file_list = []
        for item in os.listdir(chapter_path):
            if os.path.isfile(os.path.join(chapter_path, item)):
                file_list.append('%s/%d/%s' % (self.name, chapter, item))
        file_list.sort()
        return file_list

    def download_chapter(self, chapter, skip_downloaded=False):
        with open(self.chapters_path) as f:
            chapters = json.load(f)

        name = chapters[chapter][0]
        url = chapters[chapter][1]

        if skip_downloaded:
            chapter_path = os.path.join(self.manga_path, str(chapter))
            try:
                os.stat(chapter_path)
                # already downloaded, skip it
                print 'skipping chapter %d' % chapter
                return
            except OSError:
                # not downloaded yet
                pass

        print 'retrieving page list for chaper %d ...' % chapter
        page_list = []
        html = fetch_html(url)
        soup = BeautifulSoup(html)
        sel = soup.select('.wid60')
        options = sel[0].select('option')
        for option in options:
            page_list.append(option.get('value'))

        print 'downloading images'
        chapter_path = os.path.join(self.manga_path, str(chapter))
        try:
            os.stat(chapter_path)
        except OSError:
            os.mkdir(chapter_path)

        print 'pages:', len(page_list)
        existing_pages = glob.glob(os.path.join(chapter_path, '*.*'))
        last_page = len(existing_pages)

        for i, page in enumerate(page_list):
            if i < last_page:
                print 'skipping page', i
                continue
            html = fetch_html(page)
            soup = BeautifulSoup(html)
            imgs = soup.select('#viewer img')
            img_url = imgs[0].get('src')
            filename = '%03d_%s' % (i, os.path.split(img_url)[1])
            img_path = os.path.join(chapter_path, filename)
            
            print 'downloading', img_path
            try:
                data = fetch_html(img_url)
                with open(img_path, 'wb') as f:
                    f.write(data)
            except urllib2.HTTPError, e:
                print 'download failed: %s' % e
        print 'DONE!'


def fetch_html(url):
    for i in range(12):
        try:
            print 'fetching', url, '...'
            f = urllib2.urlopen(url)
            return f.read()
        except urllib2.URLError, e:
            print 'fetch failed! retrying...'
            time.sleep(1)
    raise e


def get_mangas(html):
    soup = BeautifulSoup(html)

    manga = {}

    for link in soup.find_all('a'):
        if 'manga_info' in link.get('class', []):
            name = link.get_text().strip()
            url = link.get('href')
            manga[name] = url

    return manga


def update_manga_list():
    '''Update manga database'''
    data = fetch_html('http://www.mangahere.com/mangalist/')
    
    print 'parsing data...'
    mangas = get_mangas(data)

    with open('media/download/manga-list.json', 'w') as f:
        json.dump(mangas, f)

    print 'DONE!'


def load_mangas():
    '''Load manga list from database'''
    with open('media/download/manga-list.json') as f:
        data = json.load(f)

    return Mangas(data)


def load_soup(path):
    with open(path) as f:
        data = f.read()

    return BeautifulSoup(data)


def download_chapter(name, chapter, db_update=False):
    m = load_mangas()
    mg = m.get_manga(name)
    if db_update:
        mg.update()
    mg.download_chapter(chapter)


def download(name, start=0, db_update=True):
    m = load_mangas()
    mg = m.get_manga(name)
    if db_update:
        mg.update()

    for chapter in xrange(mg.total_chapters()):
        if chapter < start:
            print 'skipping chapter', chapter
            continue
        mg.download_chapter(chapter, True)

def get_dowloaded_manga():
    dir_list = []
    for item in os.listdir('media/download/'):
        if os.path.isdir(os.path.join('media/download', item)):
            dir_list.append(item)

    dir_list = sorted(dir_list)

    m = load_mangas()
    manga_list = []
    for manga_name in dir_list:
        try:
            mg = m.get_manga(manga_name)
            manga_list.append(mg)
        except KeyError:
            pass

    return manga_list

def get_manga(name):
    m = load_mangas()
    return m.get_manga(name)

def find_manga(name):
    m = load_mangas()
    return m.find_manga(name)
    
def update_all():
    manga_list = get_dowloaded_manga()

    for manga in manga_list:
        download(manga.name)
