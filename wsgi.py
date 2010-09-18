import logging
import wsgiref.handlers
from google.appengine.ext import webapp
from foafer import Foafer                       
logging.getLogger().setLevel(logging.DEBUG)

class MainPage(webapp.RequestHandler):
    def get(self): 
        foafer = Foafer('http://borho.net/mborho-foaf.rdf')
        out = ''
        about = foafer.about()
        out += "About %s<br/>" % about['name']
        for row in foafer.knows():
            out += '%s knows %s ' % (about['name'], row['name'])
            if row['nick']:
                out += ' / %s ' % row['nick']
            if row['homepage']:
                out += '(%s)' % row['homepage']
            if row['weblog']:
                out += '(%s)' % row['weblog']
            if row['seeAlso']:
                out += '--> %s' % row['seeAlso']                
            out += "<br/>"
        self.response.out.write(out)            
        
def main():
    application = webapp.WSGIApplication(
                                        [('/', MainPage),],
                                        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()
