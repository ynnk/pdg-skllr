# pdg-skllr

## Built a `follow network`

## System requirements
    
    $ pip install -r requirements.txt
    # if you get errors  installing python deps, re run pip command later
    $ sudo aptitude install libxml2-dev libxslt-dev zlib-dev

## Crawl & graph

1. crawl website users
2. create graphs on the followers

    $ python crawl.py --crawl --infos --host http://padagraph.io --key `cat ../key.txt` --gid skllr

## Visualize data 

![network](https://github.com/ynnk/pdg-skllr/blob/master/s1.png?raw=true)
http://padagraph.io/graph/skllr
