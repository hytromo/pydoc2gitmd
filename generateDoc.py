#!/usr/bin/env python2

# whether to include a link to this github project or not
ref_self = True

mymodstr = 'macropolo' # todo later taken from the sys.argv

import inspect, importlib, types, textwrap, StringIO

# keep a list for each function's github link so as to be able to reference it in the description of other functions
githubLinks = {}

def alphanumeric(line, pos):
    string = ''
    for i in range(pos, len(line)):
        if line[i].isalnum() or line[i] == '_':
            string += line[i]
        else:
            break

    return string


def resolveRefs(line):
    while True:
        pos = line.find('@ref:')
        if pos == -1:
            break

        reference = alphanumeric(line, pos + len('@ref:'))

        line = line.replace('@ref:' + reference, '[' + reference + '](#' + githubLinks[reference] + ')')

    return line

def formatDefault(line):
    line = resolveRefs(line)
    return line


def formatNone(line):
    return formatDefault(line)

def formatDescription(line):
    if line == '':
        return ''
    return '_' + formatDefault(line) + '_'

def formatVariable(line):
    if line == 'None':
        return '`None`'

    parts = line.split(' ')

    if len(parts) < 2:
        return line

    # variable name
    parts[0] = '`' + parts[0] + '`'

    # variable type
    parts[1] = parts[1][1:]
    parts[1] = parts[1][:-2]
    
    types = parts[1].split('/')

    for i in range(len(types)):
        types[i] = '`' + types[i] + '`'

    parts[1] = '(' + '/'.join(types) + '):'

    line = ' '.join(parts)

    return formatDefault(line)

mymod = importlib.import_module(mymodstr)

functionParts = {
        '> Description': {
            'mode' : 'des',
            'title' : '* **Description**\n\n',
            'newline': False,
            'formatfunc': formatDescription
        },
        '> Parameters': {
            'mode' : 'par',
            'title' : '* **Parameters**\n\n',
            'formatfunc' : formatVariable,
        },
        '> Returns': {
            'mode' : 'ret',
            'title' : '* **Return values**\n\n',
            'formatfunc' : formatVariable,
        },
        '> Example': {
            'mode' : 'exa',
            'title' : '* **Example usage**\n\n',
            'start_string': '```python\n',
            'end_string': '```\n'
        },
}

for key, value in functionParts.iteritems():
    for attribute in ['start_string', 'end_string']:
        if not (attribute in functionParts[key]):
            functionParts[key][attribute] = ''

    if not ('formatfunc' in functionParts[key]):
        functionParts[key]['formatfunc'] = formatNone

    if not ('newline' in functionParts[key]):
        functionParts[key]['newline'] = True

classes = {}

def findExampleRemoveNo(line):
    counter = 0
    for i in range(len(line)):
        if (line[i].isspace()):
            counter += 1
        else:
            break

    return counter

def formatDoc(doc):
    finalS = ''
    s = StringIO.StringIO(doc)
    curMode = 'search'
    curPart = None
    lineStartRemoveNo = 0
    firstExampleLine = False

    for line in s:
        if firstExampleLine:
            lineStartRemoveNo = findExampleRemoveNo(line)
            firstExampleLine = False
        if curMode != 'exa':
            line = line.strip()
        else:
            line = line.rstrip()[lineStartRemoveNo:]
        if line == '' and curMode not in ['exa', 'des']:
            continue
        if line in functionParts:
            if curPart != None:
                finalS += curPart['end_string']
                #  if curPart['mode'] == 'des':
                    #  finalS += '\n'
            curPart = functionParts[line]
            finalS += curPart['title']
            finalS += curPart['start_string']
            curMode = curPart['mode']
            if curMode != 'exa':
                lineStartRemoveNo = 0
                firstExampleLine = False
            else:
                firstExampleLine = True
        else:
            if (curPart == None):
                finalS += line
            else:
                finalS += curPart['formatfunc'](line)
                if (curPart['mode'] in ['ret', 'par']):
                    finalS += '\n\n'
                elif (curPart['mode'] in ['des', 'exa']):
                    finalS += '\n'

    if curPart != None:
        finalS += curPart['end_string']

    return finalS

def methodString(method, args):
    args = [arg for arg in args if arg not in ['self', 'cls']]
    mString = method + ' ('
    mString += ', '.join(args)
    mString += ')'

    return mString

def githubLink(method, details):
    args = details['args']

    link = method.lower() + '-' + '-'.join([arg.lower() for arg in args if arg not in ['self', 'cls']])

    return link

for classTuple in inspect.getmembers(mymod, predicate = inspect.isclass):
    curClass = classTuple[1]
    if curClass.__module__ == mymodstr:

        classFunctions = {
                'own': None,
                'static': {},
                'class': {},
                'instance': {}
        }

        if curClass.__doc__ != None:
            classFunctions['own'] = curClass.__doc__

        def isLegitFunction(func):
            return func != None and (inspect.isroutine(func) or (hasattr(func, '__name__') and isinstance(curClass.__dict__[func.__name__], classmethod)))

        for methodTuple in inspect.getmembers(curClass, predicate = isLegitFunction) :

            method = methodTuple[1]
            if hasattr(method, '__doc__') and method.__doc__ is not None:
                methodType = 'instance'
                if isinstance(curClass.__dict__[method.__name__], staticmethod):
                    methodType = 'static'
                elif isinstance(curClass.__dict__[method.__name__], classmethod):
                    methodType = 'class'

                classFunctions[methodType][method.__name__] = {}
                classFunctions[methodType][method.__name__]['doc'] = method.__doc__
                classFunctions[methodType][method.__name__]['args'] = inspect.getargspec(method).args

        classes[curClass.__name__] = classFunctions

for className in classes:
    curClass = classes[className]

    print '# ' + className
    print
    if curClass['own'] is not None:
        print curClass.own
        print

    for methodType in ['static', 'class', 'instance']:
        if not curClass[methodType]:
            continue

        print '- [' + methodType.title() + ' methods](#' + methodType + '-methods)'
        print
        for method, details in sorted(curClass[methodType].items()):
            githubLinks[method] = githubLink(method, details)
            print '    - [' + method + '](#' + githubLinks[method] + ')'

        print


    for methodType in ['static', 'class', 'instance']:
        if not curClass[methodType]:
            continue

        print '## ' + methodType.title() + ' methods'
        print

        for method, details in sorted(curClass[methodType].items()):
            doc = details['doc']
            args = details['args']
            print '---'
            print
            print '### `' + methodString(method, args) + '`'
            print
            print formatDoc(textwrap.dedent(doc))
            print

if ref_self:
    print 'This documentation was automatically formated for github by [pydoc2gitmd](https://github.com/hytromo/pydoc2gitmd)'
