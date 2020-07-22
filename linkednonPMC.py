#!/usr/bin/env python
# coding: utf-8

from IPython import display
import os
import re
from html.parser import HTMLParser
from bs4 import BeautifulSoup
from bs4 import element
from itertools import product
import numpy as np
import pandas as pd
import nltk 
from itertools import groupby


# # Superscripts and subscripts

def process_supsub(soup):
    for sup in soup.find_all(['sup','sub']):
        s = sup.get_text()
        if sup.string==None:
            sup.extract()
        elif re.match('[_-]',s):
            sup.string.replace_with('{} '.format(s))
        else:
            sup.string.replace_with('_{} '.format(s))

def process_em(soup):
    for em in soup.find_all('em'):
        s = em.get_text()
        if em.string==None:
            em.extract()
        else:
            em.string.replace_with('{} '.format(s))
def table_to_2d(t):
    rows = t.find_all('tr')
    
    # How many columns in the table
    
    ftrow= [str(link.get('colspan')) for link in t.tbody.tr.find_all('td')]
    for n, i in enumerate(ftrow):
        if i == 'None':
            ftrow[n] = '1'
    col_n = sum([int(i) for i in ftrow])       
    
    # Build an empty matrix for all possible cells
    if t.thead:                                                # to account 'tr' of thead and tbody only 
        rows = t.thead.find_all('tr') + t.tbody.find_all('tr')
    else:                                                      #some table doesnot have thead tag
        rows = t.tbody.find_all('tr')
    #Build
    table = [[''] * col_n for row in rows]

    # Fill matrix from row date
    rowspans = {}  # track pending rowspans, column number mapping to count
    for row_idx, row in enumerate(rows):
        span_offset = 0  # how many columns are skipped due to row and colspans 
        for col_idx, cell in enumerate(row.findAll(['td', 'th'])):
            # adjust for preceding row and colspans
            col_idx += span_offset
            while rowspans.get(col_idx, 0):
                span_offset += 1
                col_idx += 1
        
            # fill table data 
            if not cell.get('colspan'):
                colspan = 1
            else:
                colspan= int(cell.get('colspan'))

            if not cell.get('rowspan'):
                rowspan = 1
            else:
                rowspan= int(cell.get('rowspan'))
    
            # Next column is offset by the colspan
            span_offset += colspan - 1
            value= cell.get_text()

            # clean the cell
            value = value.strip().replace('\u2009',' ')
#             value = value.replace('\u2009',' ')
            if value.startswith('(') and value.endswith(')'):
                value = value[1:-1]
            pval_regex = r'((\d+.\d+)|(\d+))(\s{0,1})[*××xX](\s{0,1})10_([−-]{0,1})(\d+)'
            if re.match(pval_regex,value):
#                 value = value.replace(' × 10_','e').replace('×10_','e').replace('−','-')
                value = re.sub(r'(\s{0,1})[*××xX](\s{0,1})10_','e',value).replace('−','-')
#             if re.match('^((\d+.\d+)|(\d+))[eE]([−-]{0,1}\d+)$',value):
#                 value = float(value)
            try:
                value = float(value.replace('−','-').replace('–','-').replace(',',''))
            except:
                value = value
            for drow, dcol in product(range(rowspan), range(colspan)):
                try:
                    table[row_idx + drow][col_idx + dcol] = value
                    rowspans[col_idx + dcol] = rowspan
                except IndexError:
                    # rowspan or colspan outside the confines of the table
                    pass
        # update rowspan bookkeeping
        rowspans = {c: s - 1 for c, s in rowspans.items() if s > 1}
    return table

		
def check_superrow(row):
    if len(set([i for i in row if (str(i)!='')&(str(i)!='\n')&(str(i)!='None')]))==1:
        return True
    else:
        return False
		
def is_number(s):
    try:
        float(s.replace(',',''))
        return True
    except ValueError:
        return False

def is_mix(s):
    if any(char.isdigit() for char in s):
        if any(char for char in s if char.isdigit()==False):
            return True
    return False

def is_text(s):
    if any(char.isdigit() for char in s):
        return False
    return True

def find_format(header):
#     parts = nltk.tokenize.word_tokenize(header)
    if header=='':
        return None
    a = re.split(r'[:|/,;]', header)
    b = re.findall(r'[:|/,;]', header)
    parts = []
    for i in range(len(b)):
        parts+=[a[i],b[i]]
    parts.append(a[-1])

    # identify special character
    special_char_idx = []
    for idx,part in enumerate(parts):
        if part in ':|\/,;':
            special_char_idx.append(idx)
    
    # generate regex pattern
    if special_char_idx:
        pattern = r''
        for idx in range(len(parts)):
            if idx in special_char_idx:
                char = parts[idx]
                pattern+='({})'.format(char)
            else:
                pattern+='(\w+)'
        pattern = re.compile(pattern)
        return pattern
    else:
        return None

def test_format(pattern,s):
    if re.search(pattern,s):
        return True
    return False

def split_format(pattern,s):
	return [i for i in re.split(r'[:|/,;]', s) if i not in ':|\/,;']


def get_headers(t):
    idx_list = []
    for idx,row in enumerate(t.findAll('tr')):
        if row.findAll('th'):
            idx_list.append(idx)
    return idx_list

def get_superrows(t):
    idx_list = []
    for idx,row in enumerate(t):
        if idx not in get_headers(t):
            if check_superrow(row):
                idx_list.append(idx)
    return idx_list

def table2json(table_2d, header_idx, subheader_idx, superrow_idx, table_num, caption, footer):
    tables = []
    sections = []
    cur_table = {}
    cur_section = {}

    pre_header = []
    pre_superrow = None
    cur_header = ''
    cur_superrow = ''
    for row_idx,row in enumerate(table_2d):
        if row_idx in header_idx:
            cur_header = [table_2d[i] for i in [i for i in subheader_idx if row_idx in i][0]]
        elif row_idx in superrow_idx:
            cur_superrow = [i for i in row if i not in ['','None']][0]
        else:      
            if cur_header!=pre_header:
                sections = []
                pre_superrow = None
                cur_table = {'identifier':str(index+1), 
                             'title':caption, 
                             'columns':cur_header,
                             'section':sections,
                             'footer':footer}
                tables.append(cur_table)
            elif cur_header==pre_header:
                cur_table['section'] = sections
            if cur_superrow!=pre_superrow:
                cur_section = {'section_name':cur_superrow, 
                               'results': [row]}
                sections.append(cur_section)
            elif cur_superrow==pre_superrow:
                cur_section['results'].append(row)

            pre_header = cur_header
            pre_superrow = cur_superrow

    if len(tables)>1:
        for table_idx,table in enumerate(tables):
            table['identifier'] += '.{}'.format(table_idx+1)
    return tables		    

		
def table2dict(table_2d):
    headers = [table_2d[i] for i in header_idx]
    tmp_list = []
    superrow = ''
    if table_2d==None:
        return None
    for r_idx,row in enumerate(table_2d):
        if r_idx not in header_idx:
            if r_idx in superrow_idx:
                superrow = row
            else:
                tmp_list.append({'headers':headers,
                                 'superrow':superrow, 
                                 'row': row,
                                 # below three items will be discarded and only added in the next formating json step
                                 'table_num':table_num,
                                 'foot':footer, 
                                 'caption':caption,})
    return tmp_list			
def get_files(base_dir):
    file_list = []
    files = os.listdir(base_dir)
    for i in files:
        abs_path = os.path.join(base_dir,i)
        if re.match(r'.*/\d*_table_\d+.html',abs_path):
            file_list.append(abs_path)
        elif os.path.isdir(abs_path)&('ipynb_checkpoints' not in abs_path):
            file_list+=get_files(abs_path)
    return file_list


def filepath(x):
    filepath = str(x)
    with open(filepath,'r') as f:
            text = f.read()
    soup = BeautifulSoup(text, 'html.parser')
    return soup

base_dir= '/home/moibrahim/Desktop/linked/'
file_list = get_files(base_dir)
#pick up the aimed files in the dict
Doc= re.findall(r'\d+_table_\d+.html',str(file_list))
Doc.sort()
D= ','.join(Doc)
#extract number of file
file_aim= re.findall(r'(\d+)_table_\d+.html',str(file_list))
file_aim.sort()
#select unique values
final_new_menu = list(dict.fromkeys(file_aim))
	

#select all table per a journal
for i,k in enumerate(final_new_menu):
    files= re.findall(f'{k}_table_\d+.html',str(D))
    for l, j in enumerate(files):  
        thelist=[filepath(base_dir + j) for j in files] 



        tables = []
        for index, obj in enumerate(thelist):
            soup=obj

            for table_num, table in enumerate(soup.find_all('table',recursive=True)): 

                    # ### caption and footer
                    # Enter caption and footer as guide 
                    if  table.find_previous('h1','c-article-table-title u-h1'):
                        caption = table.find_previous('h1','c-article-table-title u-h1').get_text().replace('\u2005',' ').replace('\u2010','').replace('\u2009',' ').replace('   ','').replace('\xa0',' ').replace('         ','').replace('\n','').replace('            ','')
                    else:
                        caption = ' '#table.find('caption').get_text()
                    
                    if table.find_next('div','c-article-table-footer'):
                        footer= [i.get_text().strip().replace('\u2005',' ').replace('\u2010','').replace('\u2009',' ').replace('   ','').replace('\xa0',' ').replace('         ','').replace('\n','').replace('            ','')  for i in table.find_next('div','c-article-table-footer')]
                    else:
                        footer = ' '
                    
                    header_idx = []
                    for idx,row in enumerate(table.findAll('tr')):
                        if row.findAll('th'):
                            header_idx.append(idx)

                    # ## span table to single-cells

                    table_2d = table_to_2d(table)
                    # ## find superrows


                    superrow_idx = []
                    if table_2d!=None:
                        for row_idx,row in enumerate(table_2d):
                            if row_idx not in header_idx:
                                if check_superrow(row):
                                    superrow_idx.append(row_idx)

                    # # Identify subheaders

                    value_idx = [i for i in range(len(table_2d)) if i not in header_idx+superrow_idx]
                    col_type = []
                    for col_idx in range(len(table_2d[0])):
                        cur_col = [i[col_idx] for i in table_2d]
                        num_cnt = 0
                        txt_cnt = 0
                        mix_cnt = 0
                        for cell in cur_col:
                            cell = str(cell).lower()
                            if cell in ['none', '', '-',]:
                                continue
                            elif is_number(cell):
                                num_cnt+=1
                            elif is_mix(cell):
                                mix_cnt+=1
                            elif is_text(cell):
                                txt_cnt+=1
                        if max(num_cnt,txt_cnt,mix_cnt)==num_cnt:
                            col_type.append('num')
                        elif max(num_cnt,txt_cnt,mix_cnt)==txt_cnt:
                            col_type.append('txt')
                        else:
                            col_type.append('mix')
                    subheader_idx = []
                    for row_idx in value_idx:
                        cur_row = table_2d[row_idx]
                        unmatch_cnt = 0
                        for col_idx in range(len(cur_row)):
                            cell = str(cur_row[col_idx]).lower()
                            if is_text(cell) and col_type[col_idx]!='txt' and cell not in ['none', '', '-',]:
                                unmatch_cnt+=1
                        if unmatch_cnt>=len(cur_row)/2:
                            subheader_idx.append(row_idx)
                    header_idx+=subheader_idx

                    subheader_idx = []
                    
                    if header_idx:
                        tmp = [header_idx[0]] 
                    

                    for i,j in zip(header_idx,header_idx[1:]):
                        if j==i+1:
                            tmp.append(j)
                        else:
                            subheader_idx.append(tmp)
                            tmp=[j]
                    subheader_idx.append(tmp)

                   
                    # ## split pattern
                    if header_idx:
                        try:
                            for col_idx,th in enumerate(table_2d[header_idx[-1]]):
                                print("\rProgress {:2.1%}".format(col_idx / len(table_2d[header_idx[-1]])))
                                display.clear_output(wait=True)
                            if table.find_next_siblings('p','TableText'):
                                [i.get_text().strip().replace('_','') for i in table.find_next_siblings('p','TableText')]
                                pattern = find_format(th)
                                if pattern:
                                    cnt = 0
                                    for row_idx in range(len(table_2d)):
                                        if (row_idx not in header_idx)&(row_idx not in superrow_idx):
                                            cnt+=test_format(pattern,table_2d[row_idx][col_idx])
                                    # if all elements follow the same pattern
                                    if cnt==len(table_2d)-len(header_idx)-len(superrow_idx):
                                        for row_idx,row in enumerate(table_2d):
                                            if (row_idx in header_idx)&(row_idx!=header_idx[-1]):
                                                row+=[table_2d[row_idx][col_idx],table_2d[row_idx][col_idx]]
                                            elif (row_idx in header_idx)&(row_idx==header_idx[-1]):
                                                row+=split_format(pattern,row[col_idx])
                                            elif row_idx in superrow_idx:
                                                row+=[table_2d[row_idx][col_idx],table_2d[row_idx][col_idx]]
                                            else:
                                                row+=split_format(pattern,row[col_idx])
                                pattern=None
                                cnt = 0
                        except:

                            # make sure that all rows have the same length
                            assert len(set([len(i) for i in table_2d]))==1
                    else:
                        continue

                            # # Index sections

                            # In[32]:


                    if  superrow_idx==[]:
                        first_col = [row[0] for row in table_2d if table_2d.index(row) not in header_idx]
                        unique_vals = set([i for i in first_col if i not in [' ','None']])
                        section_values = None
                        if len(unique_vals)<=len(first_col)/2:
                            section_values = list(unique_vals)
                        print(section_values)

                            # ## store in json

                        cur_table = table2json(table_2d, header_idx, subheader_idx, superrow_idx, table_num, caption, footer)

                            # # merge headers

                        sep = '<!>'
                        for table in cur_table:
                            headers = table['columns']
                            

                            new_header = []
                            if header_idx:
                                if range(len(headers[0])):
                                    for col_idx in range(len(headers[0])):
                                        new_element = ''
                                        for r_idx in range(len(headers)):
                                            new_element += headers[r_idx][col_idx]+sep
                                            new_element = new_element.rstrip(sep)
                                            new_header.append(new_element)
                                        table['columns'] = new_header

                               

                    # # Obsolete

                    table_json = table2dict(table_2d)

                    # 1. process every headers
                    # 2. split multi table first, then process headers in each sub-table

                    # ## Merge headers

                    # # Update Json Model

                    cur_table =  table2json(table_2d, header_idx, subheader_idx, superrow_idx, table_num, caption, footer)

                    tables+=cur_table

            


        table_json = {'tables':tables}
            
            
              

        z= k + str('_tables.json')

        import json

        with open(z, "w") as outfile: 
            json.dump(table_json , outfile) 


