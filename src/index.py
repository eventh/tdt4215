#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from whoosh.index import create_in
from whoosh.fields import *


schema = Schema(inclusion=TEXT(stored=True),
                exclusion=TEXT,
                terms=TEXT(stored=True),
                synonym=TEXT,
                short=TEXT,
                code=TEXT,
                label=TEXT,
                formatted=TEXT,
                type=TEXT,
                icpc2_label=TEXT)

if not os.path.exists("indexdir"):
    os.mkdir("indexdir")


ix = create_in("indexdir", schema)
writer = ix.writer()
writer.add_document(inclusion=u"yrkessykdom i blotvev", terms=u"Trokantertendinitt")
writer.commit()


from whoosh.qparser import QueryParser
with ix.searcher() as searcher:
	query = QueryParser("terms", ix.schema).parse(u"Trokantertendinitt")
	results = searcher.search(query)
	print results[0]
