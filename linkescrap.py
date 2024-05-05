"""Parse linkedin job pages."""

import re
from glob import glob
from bs4 import BeautifulSoup
import pandas as pd


def clean_text(a_text: str) -> str:
    """Remove shit from soup parsing."""
    return re.sub(r'\s+', ' ', a_text).strip()


def parse_job_htnl(query: str) -> pd.DataFrame:
    # what we will scrap in a data frame
    data = {
        "Job_title": [],
        "Empresa": [],
        "Ubicacion": [],
        "Mode": [],
        "Recruiting": [],
        "First_offered": [],
        "Link": [],
        "How_to_apply": []
    }
    # process all files that match the pattern we used to name when we used selenium to get the pages...
    for file_path in glob(f'linked_{query}_page*.html'):  # grab all html files related to a search
        # read the html file
        print(f'Parsing {file_path}')
        with open(file_path, 'rt', encoding='utf8') as fp:
            html_content = fp.read()
        # parse the html with BS
        soup = BeautifulSoup(html_content, "html.parser")
        # all job offers can be identified by data-chameleon-result-urn, the digits identify the job offer, yay!
        for resu in soup.find_all("div", {"data-chameleon-result-urn":re.compile("urn:li:job:\d+")}):
            # after looking at the code, we can grab these info by matching to specific elements
            # title also contains the link, but is a messy string
            elem = resu.find('span', {"class": re.compile('^entity-result__title-text.+')})
            job_desc = clean_text(elem.text)
            # the next line gives a messy https
            # link = resu.find('a', class_="app-aware-link").get('href')
            # this is a much cleaner link to the job offer:
            re_job = re.match("urn:li:job:(\d+)", resu["data-chameleon-result-urn"])
            jobid = re_job.groups()[0]
            # tried by hand to see if this works, and yes it does!
            link = f'https://www.linkedin.com/jobs/search?currentJobId={jobid}'
            # name of the company offering the job
            empresa = clean_text(resu.find('div', {"class": re.compile('^entity-result__primary-subtitle.+')}).text)
            # location and optional mode of work: remote, etc.
            loc = clean_text(resu.find("div", class_="entity-result__secondary-subtitle t-14 t-normal").text)
            modo = ''
            if loc.find('(') >= 0:  # this might fail if the location is not like 'place (mode)'
                elements = loc.split(' (')
                loc = elements[0]
                modo = elements[1].split(')')[0]
            # these are not always present, so only fill the value if a corresponding element was found
            recru = ''
            elem = resu.find("div", class_="reusable-search-simple-insight__text-container")
            if elem:
                recru = clean_text(elem.text)
            # when it was offered, plus optional how to apply string
            when = ''
            appli = ''
            elem = resu.find("div", class_="display-flex align-items-center mt1")
            if elem:
                els = clean_text(elem.text).split(' • ')  # really ad-hoc, maybe need to be refined
                if len(els) >= 2:
                    when, appli = els[:2]
                else:
                    when = els[0]
            # fill the dict to make a DataFrame
            data["Job_title"].append(job_desc)
            data["Empresa"].append(empresa)
            data["Ubicacion"].append(loc)
            data["Mode"].append(modo)
            data["Recruiting"].append(recru)
            data["First_offered"].append(when)
            data["Link"].append(link)
            data["How_to_apply"].append(appli)
    return pd.DataFrame(data)


if __name__ == '__main__':
    job_search = 'Data Analyst'
    query = job_search.replace(' ', '')
    df = parse_job_htnl(query=query)
    df.to_excel(f'parsed_{query}.xlsx', index=False)
