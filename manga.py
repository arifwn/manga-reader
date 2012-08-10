import json
import os
import urllib2
import glob

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


class Manga(object):
	def __init__(self, name, url):
		self.name = name
		self.url = url
		self.manga_path = os.path.join('download', self.name)
		self.chapters_path = os.path.join(self.manga_path, 'chapters.json')

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

	def download_chapter(self, chapter):
		with open(self.chapters_path) as f:
			chapters = json.load(f)

		name = chapters[chapter][0]
		url = chapters[chapter][1]

		print 'retrieving page list...'
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
			data = fetch_html(img_url)
			with open(img_path, 'wb') as f:
				f.write(data)
		print 'DONE!'


def fetch_html(url):
	print 'fetching', url, '...'
	f = urllib2.urlopen(url)
	return f.read()


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

	with open('download/manga-list.json', 'w') as f:
		json.dump(mangas, f)

	print 'DONE!'


def load_mangas():
	'''Load manga list from database'''
	with open('download/manga-list.json') as f:
		data = json.load(f)

	return Mangas(data)


def load_soup(path):
	with open(path) as f:
		data = f.read()

	return BeautifulSoup(data)


def download_chapter(name, chapter, db_update=False):
	m = load_mangas()
	tor = m.get_manga(name)
	if db_update:
		tor.update()
	tor.download_chapter(chapter)


def download(name, db_update=False):
	m = load_mangas()
	mg = m.get_manga(name)
	if db_update:
		mg.update()

	for chapter in xrange(mg.total_chapters()):
		mg.download_chapter(chapter)
