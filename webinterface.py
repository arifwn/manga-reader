#!/usr/bin/env python

import os

import tornado.ioloop
import tornado.web

import manga


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        manga_list = manga.get_dowloaded_manga()

        def last_view_func(name):
            cookie_key = name.replace(' ', '-')
            cookie_key = cookie_key.replace('(', '-')
            cookie_key = cookie_key.replace(')', '-')
            url = self.get_secure_cookie(cookie_key)
            if url is None:
                url = '/manga?name=%s&chapter=0&page=0' % name
            return url

        def last_chapter_func(name):
            cookie_key = name.replace(' ', '-')
            cookie_key = cookie_key.replace('(', '-')
            cookie_key = cookie_key.replace(')', '-')
            chapter = self.get_secure_cookie(cookie_key+'-last-chapter')
            if chapter is None:
                chapter = 0
            return int(chapter) + 1

        def total_chapter_func(name):
            m = manga.get_manga(name)
            return len(m.get_chapters())

        def has_update_func(name):
            last_chapter = last_chapter_func(name)
            total_chapter = total_chapter_func(name)
            if total_chapter > last_chapter:
                return True
            else:
                return False

        self.render('./templates/index.html', manga_list=manga_list, 
                    last_view=last_view_func, 
                    last_chapter=last_chapter_func,
                    total_chapter=total_chapter_func,
                    has_update=has_update_func)


class MangaHandler(tornado.web.RequestHandler):
    def get(self):
        name = self.get_argument('name')
        chapter = int(self.get_argument('chapter', '0'))
        page = int(self.get_argument('page', '0'))
        m = manga.get_manga(name)
        pages = m.get_pages(chapter)
        total_pages = m.total_pages(chapter)

        last_page_url = '/manga?name=%s&chapter=%d&page=%d' % (name, chapter, page)
        cookie_key = name.replace(' ', '-')
        cookie_key = cookie_key.replace('(', '-')
        cookie_key = cookie_key.replace(')', '-')
        self.set_secure_cookie(cookie_key, last_page_url, 365)
        self.set_secure_cookie(cookie_key+'-last-chapter', str(chapter), 365)
        self.set_secure_cookie(cookie_key+'-last-page', str(page), 365)

        if (page + 1) >= total_pages:
            _chapter = chapter + 1
            _page = 0
        else:
            _chapter = chapter
            _page = page + 1

        next_page_url = '?name=%s&chapter=%d&page=%d' % (name, _chapter, _page)

        if (page - 1) < 0:
            _chapter = chapter - 1
            if _chapter >= 0:
                _total_pages = m.total_pages(_chapter)
                _page = _total_pages - 1
            else:
                _page = 0
                _chapter = 0
        else:
            _chapter = chapter
            _page = page - 1
            
        prev_page_url = '?name=%s&chapter=%d&page=%d' % (name, _chapter, _page)

        self.render('./templates/view.html',
                    manga=m,
                    chapter=chapter,
                    page=page,
                    page_image=self.static_url('download/'+pages[page]),
                    next_page_url=next_page_url,
                    prev_page_url=prev_page_url)

settings = {
    'cookie_secret': '61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=',
    'login_url': '/login',
    'xsrf_cookies': True,
    'static_path': os.path.join(os.path.dirname(__file__), 'media'),
    'debug': True,
}

if __name__ == '__main__':
    application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/manga', MangaHandler),
    ], **settings)
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    
