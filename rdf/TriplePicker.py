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
import logging
import StringIO
from rdflib.Graph import Graph

logging.getLogger().setLevel(logging.DEBUG)

RDFS = 'http://www.w3.org/2000/01/rdf-schema#'
FOAF = 'http://xmlns.com/foaf/0.1/'
DC = 'http://purl.org/dc/elements/1.1/'

class Relations(object):

    def __init__(self,ns):
        self.ns = ns
        self.labels = {
                'friendof':'friend of',
                'closefriendof':'close friend of',
                'workswith':'works with',
                'collaborateswith':'collaborateswith',
                'hasmet':'has met',
                'knowsof':'knows of',
                'knowsinpassing':'knows in passing',
                'colleagueof':'colleague of',
                'childof':'child of',
                'liveswith':'lives with',
                'lifepartnerof':'life partner of',
                'siblingof':'sibling of',
                'spouseof':'spouse of',
                'siblingof':'sibling of',
                'acquaintanceof':'acquaintance of',
                'ambivalentof':'ambivalent of',
                'ancestorof':'ancestor of',
                'antagonistof':'antagonist of',
                'apprenticeto':'apprentice to',
                'descendantof':'descendant of',
                'employedby':'employed by',
                'employerof':'employer of',
                'enemyof':'enemy of',
                'engagedto':'engaged to',
                'grandchildof':'grandchild of',
                'grandparentof':'grandparent of',
                'knowsbyreputation':'knows by reputation',
                'lostcontactwith':'lost contact with',
                'mentorof':'mentor of',
                'neighborof':'neighbour of',
                'parentof':'parent of',
                'participant':'participant',
                'participantin':'participant in',
                'wouldliketoknow':'would like to know',
             }

    def getLabel(self, uri):
        prop = uri.replace('<'+self.ns,'')[:-1].lower()
        if self.labels.has_key(prop):
            return self.labels[prop]
        else:
            return ''

class DataObj(object):
    def __init__(self, dataStr):
        if len(dataStr) > 0:  
            self.dataStr = dataStr
        else:
            self.dataStr = ''
        self.string = None

    def __str__(self):
        if not self.string:
            m =  re.match(r'"([^"]*)', self.dataStr)
            if m: string = m.group()
            self.string = string[1:]
        return self.string.decode('unicode_escape').encode('utf-8')

class TriplePicker(object):

    def __init__(self,uri,rdf):

        self.triples = []
        self.dict    = {}
        self.about = None
        self.uri = uri
        self.errors = []
        try:
            g = Graph()
            g.parse(StringIO.StringIO(rdf))
            n3 = g.serialize(format="nt")
        except:
            self.errors.append("Error while parsing.")
            return None
        try:
            self.buildTriples(n3)
            if self.triples:
                self.buildDict()
        except Exception, e:
            logging.error("%s" % (uri))
            logging.error('%s: %s' % (e.__class__.__name__, e))
            self.errors.append("An error occured")
        self.knows_bname = []

    def buildTriples(self,n3):
        triples = []
        for triple in  n3.split('.\n'):
                lastChar = None
                triplePart= []
                part = []
                for char in triple:
                    if lastChar == " " and re.match('[\"\<\.\_]',char):
                            triplePart.append("".join(part[:-1]))
                            part = []
                    part.append(char)
                    lastChar = char
                if triplePart:
                        triplePart.append("".join(part))
                        triples.append(triplePart[0:3])
        self.triples = triples

    def find(self, cond,multi=True):
        result = []
        pattern = []
        if cond['s']: pattern.append(cond['s'])
        if cond['p']: pattern.append(cond['p'])
        if cond['o']: pattern.append(cond['o'])

        for triple in self.triples:
            ref = []
            if cond['s']: ref.append(triple[0])
            if cond['p']: ref.append(triple[1])
            if cond['o']: ref.append(triple[2])

            if pattern == ref:
                if not multi:
                    result = triple
                    break
                else:
                    result.append(triple)
        if result:
            return result

    def buildDict(self):
        for triple in self.triples:
            if len(triple) != 3:
                continue
            #print '###\n'
            #print triple
            #print '###\n'
            if not self.dict.has_key(triple[0]):
                if not self.about:
                    self.about = triple[0]
                    #self.dict[triple[0]] = [triple[1:]]
                self.dict[triple[0]] = {triple[1]:[triple[2]]}
                #self.dict[triple[0]][triple[1][] = [triple[2]]
            else:
                if self.dict[triple[0]].has_key(triple[1]):
                    self.dict[triple[0]][triple[1]].append(triple[2])
                else:
                    if triple[2] == '"': triple[2] = '""' #beware of empty elements
                    self.dict[triple[0]][triple[1]] = [triple[2]]

        for s  in self.dict:
            subjects = self.dict[s]
            for p in subjects:
                try:
                    for o in subjects[p]:
                        index = subjects[p].index(o)
                        self.dict[s][p][index]  = self.getRef(o)
                except:
                    pass

    def getRef(self, obj):
        #if type(obj) is 'list': obj = obj[0]
        ref = obj
        if obj[0] == "<" or obj[0:2] == "_:":
            if self.dict.has_key(obj):
                ref = {obj:self.dict[obj]}
                for k in  self.dict[obj]:
                    ref[obj][k] = self.getRef(self.dict[obj][k])
        elif obj[0] == '"' or obj[-1] == '"':
            ref = DataObj(obj)
        return ref

    def buildURI(self, bName):
        uri = bName
        if self.dict.has_key(bName):
            return self.cleanURI(bName)
        elif type(bName) is unicode:
            if uri.startswith('_:'):
                uri = uri.replace('_:',self.uri+'#')
            return uri

    def cleanURI(self,uri):
        #if type(uri) is unicode and uri[0:1] == "<":
            #return str(uri)[1:-1]
        typeOf = type(uri)
        if typeOf is str and uri[0:1] == "<":
            return str(uri)[1:-1]
        elif typeOf is unicode and uri[0:1] == "<":
            return str(uri)[1:-1]
        else:
            return uri

    def get(self, property, dict):
        val = dict.get('<'+property+'>',[None])[0]
        return val

    def getMulti(self, property, dict):

        multi = dict.get('<'+property+'>',[None])
        return multi

    def search(self, ns, dict):
        result = {}
        for i in [s for s in dict if s.startswith('<'+ns)]:
            result[i] = dict[i]
        return result

class Foafer(TriplePicker):

    def __init__(self,uri,rdf):
        TriplePicker.__init__(self, uri, rdf)
        self.ns_rdfs  = 'http://www.w3.org/2000/01/rdf-schema#'
        self.ns_lang  = 'http://purl.org/net/inkel/rdf/schemas/lang/1.1#'
        self.ns_foaf  = 'http://xmlns.com/foaf/0.1/'
        self.ns_doap  = 'http://usefulinc.com/ns/doap#'
        self.ns_dc    = 'http://purl.org/dc/elements/1.1/'
        self.ns_wgs84 = 'http://www.w3.org/2003/01/geo/wgs84_pos#'
        self.ns_geo   = 'http://www.perceive.net/schemas/geo'
        #self.ns_rel   = 'http://purl.org/vocab/relationship/'

    def setNs(self):
        ns =  'http://xmlns.com/foaf/0.1/'
        ns_checked = None
        while not ns_checked:
            for g in self.graph:
                if g.startswith('<http://xmlns.com/foaf/spec'):
                    ns = 'http://xmlns.com/foaf/spec/'
                    ns_checked = True
                elif g.startswith('<http://xmlns.com/foaf/0.1/'):
                    ns = 'http://xmlns.com/foaf/0.1/'
                    ns_checked = True
                elif g.startswith('<http://xmlns.com/foaf/'):
                    ns = 'http://xmlns.com/foaf/'
                    ns_checked = True
        self.ns_foaf = ns

    def setRelNs(self):
        namespaces = ['http://www.perceive.net/schemas/20021119/relationship/relationship.rdf#','http://purl.org/vocab/relationship/rel-vocab-20040308.rdf#']
        for n in namespaces:
            for g in self.graph:
                if g.startswith('<'+n):
                    self.ns_rel = n
                    return self.ns_rel

        self.ns_rel = 'http://purl.org/vocab/relationship/'
        return self.ns_rel

    def build(self):
        if self.errors:
            return None
        self.graph = None

        about = None
        while True:
            a = self.guessOwner()
            if a:
                self.about = a
                break

            a = self.find({'s':None,'p':"<"+FOAF+"primaryTopic>",'o':None},False)
            if a:
                self.about = a[2]
                break

            a = self.find({'s':None,'p':"<"+FOAF+"topic>",'o':None},False)
            if a:
                self.about = a[2]
                break

            a = self.find({'s':None,'p':"<"+FOAF+"currentProject>",'o':None},False)
            if a:
                self.about = a[0]
                break

            a = self.find({'s':None,'p':"<"+FOAF+"holdsAccount>",'o':None},False)
            if a:
                self.about = a[0]
                break

            a = self.find({'s':None,'p':"<"+FOAF+"myersBriggs>",'o':None},False)
            if a:
                self.about = a[0]
                break
                
            a = self.find({'s':None,'p':"<"+FOAF+"depiction>",'o':None},False)
            if a:
                self.about = a[0]
                break                
            break            
        #for t in self.triples:print t
        self.graph = self.dict[self.about]
        self.setNs()
        self.setRelNs()
        self.buildContainers()

    def guessOwner(self):
        owner = None
        countings = {}
        for t in self.triples:
            if countings.has_key(t[0]):
                countings[t[0]] += 1
            else:
                countings[t[0]] = 1

        items = [(v, k) for k, v in countings.items()]
        items.sort()
        items.reverse()             # so largest is first
        countings = [(k, v) for v, k in items]
        triples_len = len(self.triples)
        if len(countings) > 1:
            factor1 = triples_len/float(countings[0][1])
            factor2 = triples_len/float(countings[1][1])
            if (factor2/factor1) > 2:
                return countings[0][0]
        else:
            return countings[0][0]
        return None

    def buildContainers(self):
        #get data
        foaf = self.ns_foaf

        self.mbox_sum = self.getSimpleMultiples('mbox_sha1sum')#self.get(foaf+'mbox_sha1sum',self.graph)
        self.nick = self.getSimpleMultiples('nick')#self.get(foaf+'nick',self.graph)
        self.name = self.get(foaf+'name',self.graph)
        self.firstname = self.get(foaf+'firstName',self.graph)
        self.surname = self.get(foaf+'surname',self.graph)
        self.givenname = self.get(foaf+'givenname',self.graph)
        self.family_name = self.get(foaf+'family_name',self.graph)
        self.weblogs = self.getResource('weblog',self.graph)
        self.homepages = self.getResource('homepage',self.graph)
        self.workplaces = self.getResource('workplaceHomepage',self.graph)
        self.workinfos = self.getResource('workInfoHomepage',self.graph)
        self.schoolpages = self.getResource('schoolHomepage',self.graph)
        self.messengers = self.getMessengers(['jabberID','icqChatID','yahooChatID','msnChatID','aimChatID'])
        self.geekcode = self.get(foaf+'geekcode',self.graph)
        self.myers = self.get(foaf+'myersBriggs',self.graph)
        self.plan = self.get(foaf+'plan',self.graph)
        self.openids = self.getOpenIds('openid')
        self.accounts = self.getAccounts('holdsAccount')
        self.basedNear = self.getBasedNear([self.ns_foaf+'based_near',self.ns_geo+'location'])
        self.langs = self.getLangs(['masters','speaks','reads','writes'])
        self.depiction = self.getDepiction('depiction')
        self.interests = self.getInterests('interest')
        self.made = self.getMade('made')
        self.knows = self.getKnows('knows',self.graph)
        self.currentProjects = self.getProjects('currentProject')
        self.pastProjects = self.getProjects('pastProject')
        #self.projects = self.getDoapProjects('Project')
        self.maintains = self.maintains('maintainer-of')
        if self.knows:self.relations = self.getRelations(self.ns_rel, self.graph)
        else: self.relations = None


    def getResource(self, name, g):
        result = []
        data = self.getMulti(self.ns_foaf+name, g)
        if data[0]:
            for resource in data:
                if type(resource) is dict:
                    for x in resource.iterkeys():
                        r = {}
                        r['data'] = resource
                        r['uri'] = self.cleanURI(x)
                        r['label'] = self.get(RDFS+'label',resource[x])
                        r['title'] = self.get(DC+'title',resource[x])
                        r['desc'] = self.get(DC+'description',resource[x])
                        r['seeAlso'] = self.get(RDFS+'seeAlso',resource[x])
                        seeAlso = self.get(self.ns_rdfs+'seeAlso',resource[x])
                        if seeAlso:
                            try:r['seeAlso'] = self.cleanURI(seeAlso.keys()[0])
                            except:pass
                        result.append(r)
                elif resource:
                    r = {}
                    r['data'] = resource
                    r['uri'] = self.cleanURI(resource)
                    result.append(r)
        return result

    def getKnows(self, prop,g):
        result = []
        data = self.getMulti(self.ns_foaf+prop, g)
        if data[0]:
            for resource in data:
                if type(resource) is dict:
                    for x in resource.iterkeys():
                        r = {}
                        r['uri'] = self.cleanURI(x)
                        self.knows_bname.append(r['uri'])
                        r['mbox_sum'] = self.get(self.ns_foaf+'mbox_sha1sum',resource[x])
                        r['nick'] = self.get(self.ns_foaf+'nick',resource[x])
                        r['name'] = self.get(self.ns_foaf+'name',resource[x])
                        r['firstname'] = self.get(self.ns_foaf+'firstName',resource[x])
                        r['surname'] = self.get(self.ns_foaf+'surname',resource[x])
                        r['givenname'] = self.get(self.ns_foaf+'givenname',resource[x])
                        r['family_name'] = self.get(self.ns_foaf+'family_name',resource[x])
                        r['weblogs'] = self.getResource('weblog',resource[x])
                        r['homepage'] = self.getResource('homepage',resource[x])
                        r['workHomepage'] = self.getResource('workHomepage',resource[x])
                        r['schoolpage'] = self.getResource('schoolHomepage',resource[x])
                        r['accounts'] = self.getAccounts('holdsAccount', resource[x])
                        #self.workinfos = self.getResource('workInfoHomepage')
                        #self.schoolpages = self.getResource('schoolHomepage')
                        seeAlso = self.get(self.ns_rdfs+'seeAlso',resource[x])
                        if seeAlso:
                            typeStr = type(seeAlso)
                            if  typeStr is str:
                                r['seeAlso'] = self.cleanURI(seeAlso)
                            elif typeStr is dict:
                                seeRef = seeAlso.keys()[0]
                                ref = seeRef
                                if seeRef.startswith('_:r'):
                                    if seeAlso[seeRef].has_key('<'+RDFS+'about>'):
                                        refAbout= seeAlso[seeRef]['<'+RDFS+'about>']
                                        ref = str(refAbout[0])
                                    elif seeAlso[seeRef].has_key('<'+RDFS+'resource>'):
                                        refAbout= seeAlso[seeRef]['<'+RDFS+'resource>']
                                        ref = str(refAbout[0])
                                try:
                                    if re.match(r'^[\<]?http:', ref):
                                        r['seeAlso'] = self.cleanURI(ref)
                                except:
                                    pass
                        result.append(r)
                elif resource:
                    if type(resource) is str and not resource.startswith('<%s' % self.uri):
                        # empty nodes-ids
                        r = {}
                        r['uri'] = self.cleanURI(resource)
                        r['seeAlso'] = self.cleanURI(resource)
                        self.knows_bname.append(r['uri'])
                        result.append(r)
        return result

    def getProjects(self, prop):
        result = []
        data = self.getMulti(self.ns_foaf+prop,self.graph)
        if data[0]:
            for resource in data:
                if type(resource) is dict:
                    for x in resource.iterkeys():
                        r = {}
                        uri = self.cleanURI(x)
                        if uri.startswith('http'): r['uri'] = uri
                        else: r['uri'] = None
                        r['label'] = self.get(self.ns_rdfs+'label',resource[x])
                        r['title'] = self.get(self.ns_dc+'title',resource[x])
                        r['desc'] = self.get(self.ns_dc+'description',resource[x])
                        if not r['desc']:
                            r['desc'] = self.get(self.ns_doap+'description',resource[x])
                        if not r['desc']:
                            r['desc'] = self.get(self.ns_doap+'shortdesc',resource[x])
                        r['name'] = self.get(self.ns_foaf+'name',resource[x])
                        r['doapname'] = self.get(self.ns_doap+'name',resource[x])
                        homepage = self.get(self.ns_foaf+'homepage',resource[x])
                        if homepage:
                            r['homepage'] = self.cleanURI(homepage)
                        doappage = self.get(self.ns_doap+'homepage',resource[x])
                        if type(doappage) is unicode and doappage.startswith('<http:'):
                            r['doappage'] = self.cleanURI(doappage)
                        r['seeAlso'] = self.get(RDFS+'seeAlso',resource[x])
                        seeAlso = self.get(self.ns_rdfs+'seeAlso',resource[x])
                        if seeAlso:
                            try:r['seeAlso'] = self.cleanURI(seeAlso.keys()[0])
                            except: pass
                        result.append(r)
                elif resource:
                    r = {}
                    r['data'] = resource
                    r['uri'] = self.cleanURI(resource)
                    result.append(r)
        return result

    #def getDoapProjects(self, prop):
        #result = []
        #data = self.getMulti(self.ns_doap+prop,self.graph)
        #if data[0]:
            #for resource in data:
                #if type(resource) is dict:
                    #for x in resource.iterkeys():
                        #r = {}
                        #uri = self.cleanURI(x)
                        #if uri.startswith('http'): r['uri'] = uri
                        #else: r['uri'] = None
                        #r['label'] = self.get(self.ns_rdfs+'label',resource[x])
                        #r['title'] = self.get(self.ns_dc+'title',resource[x])
                        #r['desc'] = self.get(self.ns_doap+'description',resource[x])
                        #if not r['desc']:
                            #r['desc'] = self.get(self.ns_dc+'description',resource[x])
                        #r['name'] = self.get(self.ns_doap+'name',resource[x])
                        #homepage = self.get(self.ns_doap+'homepage',resource[x])
                        #if type(homepage)is dict:
                            #hp_uri = homepage.keys()[0]
                            #r['homepage'] = self.cleanURI(hp_uri)
                            #r['homepage_title'] = self.get(self.ns_dc+'title',homepage[hp_uri])
                        #r['seeAlso'] = self.get(RDFS+'seeAlso',resource[x])
                        #seeAlso = self.get(self.ns_rdfs+'seeAlso',resource[x])
                        #if seeAlso:
                            #try:r['seeAlso'] = self.cleanURI(seeAlso.keys()[0])
                            #except:pass
                        #result.append(r)
                #elif resource:
                    #r = {}
                    #r['uri'] = self.cleanURI(resource)
                    #result.append(r)
        #return result

    def maintains(self, prop):
        result = []
        data = self.getMulti(self.ns_doap+prop,self.graph)
        if data[0]:
            for resource in data:
                if type(resource) is dict:
                    for x in resource.iterkeys():
                        r = {}
                        uri = self.cleanURI(x)
                        if uri.startswith('http'): r['uri'] = uri
                        else: r['uri'] = None
                        r['label'] = self.get(self.ns_rdfs+'label',resource[x])
                        r['title'] = self.get(self.ns_dc+'title',resource[x])
                        r['desc'] = self.get(self.ns_doap+'description',resource[x])
                        if not r['desc']:
                            r['desc'] = self.get(self.ns_dc+'description',resource[x])
                        r['name'] = self.get(self.ns_doap+'name',resource[x])
                        homepage = self.get(self.ns_doap+'homepage',resource[x])
                        if type(homepage)is dict:
                            hp_uri = homepage.keys()[0]
                            r['homepage'] = self.cleanURI(hp_uri)
                            r['homepage_title'] = self.get(self.ns_dc+'title',homepage[hp_uri])
                        elif homepage.startswith('<http'):
                            r['homepage'] = self.cleanURI(homepage)
                        r['seeAlso'] = self.get(RDFS+'seeAlso',resource[x])
                        seeAlso = self.get(self.ns_rdfs+'seeAlso',resource[x])
                        if seeAlso:
                            try:
                                r['seeAlso'] = self.cleanURI(seeAlso.keys()[0])
                            except:
                                pass
                        result.append(r)
                elif resource:
                    r = {}
                    r['uri'] = self.cleanURI(resource)
                    result.append(r)
        #print result
        return result



    def getInterests(self, prop):
        interests = []
        data = self.getMulti(self.ns_foaf+prop,self.graph)
        if data[0]:
            for resource in data:
                if type(resource) is dict:
                    for x in resource.iterkeys():
                        r = {}
                        uri = self.cleanURI(x)
                        if uri.startswith('http'): r['uri'] = uri
                        else: r['uri'] = None
                        r['label'] = self.get(RDFS+'label',resource[x])
                        r['title'] = self.get(DC+'title',resource[x])
                        r['desc'] = self.get(DC+'description',resource[x])
                        if r['uri'] or r['label'] or r['title']:
                            interests.append(r)
                elif resource:
                    r = {}
                    uri = self.cleanURI(resource)
                    if str(uri).startswith('http'): r['uri'] = uri
                    else: r['title'] = uri
                    interests.append(r)
        return interests

    def getRelations(self, name_ns, g):
        relations = {}
        data = self.search(name_ns,self.graph)
        if len(data)> 0:
            labels = Relations(self.ns_rel)
            for rel in data:
                for r in data[rel]:
                    if type(r) is dict:
                        bname = r.keys()[0]
                        node = r
                        r = self.buildURI(bname)
                        #print r
                        if r not in self.knows_bname:
                            person = {}
                            person['uri'] = r
                            person['mbox_sum'] = self.get(self.ns_foaf+'mbox_sha1sum',node[bname])
                            person['nick'] = self.get(self.ns_foaf+'nick',node[bname])
                            person['name'] = self.get(self.ns_foaf+'name',node[bname])
                            person['firstname'] = self.get(self.ns_foaf+'firstName',node[bname])
                            person['surname'] = self.get(self.ns_foaf+'surname',node[bname])
                            person['givenname'] = self.get(self.ns_foaf+'givenname',node[bname])
                            person['family_name'] = self.get(self.ns_foaf+'family_name',node[bname])
                            person['weblogs'] = self.getResource('weblog',node[bname])
                            person['homepage'] = self.getResource('homepage',node[bname])
                            person['workHomepage'] = self.getResource('workHomepage',node[bname])
                            person['schoolpage'] = self.getResource('schoolHomepage',node[bname])
                            #self.workinfos = self.getResource('workInfoHomepage')
                            #self.schoolpages = self.getResource('schoolHomepage')
                            seeAlso = self.get(self.ns_rdfs+'seeAlso',node[bname])
                            if seeAlso:
                                if type(seeAlso) is unicode:
                                    r['seeAlso'] = self.cleanURI(seeAlso)
                                elif type(seeAlso) is dict:
                                    try:r['seeAlso'] = self.cleanURI(seeAlso.keys()[0])
                                    except:pass
                            self.knows.append(person)
                    else:
                        r = self.buildURI(r)
                    if not r in relations:
                        relations[r] = []
                    relations[r].append({'uri':rel,'label':labels.getLabel(rel)})
        #print self.ns_rel
        #print relations
        #for t in self.triples:print t
        #for p in self.knows:print p
        return relations
        
    def getSimpleMultiples(self, prop):
        results= {}        
        ids = self.getMulti(self.ns_foaf+prop, self.graph)
        if ids[0] and str(ids[0]) != '': results = ids
        return results
        
    def getMessengers(self, props):
        messengers= {}
        for p in props:
            ids = self.getMulti(self.ns_foaf+p, self.graph)
            if ids[0] and str(ids[0]) != '': messengers[p] = ids
        return messengers

    def getOpenIds(self,prop):
        ids = []
        data = self.getMulti(self.ns_foaf+'openid',self.graph)
        if data[0]:
            for openid in data:
                typeOf = type(openid)
                if typeOf is str:
                    ids.append(self.cleanURI(openid))
                elif typeOf is dict:
                    ids.append(self.cleanURI(openid.keys()[0]))
            #ids = map(self.cleanURI,ids)
        return ids

    def getAccounts(self, prop, graph=None):
        accounts = []
        if graph:
            data = self.getMulti(self.ns_foaf+prop ,graph)
        else:
            data = self.getMulti(self.ns_foaf+prop ,self.graph)
        if data[0]:
            for resource in data:
                if type(resource) is dict:
                    for x in resource.iterkeys():
                        r = {}
                        r['name'] = self.get(self.ns_foaf+'accountName', resource[x])
                        r['page'] = self.cleanURI(self.get(self.ns_foaf+'accountProfilePage', resource[x]))
                        ahp = self.cleanURI(self.get(self.ns_foaf+'accountServiceHomepage', resource[x]))
                        if ahp is None:
                            continue

                        typeOf = type(ahp)
                        hp=''
                        if typeOf is dict:
                            #with extra property, extract only account homepage
                            hp = self.cleanURI(ahp.keys()[0])
                            #self.cleanURI(self.get(self.ns_foaf+'accountServiceHomepage', resource[x]))
                        elif typeOf is str:
                            hp = ahp

                        if hp[-1] != "/":
                            hp += "/"
                        r['homepage'] = hp
                        accounts.append(r)
        return accounts

    def getBasedNear(self,props):
        points = []
        for prop in props:
            data = self.getMulti(prop, self.graph)
            if data[0]:
                for resource in data:
                    if type(resource) is dict:
                        for x in resource.iterkeys():
                            r = {}
                            lon = None
                            lat = None
                            if prop.startswith(self.ns_foaf):
                                lat = self.get(self.ns_wgs84+'lat', resource[x])
                                lon = self.get(self.ns_wgs84+'long', resource[x])
                            elif prop.startswith(self.ns_geo):
                                lat = self.get(self.ns_geo+'lat', resource[x])
                                lon = self.get(self.ns_geo+'lon', resource[x])
                            if lat: r['lat'] = lat
                            if lon: r['long'] = lon
                            if len(r) > 0:
                                    points.append(r)
                                    return points
        return points

    def getDepiction(self, prop):
        pics = []
        data = self.getMulti(self.ns_foaf+prop,self.graph)
        if data[0]:
            for resource in data:
                if type(resource) is dict:
                    for x in resource.iterkeys():
                        r = {}
                        r['data'] = resource
                        r['url'] = self.cleanURI(x)
                        r['title'] = self.get(self.ns_dc+'title',resource[x])
                        r['desc'] = self.get(self.ns_dc+'description',resource[x])
                        pics.append(r)
                elif resource:
                    r = {}
                    r['url'] = self.cleanURI(resource)
                    pics.append(r)
        return pics

    def getMade(self, prop):
        made = []
        data = self.getMulti(self.ns_foaf+prop,self.graph)
        if data[0]:
            for resource in data:
                if type(resource) is dict:
                    for x in resource.iterkeys():
                        r = {}
                        r['title'] = self.get(self.ns_dc+'title',resource[x])
                        r['uri'] = self.cleanURI(x)
                        if not r['uri'].startswith('http'):
                            r['uri'] = None
                            if not r['title']:
                                r['title'] = r['uri']
                        r['label'] = self.get(self.ns_rdfs+'label',resource[x])
                        seeAlso = self.get(self.ns_rdfs+'seeAlso',resource[x])
                        if seeAlso:
                            try:
                                r['seeAlso'] = self.cleanURI(seeAlso.keys()[0])
                            except:
                                pass
                        r['desc'] = self.get(self.ns_dc+'description',resource[x])
                        r['type'] = self.get(self.ns_dc+'type',resource[x])
                        r['topic'] = self.get(self.ns_foaf+'Topic',resource[x])
                        if r['uri'] or r['label'] or r['title'] or r['topic']:
                            made.append(r)
                elif resource:
                    r = {}
                    uri = self.cleanURI(resource)
                    if uri.startswith('http'): r['uri'] = uri
                    else: r['title'] = uri
                    made.append(r)
        return made

    def getLangs(self, props):
        langs = {}
        for prop in props:
            l = {}
            val = self.getMulti(self.ns_lang+prop, self.graph)
            if val:
                langs[prop] = []
                [langs[prop].append(str(v)) for v in val if v is not None]
                if not langs[prop]: del langs[prop]
        if len(langs) > 0:
            return langs
        else:
            return None
