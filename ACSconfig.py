[ACS]
caption = table.find_previous('div','hlFld-FigureCaption').get_text().strip().replace('\n            ','').replace('\u2005',' ').replace('\u2010','').replace('\u2009',' ').replace('   ','').replace('\xa0',' ').replace('         ','').replace('\n','').replace('            ','')
footer = ''.join([i.get_text().strip().replace('\u2005',' ').replace('\u2010','').replace('\u2009',' ').replace('   ','').replace('\xa0',' ').replace('         ','').replace('\n','').replace('            ','')  for i in  table.find_next('div','NLM_table-wrap-foot')])
