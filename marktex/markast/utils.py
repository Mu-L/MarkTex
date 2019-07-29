import re,os,shutil
from urllib.parse import urljoin
from hashlib import md5

re_command = re.compile(r"%$")

re_toc = re.compile(r"^\[TOC\]") # 目录
re_section = re.compile(r"^(#+)(.*)") # 章节
re_multibox = re.compile(r"^ ?\[([x√]?)\] (.*)") # 章节
# re_section = re.compile(r"^(#+)(.*)") # 章节

re_bold = re.compile(r"\*\*([^*\n]*)\*\*") # 加粗
re_italic = re.compile(r"\*([^*\n]*)\*") # 斜体
re_delete = re.compile(r"~~([^~\n]*)~~") # 删除线
re_underline = re.compile(r"__([^_\n]*)__") # 下划线
re_xml = re.compile(r"<[^\\>\n]+>[^<>]*<\\[^\\>\n]+>") # xml标签（只支持一级标签

re_list = re.compile("^ *- *(.*)") # 列表
re_enum = re.compile("^ *[0-9]+\. *(.*)") # enum

re_ilink = re.compile("(!?)\[([^[\n]*)\]\(([^(\n]*)\)") # link and image
re_image = re.compile("^!\[([^[\n]*)\]\(([^(\n]*)\)") # image

re_quote = re.compile("^>(.*)") # quote
re_quote_envi = re.compile("^>* *([^ ]*)")
re_quote_flag = re.compile("^>*")


re_footnote = re.compile(r"\[\^([^[^]+)\]") #footnote
re_footnote_tail = re.compile(r"^\[\^(.+)\]:(.*)") #footnote

re_table = re.compile("^\|(.*\|)+") # table
re_table_content = re.compile(r"(?=\|([^|\n]*)\|)")

re_incode = re.compile("`([^`\n]*)`") # inline code
re_code = re.compile("^```(.*)") # code

re_informula = re.compile("\$([^$\n]*)\$") # inline formula
re_formula = re.compile("^\$\$") # formula
re_formula_tail = re.compile("\$\$$") # formula

re_all = re.compile(r"(\*\*[^*]*\*\*|" #bold
                    r"\*[^*]*\*|" #italic
                    r"~~[^~]*~~|" #
                    r"__[^_]*__|" #deleteline
                    r"\[\^[^[^]+\]|" #footnote
                    r"!?\[[^[\n]*\]\([^(\n]*\)|" #link or image
                    r"`[^`\n]*`|" # code 
                    r"\$[^$\n]*\$)") # formula


class ScanTool:
    @staticmethod
    def isBlank(line):
        return len(line.strip()) == 0

    @staticmethod
    def isToc(line):
        return re.search(re_toc, line)

    @staticmethod
    def isSection(line):
        return re.search(re_section, line)

    @staticmethod
    def isCode(line):
        return re.search(re_code, line)

    @staticmethod
    def isFormula(line):
        return re.search(re_formula, line)

    @staticmethod
    def isFormulaTail(line):
        return re.search(re_formula_tail, line)

    @staticmethod
    def isList(line):
        return re.search(re_list, line)

    @staticmethod
    def isEnum(line):
        return re.search(re_enum, line)

    @staticmethod
    def isMultiBox(line):
        return re.search(re_multibox, line)

    @staticmethod
    def isQuote(line):
        return re.search(re_quote, line)

    @staticmethod
    def isTable(line):
        return re.search(re_table, line)

    @staticmethod
    def isFootTail(line):
        return re.search(re_footnote_tail, line)

    @staticmethod
    def isImage(line):
        return re.search(re_image, line)

class MatchTool:
    @staticmethod
    def initial(line:str)->list:
        sub_line, count = re.subn(re_all,
                                  lambda s: f"@@@{s.group(0)}@@@",
                                  line)
        buffer = sub_line.split("@@@")
        return buffer

    @staticmethod
    def match_bold(token):
        return re.search(re_bold, token)

    @staticmethod
    def match_italic(token):
        return re.search(re_italic, token)

    @staticmethod
    def match_deleteline(token):
        return re.search(re_delete, token)

    @staticmethod
    def match_underline(token):
        return re.search(re_underline, token)

    @staticmethod
    def match_footnote(token):
        return re.search(re_footnote, token)

    @staticmethod
    def match_incode(token):
        return re.search(re_incode, token)

    @staticmethod
    def match_informula(token):
        return re.search(re_informula, token)

    @staticmethod
    def match_ilink(token):
        return re.search(re_ilink, token)

class ExtractTool:
    @staticmethod
    def codeType(raw):
        match_start = re.search(re_code, raw)
        return match_start.group(1)

    @staticmethod
    def tableLine(raw):
        table_line = re.findall(re_table_content, raw)
        table_line = [LineParser.fromNormal(content) for content in table_line]
        return table_line

    @staticmethod
    def multibox(raw):
        check_type = {
            "√":2,
            "x":1,
            "":0,
        }

        match = re.search(re_multibox,raw)
        return (check_type[match.group(1)],LineParser.fromNormal(match.group(2)))

    @staticmethod
    def section(raw):
        match_line = re.search(re_section, raw)
        level = len(match_line.group(1))
        content = match_line.group(2).strip()
        return level,LineParser.fromNormal(content)

    @staticmethod
    def image(raw):
        match = re.search(re_ilink, raw)
        desc = match.group(2)
        link = match.group(3)
        return desc,link

    @staticmethod
    def bold(raw):
        match = re.search(re_bold, raw)
        return match.group(1).strip()

    @staticmethod
    def italic(raw):
        match = re.search(re_italic, raw)
        return match.group(1).strip()

    @staticmethod
    def deleteline(raw):
        match = re.search(re_delete, raw)
        return match.group(1).strip()

    @staticmethod
    def underline(raw):
        match = re.search(re_underline, raw)
        return match.group(1).strip()

    @staticmethod
    def incode(raw):
        match = re.search(re_incode, raw)
        return match.group(1).strip()

    @staticmethod
    def informula(raw):
        match = re.search(re_informula, raw)
        return match.group(1).strip()

    @staticmethod
    def hyperlink(raw):
        match = re.search(re_ilink, raw)
        desc = match.group(2)
        link = match.group(3)
        link = urljoin("http:",link) #自动添加http，一般网站即使应该是https也没有影响
        return desc,link

    @staticmethod
    def footnote(raw):
        match = re.search(re_footnote, raw)
        return  match.group(1).strip()

    @staticmethod
    def footnote_tail(raw):
        match = re.search(re_footnote_tail, raw)
        key = match.group(1).strip()
        content = match.group(2).strip()
        return key,content

class CleanTool:
    @staticmethod
    def clean_comment(doc:str):
        lines = doc.split("\n")
        res = []
        for line in lines:
            line = re.sub(re_command,"",line)
            res.append(line)
        return "\n".join(res)


    @staticmethod
    def clean_itemize(raw):
        return re.sub(re_list,lambda s:f"{s.group(1)}",raw)

    @staticmethod
    def clean_enumerate(raw):
        return re.sub(re_enum, lambda s: f"{s.group(1)}", raw)

    @staticmethod
    def get_multibox_flag(raw):
        return True

    @staticmethod
    def clean_quotes(raw):
        if isinstance(raw,list):
            return [re.sub(re_quote_envi, lambda x: f"{x.group(1)}", line) for line in raw]
        elif isinstance(raw,str):
            return re.sub(re_quote_envi,lambda s:f"{s.group(1)}",raw)

class LineParser:

    @staticmethod
    def fromNormal(line):
        from marktex.markast.line import TokenLine
        from marktex.markast.token import Bold, Italic, Footnote, InCode, InFormula, Hyperlink, InImage, Token,DeleteLine,UnderLine

        buffer = MatchTool.initial(line)
        tline = TokenLine()

        for token in buffer:


            match = MatchTool.match_bold(token)
            if match is not None:
                token = Bold(token)
                tline.append(token)
                continue

            match = MatchTool.match_italic(token)
            if match is not None:
                token = Italic(token)
                tline.append(token)
                continue

            match = MatchTool.match_deleteline(token)
            if match is not None:
                token = DeleteLine(token)
                tline.append(token)
                continue

            match = MatchTool.match_underline(token)

            if match is not None:
                token = UnderLine(token)
                tline.append(token)
                continue

            match = MatchTool.match_footnote(token)
            if match is not None:
                token = Footnote(token)
                tline.append(token)
                continue

            match = MatchTool.match_incode(token)
            if match is not None:
                token = InCode(token)
                tline.append(token)
                continue

            match = MatchTool.match_informula(token)
            if match is not None:
                token = InFormula(token)
                tline.append(token)
                continue

            match = MatchTool.match_ilink(token)
            if match is not None:
                if len(match.group(1)) == 0:  # 无!，是链接
                    token = Hyperlink(token)
                    tline.append(token)
                else:
                    token = InImage("InImage(can't be put inline.)")
                    tline.append(token)
                continue

            token = Token(token)
            tline.append(token)

        return tline

class ImageTool:
    @staticmethod
    def equal(a,b):
        return os.path.getsize(a) == os.path.getsize(b) and \
               os.path.getmtime(a) == os.path.getmtime(b)


    @staticmethod
    def hashmove(pref:str, fdir:str)->str:
        pref = os.path.abspath(pref)
        size = os.path.getsize(pref)
        mtime = os.path.getmtime(pref)
        mmd = md5()
        mmd.update(str(size+mtime).encode())

        _,ext = os.path.splitext(pref)
        newf = os.path.join(fdir,f"{mmd.hexdigest()}{ext}")
        newf = os.path.abspath(newf)

        if os.path.exists(newf) and ImageTool.equal(pref, newf):
            print(f"Have cache, checked.")
            newf = newf.replace("\\", "/")
            return newf
        else:
            shutil.copy2(pref, newf)

        print(f"Image is local file, move it \tfrom:{pref}\tto:{newf}")
        newf = newf.replace("\\","/")
        return newf


    @staticmethod
    def verify(url:str,fdir:str):
        '''
        如果是本地图片，那么就将其hash后移动到fdir中，hash值与文件大小、修改时间有关
        如果是网络图片，那么直接根据url得到hash值，下载到fdir中
        :param url:
        :param fdir:
        :return:
        '''
        print(f"\rCheck th Image:{url}.")
        if os.path.exists(url) and os.path.isfile(url):
            return ImageTool.hashmove(url,fdir)

        os.makedirs(fdir, exist_ok=True)
        from urllib.request import urlretrieve

        mmd = md5()
        mmd.update(url.encode())
        fname = os.path.join(fdir,f"{mmd.hexdigest()}.jpg")
        fname = os.path.abspath(fname)

        if os.path.exists(fname):
            print(f"Have cache, checked.")
            fname = fname.replace("\\", "/")
            return fname
        try:
            urlretrieve(url, fname)
        except:
            print(f"Error when download:{url}.")

        print(f"Download in {fname}.")
        fname = fname.replace("\\", "/")
        return fname

if __name__ == "__main__":
    print(ImageTool.verify(r"https://f12.baidu.com/it/u=430466972,3036851607&fm=76",r"D:\Web"))
