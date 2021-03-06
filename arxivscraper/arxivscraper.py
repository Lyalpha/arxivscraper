"""
A python program to retreive recrods from ArXiv.org in given
categories and specific date range.

Author: Mahdi Sadjadi (sadjadi.seyedmahdi[AT]gmail[DOT]com).
Updated by: Joe Lyman (https://github.com/Lyalpha/)
"""
import logging
import time
from urllib.error import HTTPError
from urllib.request import urlopen
from xml.etree import ElementTree

OAI2 = "{http://www.openarchives.org/OAI/2.0/}"
ARXIV = "{http://arxiv.org/OAI/arXiv/}"
ARXIVOAI2_URLBASE = "http://export.arxiv.org/oai2?"

LOGGING_FORMAT = "%(asctime)s  %(levelname)-10s %(processName)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)


class Category:
    """
    Holds details of valid categories for arXiv scraping

    Paramters
    ---------
    retries : int
        Number of times to try api call, in case of 503 response.
    """

    def __init__(self, retries=5):
        self.retries = retries
        self.url = "{}verb=ListSets".format(ARXIVOAI2_URLBASE)
        self.categories = self._get_categories()

    def _get_categories(self):
        logger.debug("fetching arxiv OAI2 categories")
        for i in range(self.retries):
            try:
                response = urlopen(self.url)
            except HTTPError as e:
                if e.code == 503:
                    wait = int(e.hdrs.get("retry-after", 5))
                    logger.warning("response returned 503, retrying after {} seconds.".format(wait))
                    time.sleep(wait)
                else:
                    logger.exception("unexpected error from api call")
                    raise
            else:
                break
        else:
            logger.error("could not retrieve arxiv categories")
            return

        xml = response.read()
        root = ElementTree.fromstring(xml)
        sets = root.findall(OAI2 + "ListSets/" + OAI2 + "set")
        categories = dict()
        for s in sets:
            spec = s.find(OAI2 + "setSpec").text
            name = s.find(OAI2 + "setName").text
            categories[spec] = name
        return categories

    def categories_info(self):
        s = ""
        for key, value in self.categories.items():
            s += "{:17}{:}\n".format(key, value)
        return s


class Record:
    """
    A class to hold a single record from ArXiv
    Each records contains the following properties:

    object should be of xml.etree.ElementTree.Element.
    """

    def __init__(self, xml_record):
        self.xml = xml_record
        self.id = self._get_text(ARXIV, "id")
        self.url = "https://arxiv.org/abs/" + self.id
        self.title = self._get_text(ARXIV, "title")
        self.abstract = self._get_text(ARXIV, "abstract")
        self.cats = self._get_text(ARXIV, "categories")
        self.created = self._get_text(ARXIV, "created")
        self.updated = self._get_text(ARXIV, "updated")
        self.doi = self._get_text(ARXIV, "doi")
        self.authors, self.authors_fullnames = self._get_authors()
        self.affiliation = self._get_affiliation()

    def _get_text(self, namespace, tag):
        """Extracts text from an xml field"""
        try:
            return self.xml.find(namespace + tag).text.strip().lower().replace("\n", " ")
        except:
            return ""

    def _get_authors(self):
        authors_xml = self.xml.findall(ARXIV + "authors/" + ARXIV + "author")
        last_names = [author.find(ARXIV + "keyname").text.lower() for author in authors_xml]
        first_names = [
            author.find(ARXIV + "forenames").text.lower()
            if author.find(ARXIV + "forenames") is not None
            else ""
            for author in authors_xml
        ]
        full_names = [(a + " " + b).strip() for a, b in zip(first_names, last_names)]
        return last_names, full_names

    def _get_affiliation(self):
        authors = self.xml.findall(ARXIV + "authors/" + ARXIV + "author")
        try:
            affiliation = [author.find(ARXIV + "affiliation").text.lower() for author in authors]
            return affiliation
        except:
            return []

    def output(self):
        d = {
            "title": self.title,
            "id": self.id,
            "abstract": self.abstract,
            "categories": self.cats,
            "doi": self.doi,
            "created": self.created,
            "updated": self.updated,
            "authors": self.authors,
            "authors_fullnames": self.authors_fullnames,
            "affiliation": self.affiliation,
            "url": self.url,
        }
        return d


class Scraper:
    """
    A class to hold info about attributes of scraping,
    such as date range, categories, and number of returned
    records. If `from` is not provided, the first day of
    the current month will be used. If `until` is not provided,
    the current day will be used.

    Paramters
    ---------
    category: str
        The category of scraped records
    data_from: str
        starting date in format 'YYYY-MM-DD'. Updated eprints are included even if
        they were created outside of the given date range. Default: None (= earliest
        date available in arxiv)
    date_until: str
        final date in format 'YYYY-MM-DD'. Updated eprints are included even if
        they were created outside of the given date range. Default: None (= latest
        date available in arxiv)
    progress_every: int
        Send an INFO level log entry about progress after this many seconds during querying.
        Default: 90
    timeout: int or None
        Timeout in seconds after which the scraping stops. Default: None
    filter: dictionary
        A dictionary where keys are used to limit the saved results. Possible keys:
        subcats, author, title, abstract. See the example, below.

    Example:
    Returning all eprints from

    ```
        from arxivscraper import Scraper
        scraper = Scraper(category='stat', date_from='2017-12-23', date_until='2017-12-25',
            wait=10, filters={'affiliation':['facebook'], 'abstract':['learning']})
        output = scraper.scrape()
    ```
    """

    def __init__(
        self,
        category,
        date_from=None,
        date_until=None,
        progress_every=90,
        timeout=None,
        filters=None,
        debug=False,
    ):
        self.category = category
        self.check_category()
        self.progress_every = progress_every
        self.timeout = timeout

        self.url = "{}verb=ListRecords&metadataPrefix=arXiv&set={}".format(
            ARXIVOAI2_URLBASE, self.category
        )
        if date_from is not None:
            self.url += "&from={}".format(date_from)
        if date_until is not None:
            self.url += "&until={}".format(date_until)

        if filters is None:
            filters = dict()
        self.filters = filters
        if not self.filters:
            self.append_all = True
        else:
            self.append_all = False
            self.keys = filters.keys()
        if debug:
            logger.setLevel(logging.DEBUG)

    def check_category(self):
        c = Category()
        valid_categories = c.categories
        if valid_categories is None:
            logger.warning("couldn't check valid categories")
            return
        try:
            category = valid_categories[self.category]
        except KeyError:
            logger.error("{} is not a valid category.".format(self.category))
            logger.info("valid categories:\n{}".format(c.categories_info()))
            raise

    def scrape(self):
        logger.debug("scraping {} from arxiv".format(self.category))
        start = time.time()
        lastlog = 0
        elapsed = 0
        url = self.url
        logger.debug("url being queried: {}".format(url))
        results = []
        while True:
            loop_start = time.time()
            logger.debug("fetching next 1000 records")
            try:
                response = urlopen(url)
            except HTTPError as e:
                if e.code == 503:
                    wait = int(e.hdrs.get("retry-after", 5))
                    logger.warning("response returned 503, retrying after {} seconds.".format(wait))
                    time.sleep(wait)
                    continue
                else:
                    logger.exception("unexpected error from api call")
                    raise
            xml = response.read()
            root = ElementTree.fromstring(xml)
            records = root.findall(OAI2 + "ListRecords/" + OAI2 + "record")
            for record in records:
                meta = record.find(OAI2 + "metadata").find(ARXIV + "arXiv")
                record = Record(meta).output()
                if self.append_all:
                    results.append(record)
                else:
                    save_record = False
                    for key in self.keys:
                        for word in self.filters[key]:
                            if word.lower() in record[key]:
                                save_record = True

                    if save_record:
                        results.append(record)

            list_records = root.find(OAI2 + "ListRecords")
            if list_records is None:
                logger.debug("ListRecords empty")
                break
            token = list_records.find(OAI2 + "resumptionToken")
            if token is None or token.text is None:
                logger.debug("resumptionToken text empty")
                break
            url = "{}verb=ListRecords&resumptionToken={}".format(ARXIVOAI2_URLBASE, token.text)

            loop_duration = time.time() - loop_start
            lastlog += loop_duration
            if lastlog > self.progress_every:
                logger.info("records fetched so far: {}".format(len(results)))
                logger.info("created date of latest entry: {}".format(results[-1]["created"]))
                lastlog = 0

            elapsed += loop_duration
            if self.timeout is not None and elapsed >= self.timeout:
                break

        total_duration = time.time() - start
        logger.info("fetching completed in {:.1f} seconds.".format(total_duration))
        logger.info("total number of records fetched: {:d}".format(len(results)))
        return results


cats = [
    "astro-ph",
    "cond-mat",
    "gr-qc",
    "hep-ex",
    "hep-lat",
    "hep-ph",
    "hep-th",
    "math-ph",
    "nlin",
    "nucl-ex",
    "nucl-th",
    "physics",
    "quant-ph",
    "math",
    "CoRR",
    "q-bio",
    "q-fin",
    "stat",
]
subcats = {
    "cond-mat": [
        "cond-mat.dis-nn",
        "cond-mat.mtrl-sci",
        "cond-mat.mes-hall",
        "cond-mat.other",
        "cond-mat.quant-gas",
        "cond-mat.soft",
        "cond-mat.stat-mech",
        "cond-mat.str-el",
        "cond-mat.supr-con",
    ],
    "hep-th": [],
    "hep-ex": [],
    "hep-ph": [],
    "gr-qc": [],
    "quant-ph": [],
    "q-fin": [
        "q-fin.CP",
        "q-fin.EC",
        "q-fin.GN",
        "q-fin.MF",
        "q-fin.PM",
        "q-fin.PR",
        "q-fin.RM",
        "q-fin.ST",
        "q-fin.TR",
    ],
    "nucl-ex": [],
    "CoRR": [],
    "nlin": ["nlin.AO", "nlin.CG", "nlin.CD", "nlin.SI", "nlin.PS"],
    "physics": [
        "physics.acc-ph",
        "physics.app-ph",
        "physics.ao-ph",
        "physics.atom-ph",
        "physics.atm-clus",
        "physics.bio-ph",
        "physics.chem-ph",
        "physics.class-ph",
        "physics.comp-ph",
        "physics.data-an",
        "physics.flu-dyn",
        "physics.gen-ph",
        "physics.geo-ph",
        "physics.hist-ph",
        "physics.ins-det",
        "physics.med-ph",
        "physics.optics",
        "physics.ed-ph",
        "physics.soc-ph",
        "physics.plasm-ph",
        "physics.pop-ph",
        "physics.space-ph",
    ],
    "math-ph": [],
    "math": [
        "math.AG",
        "math.AT",
        "math.AP",
        "math.CT",
        "math.CA",
        "math.CO",
        "math.AC",
        "math.CV",
        "math.DG",
        "math.DS",
        "math.FA",
        "math.GM",
        "math.GN",
        "math.GT",
        "math.GR",
        "math.HO",
        "math.IT",
        "math.KT",
        "math.LO",
        "math.MP",
        "math.MG",
        "math.NT",
        "math.NA",
        "math.OA",
        "math.OC",
        "math.PR",
        "math.QA",
        "math.RT",
        "math.RA",
        "math.SP",
        "math.ST",
        "math.SG",
    ],
    "q-bio": [
        "q-bio.BM",
        "q-bio.CB",
        "q-bio.GN",
        "q-bio.MN",
        "q-bio.NC",
        "q-bio.OT",
        "q-bio.PE",
        "q-bio.QM",
        "q-bio.SC",
        "q-bio.TO",
    ],
    "nucl-th": [],
    "stat": ["stat.AP", "stat.CO", "stat.ML", "stat.ME", "stat.OT", "stat.TH"],
    "hep-lat": [],
    "astro-ph": [
        "astro-ph.GA",
        "astro-ph.CO",
        "astro-ph.EP",
        "astro-ph.HE",
        "astro-ph.IM",
        "astro-ph.SR",
    ],
}
