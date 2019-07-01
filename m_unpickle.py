import numpy as np
from functools import reduce
from collections import defaultdict
from common.util import Alphabet,ETag,ConstTag

def findSubstring(fullString, srtString, endString, skips, i):
    cnt = i
    srt = i
    found = False
    parenCount = 0

    while cnt < len(fullString):
        if found:
            if fullString.startswith(endString, cnt):
                parenCount = parenCount + 1
                if parenCount > skips:
                    found = False
                    parenCount = 0
                    return (fullString[srt:cnt], cnt)
        else:
            if fullString.startswith(srtString, cnt):
                srt = cnt
                found = True
        cnt = cnt + 1
    return (None, cnt)

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def decode_numpy(line):
    searchTxt = 'shape=('
    (shapeTxt, cnt) = findSubstring(line, searchTxt, ')', 0, 0)
    shapeTxt = shapeTxt[len(searchTxt):cnt]
    # print('shapeTxt = ' + shapeTxt)

    dim = []
    for i in shapeTxt.split(', '):
        dim.append(int(i))

    # print('dim = ' + str(dim))

    searchTxt = 'dtype='
    (typeTxt, cnt) = findSubstring(line, searchTxt, ' ', 0, cnt)
    typeTxt = typeTxt[len(searchTxt):cnt]

    # print('typeTxt = ' + typeTxt)

    aryType = None
    if typeTxt.startswith('float32'):
        aryType = np.float32
    else:
        raise Exception('Unknown numpy dtype = ' + typeTxt)

    ary = np.zeros(reduce((lambda x, y: x * y), dim), dtype=aryType)

    i = 0
    for seg in line[(cnt+2):-1].split(', '):
        if isfloat(seg):
            ary[i] = float(seg)
            i = i + 1
        else:
            print('Unknown number: ' +  seg)

    if i != reduce((lambda x, y: x * y), dim):
        print('Size = ' + str(reduce((lambda x, y: x * y), dim)))
        print('i = ' + str(i))
        raise Exception("We didn't find the correct number of elements the decode failed!")

    return np.reshape(ary, tuple(dim))

def decodeUnicodeString(uniString):
    out = str('')
    ar = uniString.split(', ')
    for i in ar:
        if i is not '':
            out += chr(int(i))
    return out

def get_element(data):
    if data.startswith('(None'):
        return None

    elif data.startswith('(unicode '):
        return decodeUnicodeString(data[9:])

    elif data.startswith('(etag '):
        # return ETag(bytes(data[6:], "utf-8"))
        return ETag(str(data[6:]))

    elif data.startswith('(constTag '):
        # return ConstTag(bytes(data[10:], "utf-8"))
        return ConstTag(str(data[10:]))

    elif data.startswith('(string '):
        # return bytes(data[8:], "utf-8")
        return str(data[8:])

    elif data.startswith('(int '):
        return int(data[5:])

    else:
         raise Exception('Unknown token table type: ' + data)

# (etag understand-01+-), (unicode 117, 110, 100, 101, 114, 115, 116, 97, 110, 100, 45, 48, 49, ),
def decode_array(line):
    ary = []
    for s in line.split('), '):
        if s:
            ary.append(get_element(s))

    return ary

def decode_token_table(line):
    if line.startswith('(None)'):
        return None

    searchTxt = 'type= '
    (dict_type, cnt) = findSubstring(line, searchTxt, ' ', 1, 0)
    dict_type = dict_type[len(searchTxt):cnt]

    # print('dict_type = ' + dict_type)

    dd = None
    if dict_type.startswith('set'):
        dd = defaultdict(set)
    else:
        raise Exception('Unknown defualt dictionary type ' + dict_type)


    cnt = cnt + 2
    # print(line[cnt:-1])
    dictArray = line[cnt:-1].split('\': [')

    # print(len(dictArray))
    i = 0
    key = dictArray[i][1:]
    i = i + 1
    while i < len(dictArray):
        valueLine = dictArray[i].split('], \'')
        if len(valueLine) == 2:
            val = valueLine[0]
            setVal = set(decode_array(val))
            # print(key + ' _ ' + str(setVal))
            dd[key] = setVal

            key = valueLine[1]

        elif len(valueLine) == 1:
            val = valueLine[0][:-4]
            setVal = set(decode_array(val))
            # print(key + ' _ ' + str(setVal))
            dd[key] = setVal

        else:
            print('dictArray[i] = ' + dictArray[i])
            raise Exception('Irregular arguments ' + str(valueLine))

        i = i + 1

    return dd

def decode_pp_count_dict(line):
    if line.startswith('(None)'):
        return None

    searchTxt = 'type= '
    (dict_type, cnt) = findSubstring(line, searchTxt, ' ', 1, 0)
    dict_type = dict_type[len(searchTxt):cnt]

    # print('dict_type = ' + dict_type)

    dd = None
    if dict_type.startswith('int'):
        dd = defaultdict(int)
    else:
        raise Exception('Unknown defualt dictionary type ' + dict_type)
    cnt = cnt + 2

    dictArray = line[cnt:-1].split('\': ')
    i = 0
    key = get_element(dictArray[i][1:-1])
    i = i + 1
    while i < len(dictArray):
        valueLine = dictArray[i].split(', \'')
        if len(valueLine) == 2:
            val = int(valueLine[0])
            # print(str(key) + ' _ ' + str(val))
            dd[key] = val

            key = get_element(valueLine[1][:-1])

        elif len(valueLine) == 1:
            val = int(valueLine[0][:-3])
            # print(str(key) + ' _ ' + str(val))
            dd[key] = val

        else:
            raise Exception('Irregular arguments ' + str(valueLine))

        i = i + 1

    return dd

def decode_weight(line):
    if line.startswith('(None)'):
        return None

    l = []
    npText = ''
    cnt = 0
    while npText is not None:
        (npText, cnt) = findSubstring(line, '(np.array ', ')', 1, cnt)

        if npText is not None:
            print('Found at '+ str(cnt))
            l.append(decode_numpy(npText))
    return l


# (int 0): (int 0), (int 1): (int 1), (int 2): (int 2), (int 8): (int 8
def decode_dictionary_v2(line):
    if line.startswith('(None'):
        return None

    # print('decode_dictionary_v2 line = ' + line)

    cnt = 0
    keyStart = cnt
    keyStop = cnt

    buffer = ''
    dd = {}
    while cnt < len(line):
        if (line[cnt] == '{') or (line[cnt] == '('):
            buffer = buffer + line[cnt]

        elif (line[cnt] == '}'):
            if buffer[-1] == '{':
                buffer = buffer[:-1]
            else:
                raise Exception('{} buffer = ' + buffer + ', line left = ' + line[cnt:])

        elif (line[cnt] == ')'):
            if buffer[-1] == '(':
                buffer = buffer[:-1]
            else:
                raise Exception('() buffer = ' + buffer + ', line left = ' + line[cnt:])

        elif (line[cnt] == ':'):
            if len(buffer) == 0:
                keyStop = cnt

        elif(line[cnt] == ','):
            if len(buffer) == 0:
                # print('line = ' + line[keyStart:cnt])
                # print('Key = ' + line[keyStart:keyStop-1] + ', value = ' + line[keyStop+2:cnt-1])

                dd[get_element(line[keyStart:keyStop-1])] = get_element(line[keyStop+2:cnt-1])
                # print(dd)
                cnt = cnt + 1
                keyStart = cnt + 1


        cnt = cnt + 1


    dd[get_element(line[keyStart:keyStop-1])] = get_element(line[keyStop+2:cnt])
    return dd


def decode_dictionary(line):
    dd = {}
    dictArray = line.split('): ')
    key = get_element(dictArray[0])
    i =  1
    while i < len(dictArray):
        valueLine = dictArray[i].split('), ')
        if len(valueLine) == 2:
            val = get_element(valueLine[0])
            # print(str(key) + ' _ ' + str(val))
            dd[key] = val

            key = get_element(valueLine[1])

        elif len(valueLine) == 1:
            val = get_element(valueLine[0])
            # print(str(key) + ' _ ' + str(val))
            dd[key] = val

        else:
            val = valueLine[0]
            for j in valueLine[1:-1]:
                val = val + '), ' + j


            print('Warning! ' + dictArray[i])
            print('became key = ' + str(key) + ' and val = ' + str(val) )


            dd[key] = get_element(val)

            key = get_element(valueLine[-1])
            # print('-------------------------------------------------')
            # print('Warning! ' + dictArray[i])
            # print('became key = ' + str(key) + ' and val = ' + str(val) )
            # print('-------------------------------------------------')
            # raise Exception('Irregular arguments ' + str(valueLine))

        i = i + 1
    return dd

def decode_Alphabet(line):
    if line.startswith('(None'):
        return None

    print(line)

    alpha = Alphabet()

    searchTxt = '_index_to_label= {'
    (index_to_label_text, cnt) = findSubstring(line, searchTxt, '), }', 0, 0)
    index_to_label_text = index_to_label_text[len(searchTxt):cnt]

    # print('Alphabet: ')
    # alpha._index_to_label = decode_dictionary(index_to_label_text)
    alpha._index_to_label = decode_dictionary_v2(index_to_label_text)
    # print( 'alpha._index_to_label = ' + str(alpha._index_to_label))


    searchTxt = '_label_to_index= {'
    (label_to_index_text, cnt) = findSubstring(line, searchTxt, '), }', 0, cnt)
    label_to_index_text = label_to_index_text[len(searchTxt):cnt]

    # alpha._label_to_index = decode_dictionary(label_to_index_text)
    alpha._label_to_index = decode_dictionary_v2(label_to_index_text)
    # print(alpha._label_to_index)

    searchTxt = 'num_labels= '
    (num_label_text, cnt) = findSubstring(line, searchTxt, ')', 0, cnt)
    num_label_text = num_label_text[len(searchTxt):cnt]
    alpha.num_labels = int(num_label_text)
    # print(alpha.num_labels)

    return alpha

def decode_feature_codebook(line, type):
    if line.startswith('(None'):
        return None

    # print(line)

    cnt = len('(dictionary ')
    keyStart = cnt
    keyStop = cnt

    buffer = ''
    dd = {}
    while cnt < len(line):
        if (line[cnt] == '{') or (line[cnt] == '('):
            buffer = buffer + line[cnt]

        elif (line[cnt] == '}'):
            if buffer[-1] == '{':
                buffer = buffer[:-1]
            else:
                raise Exception('{} buffer = ' + buffer + ', line left = ' + line[cnt:])

        elif (line[cnt] == ')'):
            if buffer[-1] == '(':
                buffer = buffer[:-1]
            else:
                raise Exception('() buffer = ' + buffer + ', line left = ' + line[cnt:])

        elif (line[cnt] == ':'):
            if len(buffer) == 1:
                keyStop = cnt

        elif(line[cnt] == ','):
            if len(buffer) == 1:
                # print('Key = ' + line[keyStart+1:keyStop] + ', value = ' + line[keyStop+2:cnt])
                # print('Key = ' + line[keyStart+1:keyStop] + ', value = ' + line[keyStop+2:cnt][:5])
                # print('line = ' + line[keyStart:keyStop])
                dd[type(line[keyStart+1:keyStop])] = decode_Alphabet(line[keyStop+2:cnt])
                # print(dd.keys())

                cnt = cnt + 1
                keyStart = cnt

        if len(buffer) == 0:
            if (len(line) - cnt) == 2:
                cnt = cnt + 1
            else:
                print(line[cnt-5:])
                raise Exception('buffer underflow')

        cnt = cnt + 1

    return dd
