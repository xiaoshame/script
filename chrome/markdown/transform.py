import sys
import time
import re


TIMESTAMP = int(time.time())

HTML_HEAD = """\
<!DOCTYPE NETSCAPE-Bookmark>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
""".format(TIMESTAMP)
HTML_END = """</DL><p>\n"""

GROUP_HEAD = """\t<DT><H3 ADD_DATE="{ts}" LAST_MODIFIED="{ts}">{title}</H3>
\t<DL><p>
"""
GROUP_END = "\t</DL><p>\n"

MASK = """\t<DT>\
<A HREF="{link}" ADD_DATE="{ts}" ICON="data:image/png;base64,{icon}">{title}</A>
"""


def main(input):
    with open(input, 'r',encoding='utf-8') as f:
        lists = f.readlines()

    # open html file to write into
    output = open('favorites.html', 'w',encoding='utf-8')
    output.write(HTML_HEAD)

    group_re = re.compile(r'^(#+) +(.*)$') # eg. ## network
    mask_re = re.compile(r'\[(.*)\]\((.*)\)') # eg. [baidu](https://www.baidu.com)

    pre_H_level = 0 # previous Header level, H2 or H3 or ...
    for line in lists:
        line = line.strip()

        m = mask_re.search(line)
        if m:
            # find link
            output.write(MASK.format(link=m.group(2), ts=TIMESTAMP, icon=None, title=m.group(1)))
        else:
            m = group_re.search(line)
            if m:
                # find header
                cur_H_level = len(m.group(1)) # current Header level
                if cur_H_level <= pre_H_level:
                    for _ in range(pre_H_level - cur_H_level + 1):
                        output.write(GROUP_END)
                pre_H_level = cur_H_level
                output.write(GROUP_HEAD.format(ts=TIMESTAMP, title=m.group(2)))
    output.write(HTML_END)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('No input files.')
        sys.exit(1)
    main(sys.argv[1])