#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import datetime
import requests
import shelve
import argparse

from pyquery import PyQuery as pq

SEED_URL = "http://skiller.fr/profile/user/142"
DB_USERS_PATH = 'users.shelve'

def infos():
    profiles = shelve.open(DB_USERS_PATH)

    for k, p in profiles.iteritems():
        follows = p['follows']
        print k, len(p['follows'])
        
    cinq_follow = [ (i, len([ p for p in profiles.values() if len(p['follows']) >= i  ] ))
                    for i in range(6)+[10,20,50,100, 200, 500,1000] ] 
    print len(profiles) , " users", cinq_follow
    profiles.close()

def to_padagraph(host, key, gid):
    from reliure.types import Text, Numeric 
    from botapi import Botagraph, BotApiError

    
    bot = Botagraph(host, key)
    
    profiles = shelve.open(DB_USERS_PATH)

    if not bot.has_graph(gid) :
        
        print "\n * Create graph %s" % gid
        attrs = {
            'description':
            """ user dump of a social network
            """.replace("    ", ""),
    
            'image': "",
            'tags': ['social-network']
        }
        bot.create_graph(gid, attrs )
                        
        print "\n * Creating node type %s" % "Profile"
        props = {
                    'label' : Text(),
                    'path' : Text(),
                    'name' : Text(),
                    'url'  : Text(),
                    'score' : Numeric(),
                    'image' : Text(),
                }
        bot.post_nodetype(gid, "Profile",  "Profile ", props)

        print "\n * Creating edge type %s" % "follows"
        props = {
                    'score' : Numeric(),
                }
        bot.post_edgetype(gid, "follows", "follows", props )
    

    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }

    def gen_nodes():
        for path, p in profiles.iteritems():

            
            props = { 
                k: p[k] for k in ['path' ,'name', 'url','score', 'image' ]                 
            }
            props['label'] = props['name']
            if props['image'].startswith("/"):
                props['image'] = "http://skiller.fr" + props['image']
            yield {
                'nodetype': nodetypes['Profile']['uuid'],
                'properties': props
            }
    
    print "posting nodes"
    count = 0
    fail = 0
    idx = {}
    for node, uuid in bot.post_nodes( gid, gen_nodes() ):
        if not uuid:
            fail += 1
        else :
            count += 1
            idx[node['properties']['path']] = uuid
        
    print "%s nodes inserted " % count

    
    def gen_edges():
        for k, p  in profiles.iteritems(): 

            # skipping 
            follows = len(p['follows'])
            if follows > 1000  or follows == 1 :
                print "skipping ",  k
                continue
                
            for path, name in p['follows']:
                src = idx.get(k, None)
                tgt = idx.get(path, None)
                if src and tgt:
                    yield {
                        'edgetype': edgetypes['follows']['uuid'],
                        'source': src,
                        'label' : "follows",
                        'target': tgt,
                        'properties': {'score':1}
                    }

    print "posting edges"
    count = 0
    fail = 0

    for obj, uuid in bot.post_edges( gid, gen_edges() ):
        if not uuid:
            fail += 1
        else :
            count += 1

    profiles.close()


    
def crawl():

    profile = parse_profile(open("142",'r').read())

    profiles = shelve.open(DB_USERS_PATH)
    profiles[profile['path']] = profile

    for path, name  in profile['follows']:
        if path not in profiles:
            url = "http://skiller.fr" + path
            print url
            r = requests.get( url )
            if r.status_code == 200:
                p = parse_profile(r.text)
                profiles[p['path']] = p
            
    profiles.close()

    
def parse_profile(text):
    page = pq( text )
    avatar = pq(".row.profile .profile-avatar a ", page)
    path =  avatar.attr('href')
    name = pq("img", avatar).attr('alt')
    image = pq("img", avatar).attr('src')
    score  = pq(".row.profile h4 .badge", page).text()
    
    tags = [ (e.attr('href'), pq('.badge', e).text() ) for e in pq( ".row .skill-point-list a"  ,page).items("a")]
    
    questions = [ (e.attr('href'), e.text() )  for e in pq("ul.question-list li a", page).items("a")] # ( url, text )
    
    followed_by, follows = [], []

    connexions = [pq(e) for e in pq(".row.connexions", page)]
    if len(connexions) >= 1:
        followed_by = connexions[0]
        followed_by = [ (e.attr('href'), pq('img', e).attr('title') ) for e in followed_by.items("a")]
    if len(connexions) == 2:
        follows = [ (e.attr('href'), pq('img', e).attr('title') ) for e in connexions[1].items("a")]

    
    print name, path, score, len(followed_by), len(follows)
    #print tags[:5], len(tags)
    #print image
    #print followed_by[:5], follows[:5]

    profile = {
        'path' : path,
        'name' : name,
        'url'  : "http://skiller.fr" + path,
        'score' : score,
        'image' : image,
        'tags' : tags,
        'questions' : questions,
        'follows' : follows,
        'followed_by' : followed_by,
        'time' : datetime.datetime.now().isoformat()
    }

    return profile
    
    
def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--host", action='store', help="host", default=None)
    parser.add_argument("--key", action='store', help="host", default=None)
    parser.add_argument("--gid", action='store', help="host", default="")

    parser.add_argument("--crawl", action='store_true', help="", default=False)
    parser.add_argument("--infos", action='store_true', help="", default=False)

    args = parser.parse_args()

    if args.crawl:
        crawl()
    if args.infos:
        infos()
    if args.host and args.key and args.gid:
        to_padagraph(args.host, args.key, args.gid)


if __name__ == '__main__':
    sys.exit(main())