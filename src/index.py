import os
from whoosh.index import create_in
from whoosh.fields import *

schema = Schema(umls_semanticType=TEXT(stored=True),
				icpc2_label=TEXT,
				synonym=TEXT(stored=True),
				code_compacted=TEXT,
				code_formatted=TEXT,
				umls_tui=TEXT,
				exclusion=TEXT,
				umls_conceptId=TEXT,
				umls_atomId=TEXT,
				inclusion=TEXT,
				underterm=TEXT,
				icpc2_code=TEXT)
				
if not os.path.exists("indexdir"):
    os.mkdir("indexdir")

ix = create_in("indexdir", schema)
writer = ix.writer()
writer.add_document(umls_semanticType = u"First document", synonym = u"good stuff")
writer.commit()


from whoosh.qparser import QueryParser
with ix.searcher() as searcher:
	query = QueryParser("synonym", ix.schema).parse(u"good")
	results = searcher.search(query)
	print results[0]
	
