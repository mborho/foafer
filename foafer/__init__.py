from rdflib import Graph, Namespace
import rdflib

rdflib.plugin.register('sparql', rdflib.query.Processor,
                       'rdfextras.sparql.processor', 'Processor')
rdflib.plugin.register('sparql', rdflib.query.Result,
                       'rdfextras.sparql.query', 'SPARQLQueryResult')
                       
class Foafer (object):
    
    def __init__(self, uri):
        self.uri = uri
        self.graph = Graph()        
        self.graph.parse(uri)

    def about(self):
        query = self.graph.query('''
                    PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    SELECT ?name ?homepage ?weblog ?nick ?seeAlso 
                    WHERE { 
                        ?subject foaf:knows ?knows .                        
                        OPTIONAL { ?subject foaf:name ?name . }
                        OPTIONAL { ?subject foaf:homepage ?homepage .}
                        OPTIONAL { ?subject foaf:weblog ?weblog . }
                        OPTIONAL { ?subject rdfs:seeAlso ?seeAlso .}. 
                        OPTIONAL { ?subject foaf:nick ?nick . }
                    }''')
                    
        result = {}
        for row in query:  
            result = {'name':row[0],'homepage':row[1],'weblog':row[2], 
                       'nick':row[3],'seeAlso':row[4]}
            
        #print result
        return result
        
    def knows(self):
        query = self.graph.query('''
                    PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    SELECT ?name ?homepage ?weblog ?nick ?seeAlso
                    WHERE { 
                        ?subject foaf:knows ?knows . 
                        OPTIONAL { ?knows foaf:name ?name . }
                        OPTIONAL { ?knows foaf:homepage ?homepage . }
                        OPTIONAL { ?knows foaf:weblog ?weblog . }
                        OPTIONAL { ?knows foaf:nick ?nick . }
                        OPTIONAL { ?knows rdfs:seeAlso ?seeAlso . }
                        } .
                        
                    }''')
        result = []
        for row in query:  
            result.append({'name':row[0],'homepage':row[1],'weblog':row[2], 
                            'nick':row[3], 'seeAlso':row[4]})
        return result
            
        
    
    