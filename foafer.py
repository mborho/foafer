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
import os
import re
import logging
import wsgiref.handlers
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from mako.template import Template
from mako.lookup import TemplateLookup
from rdf.TriplePicker import Foafer
from rdf import http

logging.getLogger().setLevel(logging.DEBUG)

TEMPLATE_PATH = os.path.dirname(__file__)+'/templates/'
mylookup = TemplateLookup(directories=[TEMPLATE_PATH], input_encoding='utf-8', output_encoding='utf-8', encoding_errors='replace',default_filters=['decode.utf8'])
    
def getRssContainer(target, source_type=''):
        div_id = re.sub('[^\w]','_',target)
        ajax_div = ' <a href="" onclick="try {getRSS(\'%s\',\'%s\',\'auto\');} catch(e) {};return false;" id="link_%s" title="click for latest entries">' % (div_id, target, div_id)
        ajax_div += '<script type="text/javascript">showInfoIcon();</script></a>'
        ajax_div += '<div class="api_target" id="'+div_id+'"></div>'
        return ajax_div
    
class MainPage(webapp.RequestHandler):
    def get(self):
        foafer = None
        rdf = None
        uri = self.request.get('file','start')
        output = ''
        errors = []
        
        if uri.startswith('http://'):            
            net = http.http(uri=uri)
            rdf = net.load()
            if rdf is None:
                if net.detected and not self.request.get('detected'):
                    self.redirect('/?file=%s&detected=1' % net.detected)
                errors = net.errors                            
        elif self.request.get('file') == 'supports':
            self.redirect("/supports")
                        
        if(uri is not None and rdf is not None):
            foafer = Foafer(uri,rdf)
            foafer.build()
            if len(foafer.errors) > 0:
                errors = foafer.errors
                        
        if len(errors) == 0:
            try:
                mytemplate = mylookup.get_template("index.tmpl")        
                output = mytemplate.render(foafer=foafer,rdfuri=uri,getRssContainer=getRssContainer)            
            except:
                logging.error("rendering failed: %s" % uri)
                errors.append('Problems with foaf file')
                
        if len(errors) > 0:
            mytemplate = mylookup.get_template("error.tmpl")        
            output = mytemplate.render(errors = errors,rdfuri=uri)

        self.response.out.write(output)            

            
class DataApi(webapp.RequestHandler):
    def get(self):        
        urls = self.request.get('url', allow_multiple=True)
        output = ''
        
        if len(urls) > 0:
            mode = self.request.get('mode')
            from tools import feedmerger
            output = feedmerger.getData(urls,mode)
            if mode == "mix": content_type = 'text/xml'
            else: content_type = 'text/plain'
                
        self.response.headers['Content-Type'] = '%s charset=utf-8' % content_type
        self.response.out.write(output)
            
class Supports(webapp.RequestHandler):
    def get(self):            
        mytemplate = mylookup.get_template("supports.tmpl")        
        output = mytemplate.render()
        self.response.out.write(output)
        
def main():
    application = webapp.WSGIApplication(
                                        [('/', MainPage),
                                        ('/api',DataApi),
                                        ('/supports',Supports)],
                                        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()
