[PeerJ]
caption = table.find_previous('div','caption').get_text().strip().replace('\u2005',' ').replace('\u2010','').replace('\u2009',' ').replace('   ','').replace('\xa0',' ').replace('         ','').replace('\n','').replace('            ','')
footer= table.find_next('div','table-wrap-foot').get_text().strip().replace('\u2005',' ').replace('\u2010','').replace('\u2009',' ').replace('   ','').replace('\xa0',' ').replace('         ','').replace('\n','').replace('            ','')

