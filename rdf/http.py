#!/usr/bin/python
# -*- coding: utf-8 -*-
# 
# FOAFer
# Copyright (C) 2003, 2010, Martin Borho <martin@borho.net>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import re
from google.appengine.api import urlfetch

class http(object):

    def __init__(self,uri=None):
        self.user_agent = 'FOAFer.org'
        self.detected = None       
        self.uri = uri
        self.errors = []
        pass

    def load(self,uri=None):
        rdf = None

        if uri is not None:
            self.uri = uri

        if self.uri:
            self.uri =  re.sub(r'#.*$','',self.uri)
            try:
                headers = {'Cache-Control' : 'max-age=10','User-Agent': self.user_agent}
                result = urlfetch.fetch(self.uri, headers = headers)#,'Accept':'application/rdf+xml'})
                if result.status_code in [200,302,301]:
                    rdf = result.content             
                    if not self.checkRDF(rdf):
                        self.errors.append('No Foaf-File found.')
                        return None
                elif result.status_code in [404]:
                    self.errors.append('Response Code 404 - Document Not Found.')
                else:
                    self.errors.append('File was not found.')
                    self.errors.append('Return Code: %d' % xml['status'])
            except urlfetch.InvalidURLError,e:                    
                    self.errors.append("Invalid URL, only http and https is supported")
            except urlfetch.DownloadError,e:
                    self.errors.append(unicode(e))          
            except urlfetch.ResponseTooLargeError,e:                    
                    self.errors.append("The response data exceeded the maximum allowed size.")
            except Exception, e:
                self.errors.append('%s: %s' % (e.__class__.__name__, e))
        else:
            self.errors.append('no uri given')
        return rdf

    def checkRDF(self,rdf):
        rdf = re.sub(r'\s',' ', rdf)
        pat = re.compile('<html.*<head',re.I)
        if not pat.search(rdf) and re.search(r'http://xmlns.com/foaf/',rdf):
            return True
        else:
            self.checkLink(rdf)
            return False
    
    def checkLink(self, string):
        pat = re.compile(r'<link[^>]*rel=\"meta\"[^>]*>',re.I)
        links = pat.findall(string)
        links = [l for l in links if re.search(r'foaf',l,re.I) is not None]
        if len(links) > 0:
            pat = re.compile(r'href="([^"]*)"',re.I)
            foaf = pat.findall(links[0])
            if foaf and foaf[0].startswith('http'):
                self.detected = foaf[0]
            return True
        else:
            return False
