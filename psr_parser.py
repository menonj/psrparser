import sys
import getopt
import time

import io
import os
import re
import json
import pdfplumber

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter

from os import listdir

# Comment: Extract using PDF Miner - This helps with parsing columnar data
def extract_text_by_pdfminer(pdf_path):
    txt = io.StringIO()
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, txt, codec='UTF-8', laparams=LAParams(), imagewriter=None)
    fp = open(pdf_path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    # We only need this data from the first page of the PSR
    for page in PDFPage.get_pages(fp):
        interpreter.process_page(page)
        break
    fp.close()
    device.close()

    str = txt.getvalue()
    txt.close()
    return str

def extract_penalty(inputText):
    regexString = '\d+\s[uU]?.[sS]?.[cC]?.\s[\\u00a7 | §]{1,2}\s\d+(?:\(\w\))*'
    txt2 = extract_section(inputText, 'Offense:', 'Arrest')
    txt3 = txt2.strip()
    strs = re.findall(regexString, txt3,re.MULTILINE)

    return strs

def extract_EOL_score(inputText):

    iTxt = inputText.strip().replace('\n',' ')
    score = re.search("[-+]?\d+$", iTxt, re.MULTILINE)

    if (score is None):
        return 0
    else:
        return score.group(0)

def findUsingRegex(txt, regex):
    match = re.findall(regex, txt)

    if(len(match) < 1):
        return ''
    else:
        return match[0]

def findNumber(txt):
    numberRegEx = '\d+'
    match = re.findall(numberRegEx, txt)

    if(match is None):
        return ''
    else:
        return match[0]

def findDate(txt):
    dateRegEx = '(\d{1,2}|January|Jan|February|Feb|March|Mar|April|Apr|May|May|June|Jun|July|Jul|August|Aug|September|Sep|October|Oct|November|Nov|December|Dec)(\s\d{1,2},\s{0,3}\d{4}|\/\d{1,2}\/(?:\d{4}|\d{2}))'
    match = re.search(dateRegEx, txt)

    if(match is None):
        return ''
    else:
        return match.group(0)

def findValueRightOfColon(txt):
    i = txt.find(':') + 1
    txt2 = txt[i:]

    if(txt2 is None):
        return ''

    return txt2.strip()

def remove_leading_nonalphanumeric(str):
    while not str[0].isalnum(): str = str[1:]
    return str

def remove_lagging_nonalphanumeric(str):
    while not str[len(str)-1].isalnum(): str = str[:len(str)-1]
    return str

def junk_to_alpha(s):
  s = re.sub(r"\s*[^A-Za-z]+\s*", " ", s)
  return s

def extractDataFromPDF(pdfSource):
    text = ''
    with pdfplumber.open(pdfSource) as pdf:
        for page in pdf.pages:
            text1 = page.extract_text()
            text = text + text1
    return text

def extractDataFromPDF2(pdfSource, x_coord, y_coord):
    text = ''
    with pdfplumber.open(pdfSource) as pdf:
        for page in pdf.pages:
            text1 = page.extract_text(x_tolerance=x_coord,y_tolerance=y_coord)
            text = text + text1
    return text


def extractDataFromPDFFile(pdfSource):
    text = ''
    with pdfplumber.load(pdfSource) as pdf:
        for page in pdf.pages:
            text1 = page.extract_text()
            text = text + text1
    return text

def extractDataFromPDFFile(pdfSource, x_coord, y_coord):
    text = ''
    with pdfplumber.load(pdfSource) as pdf:
        for page in pdf.pages:
            text1 = page.extract_text(x_tolerance=x_coord,y_tolerance=y_coord)
            text = text + text1
    return text

def extract_section(txt, fromTag, toTag):
    start = txt.lower().find(fromTag.lower())
    end = txt.lower().find(toTag.lower())

    if(start == -1):
        return ''
    if(end == -1):
        return ''

    sec = txt[start+len(fromTag):end]

    return sec

def extract_section_include_tag(txt, fromTag, toTag):
    start = txt.lower().find(fromTag.lower())
    end = txt.lower().find(toTag.lower())

    if(start == -1):
        return ''

    if(end == -1):
        return ''

    sec = txt[start:end]

    return sec

def extract_section_to_next_key(txt, fromTag, spaceNewLine=True):
    start = txt.lower().find(fromTag.lower())
    first = txt.lower().find(':',start+len(fromTag))
    end = txt.lower().find(':',first+2)

    if(start == -1):
        return ''

    if(end == -1):
        return ''
    sec = txt[start:end]
    arr = sec.split('\n')

    secArray = arr[0:len(arr)-1]
    str3 = ' '

    for s in secArray:
        if(spaceNewLine == True):
            str3 = str3 + s.strip() + ' '
        else:
            str3 = str3 + s.strip()

    return str3

def extract_section_to_newline(txt, fromTag):
    start = txt.lower().find(fromTag.lower())
    end = txt.lower().find('\n',start)

    if(start == -1):
        return -1

    if(end == -1):
        return -1
    sec = txt[start:end]

    return sec

def extract_section_from_computation3(txt, fromTag):

    start = txt.lower().find(fromTag.lower())
    str1 = txt[start:]

    if(start == -1):
        return ''

    strArray = str1.strip().split('\n')
    sec = ''
    for str in strArray:
        str = str.strip()

        if(len(str) == 0):
            continue
        if(re.match('\d+$',str) is None):
            sec = sec + str
            break
        else:
            continue

    return sec.strip()

def extract_section_from_computation2(txt, fromTag):

    strArray = txt.split('\n')
    sec = ''
    for str in strArray:
        str = str.strip()
        if(len(str) == 0):
            continue
        if(re.match('^\d+\.',str) is None):
            sec = sec + str + ' '
        else:
            break

    return sec.strip()

def extract_section_from_computation(txt, fromTag):
    start = txt.lower().find(fromTag.lower())
    if(start == -1):
        return ''

    sec = txt[start:]
    r1 = re.search(r"\s\d+\.", sec, re.MULTILINE)
    end = sec.lower().find(r1.group(0))
    sec = sec[:end]
    return sec

def get_arrest_date(inputText):
    txt2 = extract_section(inputText, 'Arrest', 'Release')
    #txt2 = txt2[txt2.find(':')+1:]
    txt2 = findDate(txt2)
    return txt2.strip()


def get_sentence_date(inputText):
    txt2 = extract_section(inputText, 'Sentence Date', 'Offense')
    #txt3 = txt2[txt2.find(':')+1:]
    txt3 = findDate(txt2)
    return txt3.strip()


def get_release_status(inputText):
    txt2 = extract_section(inputText, 'Release Status', 'Detainers')
    txt3 = txt2[txt2.find(':')+1:]
    return txt3.strip()

def get_district(inputText):
    txt2 = extract_section(inputText, 'United States District Court', 'United States of America')
    idx = txt2.lower().find('for the')
    if(idx > -1):
        txt2 = txt2[idx+7:]
    return txt2.strip()

def get_offenses(inputText):
    txt2 = extract_section(inputText, 'Offense:', 'Arrest')
    txt3 = txt2.strip()

    txt3 = txt3.replace('\n','|')
    txt3 = txt3.split('|')
    t = ''
    for i in txt3:
        if(len(i.strip()) == 0):
            t = t + '|'
        else:
            t = t + i

    return t.split('|')

def get_offense_characteristics(inputText):
    txt2 = extract_section(inputText, 'Offense Level Computation', 'Part B')
    cnt = txt2.lower().count('base offense level')
    i = 1

    str1 = ''
    offChar = []
    while(i <= cnt):
        idx1 = txt2.lower().find('base offense level:')
        idx2 = txt2.lower().find('base offense level:',idx1+5)

        if(idx2 == -1):
            str1 = txt2[idx1:]
            data = parse_offense_characteristics(str1)
            offChar.append(data)
            break
        else:
            str1 = txt2[idx1:idx2]
            data = parse_offense_characteristics(str1)
            offChar.append(data)

        txt2 = txt2[idx2-19:]
        i = i + 1

    return offChar

def parse_offense_characteristics(inputText):
    data = {}
    #txt2 = extract_section_from_computation2(inputText, 'base offense level')
    txt2 = extract_section_from_computation2(inputText, 'base offense level')
    txt3 = extract_section_from_computation3(inputText, 'total offense level')
    scArray = parse_specific_offense_characteristics(inputText)
    data["baseOffense"] = txt2
    data["baseOffenseComputation"] = extract_EOL_score(txt2)
    data["totalOffenseComputation"] = extract_EOL_score(txt3)
    data["specificOffenseCharacteristics"] = scArray

    return data

def parse_specific_offense_characteristics(inputText):
    cnt = inputText.lower().count('specific offense characteristics')
    i = 1
    txt2 = extract_section_from_computation(inputText, 'Specific Offense Characteristics')
    str1 = ''
    scArrary = []
    while(i <= cnt):
        data = {}
        idx5 = txt2.lower().find('specific offense characteristics')
        idx6 = txt2.lower().find('specific offense characteristics',idx5+5)

        if(idx6 == -1):
            str1 = txt2[idx5:]
            data["description"] = str1
            data["adjustment"] = extract_EOL_score(str1)
            scArrary.append(data)
            break
        else:
            str1 = txt2[idx5:idx6]
            data["description"] = str1
            data["adjustment"] = extract_EOL_score(str1)
            scArrary.append(data)

        txt2 = txt2[idx6-30:]
        i = i + 1

    return scArrary

def get_us_attorney(txt):
    txt2 = extract_section(txt, 'Assistant U.S. Attorney', 'Defense Counsel')
    txt3 = txt2.split('\n')

    str = ''
    for t in txt3:
        if(len(t) == 0):
            continue
        else:
            str = str + t.strip() + ' '

    return str.strip()

def get_defense_attorney(txt):
    txt2 = extract_section(txt, 'Defense Counsel', 'Offense')
    txt3 = txt2.split('\n')

    str = ''
    for t in txt3:
        if(len(t) == 0):
            continue
        else:
            str = str + t.strip() + ' '

    return str.strip()


def get_judge(txt):
    txt2 = extract_section(txt, 'Prepared for:', 'Prepared by')
    txt3 = txt2.split('\n')
    ret = ''
    for t in txt3:
        if(len(t.strip()) > 0):
            ret = ret + ', ' + t.strip()
    ret = ret.strip()
    return remove_leading_nonalphanumeric(ret)

def get_section(inputText, startText, endText, regExString):

    inText = inputText.strip().replace('\n',' ')
    sec = extract_section(inText, startText, endText)
    return sec

def get_section_and_parse(inputText, startText, endText, regExString):

    inText = inputText.strip().replace('\n',' ')
    sec = extract_section(inText, startText, endText)
    num = re.search(regExString, sec)
    if(num is None):
        return ''
    else:
        return num.group(0).strip()


def get_key_value_data(inputText, type, searchStrings, regex='', spaceNewLines=True):
    ii = 0
    ret = ''
    for str in searchStrings:
        sec = extract_section_to_next_key(inputText, str, spaceNewLines)
        if(len(sec) > 0):
            break

    if(sec == -1):
        return -1

    if(type == 'date'):
        ret = findDate(sec)
    elif (type == 'number'):
        ret = findNumber(sec)
    elif (regex != ''):
        ret = findUsingRegex(sec, regex)
    else:
        ret = findValueRightOfColon(sec)

    if(ret is None) or (ret == ''):
        return ''
    else:
        return ret

def get_marshall_number(inputText):

    regString = '\d{5}-\d{3}'

    sec = extract_section_to_newline(inputText, "USM#")
    if(sec == -1):
        sec = extract_section_to_newline(inputText, "USM #")
    if(sec == -1):
        return -1

    num = re.search(regString, sec)
    if(num is None):
        return 0
    else:
        return num.group(0)

def get_name(txt):
    txt2 = extract_section(txt, 'Presentence', 'Prepared For')

    txt3 = txt2.replace('\n','|')
    txt4 = txt3.split('|')
    txt5 = ''

    dd = 0
    for n in txt4:
        if( (n.lower().find('presentence') > -1) or
            (n.lower().find('investigation') > -1) or
            (n.lower().find('report') > -1) or
            (n.lower().find('vs') > -1) or
            (n.lower().find('versus') > -1)):
            continue
        else:
            dd = dd + 1
            n = n.strip()
            if(dd == 1):
                txt5 = n
            else:
                txt5 = txt5 + '|' + n
    txt6 = txt5.split('|')

    for k in txt6:
        g = k.lower().find('docket')
        if(g > -1):
            name = k[0:g].replace('\n','').strip()
            if(name == ''):
                continue
            else:
                nm = name.replace('\n','').strip()
                nm = junk_to_alpha(nm).strip()
                if (len(nm) > 0):
                    return nm
        else:
            nm2 = k.replace('\n','').strip()
            nm2 = junk_to_alpha(nm2).strip()
            if(len(nm2) > 0):
                return nm2

def get_docket(txt):
    txt2 = extract_section(txt, 'Presentence', 'Prepared For')

    txt3 = txt2.replace('\n','|')
    txt4 = txt3.split('|')
    txt5 = ''

    dd = 0
    for n in txt4:
        if( (n.lower().find('presentence') > -1) or
            (n.lower().find('investigation') > -1) or
            (n.lower().find('report') > -1) or
            (n.lower().find('vs') > -1) or
            (n.lower().find('versus') > -1)):
            continue
        else:
            dd = dd + 1
            n = n.strip()
            if(dd == 1):
                txt5 = n
            else:
                txt5 = txt5 + '|' + n

    txt6 = txt5.split('|')
    for k in txt6:
        g = k.lower().find('docket')
        if(g > -1):
            name = k[g + 9:]
            if(len(name) > 0):
                return remove_leading_nonalphanumeric(name)
        else:
            continue

def process(pth):

    inputText = extractDataFromPDF(pth)
    inputText2 = extract_text_by_pdfminer(pth)

    data = {}
    data["name"] = get_name(inputText)
    data["criminalHistoryComputation"] = get_section_and_parse(inputText, "criminal history computation", "part c", '(?<=criminal history category (of|is)).\w+')
    data["judge"] = get_key_value_data(inputText, 'text', ['prepared for', 'prepared for'])
    data["preparedBy"] = get_section(inputText, 'prepared by:', 'Assistant','')
    data["usAttorney"] = get_us_attorney(inputText2)
    data["defenseCounsel"] = get_defense_attorney(inputText2)
    data["arrestDate"] = get_key_value_data(inputText, 'date', ['arrest date', 'date of arrest'])
    data["sentenceDate"] = get_key_value_data(inputText, 'date', ['sentence date'])
    data["dateOfBirth"] = get_key_value_data(inputText, 'date', ['Date Of Birth', 'DOB'])
    data["age"] = get_key_value_data(inputText, 'number', ['Age'])
    data["race"] = get_key_value_data(inputText, 'text', ['Race'])
    data["gender"] = get_key_value_data(inputText, 'text', ['Gender','Sex'])
    data["ssn"] = get_key_value_data(inputText, 'text', ['Social Security No', 'Social Security Number', 'SSN'], '\d{3}-\d{2}-\d{3,4}', False)
    data["fbiNumber"] = get_key_value_data(inputText, 'text', ['FBI#', 'FBI #'])
    data["marshallNumber"] = get_key_value_data(inputText, 'text', ['USM#', 'USM #'])
    data["pacsNumber"] = get_key_value_data(inputText, 'text', ['PACTS#', 'PACTS #'])
    data["education"] = get_key_value_data(inputText, 'text', ['education'])
    data["dependents"] = get_key_value_data(inputText, 'text', ['dependents'])
    data["citizenship"] = get_key_value_data(inputText, 'text', ['citizenship'])
    data["legalAddress"] = get_key_value_data(inputText, 'text', ['legal address'])
    data["otherDefendants"] = get_key_value_data(inputText, 'text', ['other defendants'])
    data["docket"] = get_docket(inputText)
    data["district"] = get_district(inputText)
    data["offense"] = get_offenses(inputText)
    data["releaseStatus"] = get_release_status(inputText)
    data["penalty"] = extract_penalty(inputText)
    data["offenseCharacteristics"] = get_offense_characteristics(inputText)

    json_data = json.dumps(data)
    return(json_data)

def main(argv):

    fullCmdArguments = sys.argv
    argumentList = fullCmdArguments[0:]

    #print(argumentList)
    try:
        opts, args = getopt.getopt(argv, "df:")
    except getopt.GetoptError:
        print('python psr_parser.py -f <input file>' or 'python psr_parser.py -d <input directory>')
        sys.exit(2)

    jsonTxt = ''
    timestr = time.strftime("%Y%m%d-%H%M%S")
    
    for opt, arg in opts:
        if opt == '-f':
            arg = argumentList[2]

            jsonTxt = process(arg)
            parsed = json.loads(jsonTxt)

            base = os.path.basename(arg)
            base_filename = base.split('.')[0]
            name = os.path.join('output', base_filename +'_'+timestr+'.json')
            parsed = json.loads(jsonTxt)

            with open(name, "w") as text_file:
                print(json.dumps(parsed, indent=3, sort_keys=True), file=text_file)

        elif opt == '-d':
            arg = argumentList[2]
            i = 0
            for f in listdir(arg):
                i = i + 1
                currFile = arg + '/' + f
                jsonTxt = process(currFile)

                base = os.path.basename(currFile)
                base_filename = base.split('.')[0]
                name = os.path.join('output', base_filename+'_'+timestr+'.json')
                parsed = json.loads(jsonTxt)
                with open(name, "w") as text_file:
                    print(json.dumps(parsed, indent=3, sort_keys=True), file=text_file)

        else:
            print('psr_parser.py -f <inputfile> or PSRParser.py -d <inputdirectory>')

if __name__ == "__main__":
   main(sys.argv[1:])
