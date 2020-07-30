[ATS]
caption = table.caption.get_text().strip().replace('\u2005',' ').replace('\u2010','').replace('\u2009',' ').replace('   ','').replace('\xa0',' ').replace('         ','').replace('\n','').replace('            ','')
footer=  [i.get_text().strip().replace('\u2005',' ').replace('\u2010','').replace('\u2009',' ').replace('   ','').replace('\xa0',' ').replace('         ','').replace('\n','').replace('            ','') for i in table.find_next('div','tableFooter')]

                   
