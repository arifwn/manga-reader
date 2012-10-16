#!/usr/bin/env python

import os

import tornado.ioloop
import tornado.web

import manga


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        manga_list = manga.get_dowloaded_manga()

        def last_view_func(name):
            url = self.get_secure_cookie(name.replace(' ', '-'))
            if url is None:
                url = '/manga?name=%s&chapter=0&page=0' % name
            return url

        self.render('./templates/index.html', manga_list=manga_list, last_view=last_view_func)


class MangaHandler(tornado.web.RequestHandler):
    def get(self):
        name = self.get_argument('name')
        chapter = int(self.get_argument('chapter', '0'))
        page = int(self.get_argument('page', '0'))
        m = manga.get_manga(name)
        pages = m.get_pages(chapter)
        total_pages = m.total_pages(chapter)

        last_page_url = '/manga?name=%s&chapter=%d&page=%d' % (name, chapter, page)
        self.set_secure_cookie(name.replace(' ', '-'), last_page_url)

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
                    page_image=self.static_url(pages[page]),
                    next_page_url=next_page_url,
                    prev_page_url=prev_page_url)

settings = {
    'cookie_secret': '61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=',
    'login_url': '/login',
    'xsrf_cookies': True,
    'static_path': os.path.join(os.path.dirname(__file__), 'download'),
    'debug': True,
}

if __name__ == '__main__':
    application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/manga', MangaHandler),
    ], **settings)
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    
