import time
import os
import feedparser
import json
import re
import urllib
import logging
from sgmllib import SGMLParser
from google.appengine.api import urlfetch
from google.appengine.api import memcache

logging.getLogger().setLevel(logging.DEBUG)        
    
class Entry(object):
    def __init__(self, data, blog,cached):
        self.blog = blog
        self.title = data.get('title','')
        if data.has_key('modified_parsed'):
            self.date = time.mktime(data.modified_parsed)
        else:
            self.date = time.mktime(cached)
        self.link = data.link
        if data.has_key('description'):
            self.description = data.description
        else:
            self.description = ''
        
    def __cmp__(self, other):
        return other.date - self.date

class Feed(object):
    
    def __init__(self, mode, sources, title='', out_format='rss', num_items=60, cache_name=None,cache_time=300):
        self.mode = mode
        self.sources = sources
        self.title = title
        self.output_format = out_format
        self.postings = []        
        self.num_items = int(num_items)
        self.output = ''
        self.cache_name = cache_name
        self.cache_time = cache_time
        self.xml = None
        self.mime = "text/plain"
        self.link = ''
        self.desc = ''

        # do the action here
        self.buildPostings()
        self.buildFormat()
            
    def buildPostings(self):
        feed_title = []
        for uri in self.sources:
            
            if not self.cache_name: cache_name = uri
            else: cache_name = self.cache_name
            cache_name = cache_name.replace("/", "_")                 
            #self.output += "cache name %s" % str(cache_name)
            
            cache = memcache.get(cache_name)
            if not cache:
                try:
                    logging.info("%s recache" % uri)
                    source = getSource(uri.strip())
                    cache = {}
                    cache['xml'] = feedparser.parse(source)
                    cache['cached'] = time.localtime()
                    if not memcache.add(cache_name, cache, self.cache_time):
                        logging.error("Memcache set failed.")
                except:
                    logging.error("%s failed to fetch" % uri)
                    continue
                    
            xml = cache.get('xml')
            cached = cache.get('cached')
            
            blog = xml.feed.get('title','')
            feed_title.append(blog)
            for e in xml.entries[:30]:
                self.postings.append(Entry(e, blog, cached))

        self.postings.sort()
        if not self.title:
            self.title = " / ".join(feed_title)
        
    def buildFormat(self):
        self.setTitle()
        self.setLink()
        if self.output_format == "rss":
            self.buildRSS()
        elif self.output_format == "json":
            self.buildJSON()

    def setTitle(self):
        if self.mode == 'mix':
            self.desc = 'Latest News from '+self.title
            self.title = 'Merged '+self.title
        elif self.mode == 'delicious':
            self.desc = 'Tagged websites from '+self.title
            self.title = 'Tags merged '+self.title
            
        
    def setLink(self):
        self.link = '?mode='+self.mode
        self.link += '&amp;url='+'&amp;url='.join([urllib.quote_plus(url[:]) for url in self.sources])
        if self.output_format != "rss":
            self.link += '&amp;out='+self.output_format
        
    def buildRSS(self):         
        rss = []
        rss.append('<?xml version="1.0" encoding="UTF-8"?>')
        rss.append('<rss version="0.92" xmlns:dc="http://purl.org/dc/elements/1.1/">')
        rss.append('<channel>')
        rss.append('<title>'+self.title+'</title>')
        rss.append('<link>'+self.link+'</link>')
        rss.append('<description>'+self.desc+'</description>')
        rss.append('<language>en</language>')
        rss.append('<dc:date>'+time.strftime('%Y-%m-%dT%H:%M:%S+02:00')+'</dc:date>')

        for post in self.postings[:self.num_items]:
            date = time.gmtime(post.date)
            date = time.strftime('%Y-%m-%dT%H:%M:%SZ', date)
            item ='<item>\n<link>%s</link>\n<title><![CDATA[%s]]></title>\n<description><![CDATA[%s]]></description>\n<dc:date>%s</dc:date>\n<dc:source>%s</dc:source>\n</item>\n'
            rss.append(item % (post.link.replace("&", "&amp;"), post.title.replace("&", "&amp;"), post.description, date, post.blog))

        rss.append('</channel></rss>')
        self.mime = "text/xml"
        self.output = "\n".join(rss).encode("utf-8")

    def buildJSON(self):
        jsonData = {}
        jsonData['feed'] = {
                    'title':self.title,
                    'link':self.link,
                    'description':self.desc,
                    'language':'en',
                    'dc:date':time.strftime('%Y-%m-%dT%H:%M:%S+02:00')
                    }
        jsonData['entries'] = []

        for post in self.postings[:self.num_items]:
            date = time.gmtime(post.date)
            date = time.strftime('%Y-%m-%dT%H:%M:%SZ', date)
            item = {
                    'link':post.link,
                    'title':post.title,
                    'description':post.description,
                    'dc:date':date,
                    'dc:source':post.blog,
                    }
            jsonData['entries'].append(item)
        self.mime = "application/json"
        self.output = json.write(jsonData)

def getData(urls, mode='auto'):
    source_list = []
    if mode == "auto":
        if len(urls) == 1:
            url = urllib.unquote_plus(urls[0])
            url = re.sub('([^\:])//','\\1/',url)
            rss_link = getRSSLink(url)
            if rss_link:
                source_list.append(rss_link)
                cache_name = url
                feed = Feed(mode=mode, sources=source_list, title="", out_format="json",num_items=5, cache_name=cache_name,cache_time=1800)
                return feed.output  
            else:
                return '{}'          
                
    elif mode == 'mix' and len(urls) > 0:
        feed = Feed(mode=mode, sources=urls, title="", out_format="rss", num_items=15, cache_name=None)        
        return feed.output
        ##for url in urls:
            ##source_list.append(urllib.unquote_plus(url[:]))
    return '' 
        
class LinkParser(SGMLParser):
    def reset(self):
        SGMLParser.reset(self)
        self.href = ''
        
    def do_link(self, attrs):
        if not ('rel', 'alternate') in attrs: return
        if not ('type', 'application/rss+xml') in attrs: return
        hreflist = [e[1] for e in attrs if e[0]=='href']
        if hreflist:
            self.href = hreflist[0]
        self.setnomoretags()
    
    def end_head(self, attrs):
        self.setnomoretags()
    start_body = end_head        
    
def getRSSLink(url):
    html = getSource(url)
    return getRSSLinkFromHTMLSource(html)

def getSource(url):
    html = ''
    try:
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            html = result.content    
    except:
        return html
    return html    

def getRSSLinkFromHTMLSource(htmlSource):
    try:
        parser = LinkParser()
        parser.feed(htmlSource)
        return parser.href
    except:
        return ''    