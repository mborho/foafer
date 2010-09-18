import logging
import os
import wsgiref.handlers
from google.appengine.ext import webapp
from mako.lookup import TemplateLookup
from foafer import Foafer       
import template_helpers
logging.getLogger().setLevel(logging.DEBUG)

TEMPLATE_PATH = os.path.dirname(__file__)+'/templates/'
mylookup = TemplateLookup(directories=[TEMPLATE_PATH], input_encoding='utf-8', output_encoding='utf-8', encoding_errors='replace',default_filters=['decode.utf8'])


class MainPage(webapp.RequestHandler):
    def get(self): 
        uri = 'http://borho.net/mborho-foaf.rdf'
        foafer = Foafer(uri)
        output = ''
        errors = []
        #about = foafer.about()
        #out += "About %s<br/>" % about['name']
        #for row in foafer.knows():
            #out += '%s knows %s ' % (about['name'], row['name'])
            #if row['nick']:
                #out += ' / %s ' % row['nick']
            #if row['homepage']:
                #out += '(%s)' % row['homepage']
            #if row['weblog']:
                #out += '(%s)' % row['weblog']
            #if row['seeAlso']:
                #out += '--> %s' % row['seeAlso']                
            #out += "<br/>"
            
            
                
        mytemplate = mylookup.get_template("index.tmpl")        
        output = mytemplate.render(foafer=foafer,rdfuri=uri,h=template_helpers,request=self.request)                            
        #if len(errors) == 0:
            #try:
                #mytemplate = mylookup.get_template("index.tmpl")        
                #output = mytemplate.render(foafer=foafer,rdfuri=uri,h=template_helpers,request=self.request)            
            #except:
                #logging.error("rendering failed: %s" % uri)
                #errors.append('Problems with foaf file')
                
        #if len(errors) > 0:
            #mytemplate = mylookup.get_template("error.tmpl")        
            #output = mytemplate.render(errors = errors,rdfuri=uri,request=self.request)


        self.response.out.write(output)              
        
def main():
    application = webapp.WSGIApplication(
                                        [('/', MainPage),],
                                        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()
