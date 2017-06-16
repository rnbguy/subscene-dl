#!/usr/bin/env python3

import pprint

import requests
import bs4
import terminaltables
import textwrap
import zipfile
import io
import os
import sys
import re

server_addr = "https://subscene.com"
request_session = requests.Session()
requests.utils.cookiejar_from_dict({"LanguageFilter": "13"}, request_session.cookies)


class SubResult:
    row_header = ["Language", "Positive", "Name", "Files", "HI", "Uploader", "Comment"]
    def __init__(self, soup_):
        tds = soup_.select("td")
        col1 = tds[0].select("span")
        self.info = {}
        self.info["language"] = col1[0].text.strip()
        self.info["positive"] = "★" if "positive-icon" in col1[0]["class"] else ""
        self.info["orig_name"] = col1[1].text.strip()
        self.info["name"] = "\n".join(textwrap.wrap(self.info["orig_name"], 50))
        self.info["link"] = tds[0].select("a")[0]["href"]
        self.info["files"] = tds[1].text.strip()
        self.info["hi"] = "✓" if "a41" in tds[2]["class"] else ""
        self.info["uploader"] = tds[3].select("a")[0].text.strip()
        self.info["uploader_link"] = tds[3].select("a")[0]["href"]
        self.info["orig_comment"] = tds[4].text.strip()
        self.info["comment"] = "\n".join(textwrap.wrap(self.info["orig_comment"], 50))

    def __str__(self):
        return pprint.pformat(self.info, indent=2)

    def row_format(self):
        return [self.info[e.lower()] for e in SubResult.row_header]


class Sub:
    def __init__(self, subresult):
        self.info = subresult.info
        link = server_addr + self.info["link"]
        sub_r = request_session.get(link)
        sub_soup = bs4.BeautifulSoup(sub_r.text, "lxml")
        main_soup = sub_soup.select("div.box.clearfix > div.top.left")[0]
        try:
            self.info["poster"] = main_soup.select("img[alt=Poster]")[0]["src"]
        except:
            pass
        self.info["name1"] = main_soup.select("div.header h1 span[itemprop=name]")[0].text.strip()
        try:
            self.info["imdb"] = main_soup.select("div.header h1 a.imdb")[0]["href"]
        except:
            pass
        self.info["release"] = main_soup.select("div.header > ul > li.release > div")[0].text.strip()
        author = main_soup.select("div.header > ul > li.author > a")[0]
        self.info["author"] = author.text.strip()
        self.info["author_link"] = author["href"]
        self.info["comment1"] = main_soup.select("div.header > ul > li.comment-wrapper > div.comment")[0].text.strip()
        self.info["download_link"] = main_soup.select("div.download > a#downloadButton")[0]["href"]

    def __str__(self):
        return pprint.pformat(self.info, indent=2)

def get_table(subs):
    li = ["No."]
    li.extend(SubResult.row_header)
    table = [li]
    for i, e in enumerate(subs, start=1):
        k = [i]
        k.extend(e.row_format())
        table.append(k)
    return table



def search_keywords(filename):
    filename = os.path.splitext(filename)[0]
    l = ["720p", "1080p", "hdtv", "web-*dl", "x264", "x265", "hevc", "2ch"]
    k = re.search("(^.*?)((?:"+"|".join(l)+").*)", filename)
    n = k.group(1)
    a = k.group(2)
    # if re.search("s\d\de\d\d", n, flags=re.IGNORECASE):
    #     print("tv series")
    # else:
    #     print("movies")
    n = n.lower().replace(".", " ").split()
    a = a.lower().replace(".", " ").split()
    return (n, a)

def search_with_filename(video_filename):
    q, a = search_keywords(re.sub(r":|'|&", "", video_filename))
    print("keyword: {}".format(" ".join(q)))
    mr = re.compile("(?=.*" +  ")(?=.*".join(q + a) + ")", flags=re.IGNORECASE)
    msr = re.compile("(?=.*" +  ")(?=.*".join(q) + ")", flags=re.IGNORECASE)
    query = {"q": " ".join(q), "r": True}
    path = "/subtitles/release"
    r = request_session.get(server_addr + path, params=query)
    soup = bs4.BeautifulSoup(r.content, "lxml")
    results = soup.select(".box > .content tr")[1:]
    subs_orig = []
    subs_same_name = []
    for e in results:
        try:
            s = SubResult(e)
            if mr.search(s.info["orig_name"]):
                subs_orig.append(s)
            elif msr.search(s.info["orig_name"]):
                subs_same_name.append(s)
            # print(Sub(s))
        except:
            raise
    if len(subs_orig) == 0 and len(subs_same_name) == 0:
        print("No subtitles found!")
    else:
        if len(subs_orig) > 0:
            subs = subs_orig
        elif len(subs_same_name) > 0:
            subs = subs_same_name
        table = get_table(subs)
        print(terminaltables.SingleTable(table).table)
        sub_ix = input("sub no.? [1..{}] ".format(len(table) - 1))
        sub = Sub(subs[int(sub_ix) - 1])
        link = server_addr + sub.info["download_link"]
        r = request_session.get(link)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for infofile in z.infolist()[:1]:
                z.extract(infofile)
                sub_ext = os.path.splitext(infofile.filename)[1]
                vid_name = os.path.splitext(video_filename)[0]
                os.rename(infofile.filename, vid_name+sub_ext)


def main():
    search_with_filename(sys.argv[1])

if __name__ == "__main__":
    main()