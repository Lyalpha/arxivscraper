"""
A python program to retreive recrods from ArXiv.org in given
categories and specific date range.

Author: Mahdi Sadjadi (sadjadi.seyedmahdi[AT]gmail[DOT]com).
Updated by: Joe Lyman (https://github.com/Lyalpha/)
"""
from xml.etree import ElementTree
import datetime
import logging
import time

from urllib.request import urlopen
from urllib.error import HTTPError

OAI = "{http://www.openarchives.org/OAI/2.0/}"
ARXIV = "{http://arxiv.org/OAI/arXiv/}"
BASE = "http://export.arxiv.org/oai2?verb=ListRecords&"

LOGGING_FORMAT = "%(asctime)s  %(levelname)-10s %(processName)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)


class Record(object):
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


class Scraper(object):
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
        they were created outside of the given date range. Default: first day of current month.
    date_until: str
        final date in format 'YYYY-MM-DD'. Updated eprints are included even if
        they were created outside of the given date range. Default: today.
    wait: int
        Waiting time in seconds between subsequent calls to API, triggered by Error 503. Default: 30
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
        import arxivscraper.arxivscraper as ax
        scraper = ax.Scraper(category='stat',date_from='2017-12-23',date_until='2017-12-25',t=10,
                 filters={'affiliation':['facebook'],'abstract':['learning']})
        output = scraper.scrape()
    ```
    """

    def __init__(
        self,
        category,
        date_from=None,
        date_until=None,
        wait=30,
        progress_every=90,
        timeout=None,
        filters=None,
        debug=False,
    ):
        self.cat = str(category)
        self.wait = wait
        self.progress_every = progress_every
        self.timeout = timeout
        datetoday = datetime.date.today()
        if date_from is None:
            self.f = str(datetoday.replace(day=1))
        else:
            self.f = date_from
        if date_until is None:
            self.u = str(datetoday)
        else:
            self.u = date_until
        self.url = (
            BASE + "from=" + self.f + "&until=" + self.u + "&metadataPrefix=arXiv&set=%s" % self.cat
        )
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

    def scrape(self):
        start = time.time()
        lastlog = 0
        elapsed = 0
        url = self.url
        logger.debug("url being queried: {}".format(url))
        ds = []
        while True:
            loop_start = time.time()
            logger.debug("fetching next 1000 records")
            try:
                response = urlopen(url)
            except HTTPError as e:
                if e.code == 503:
                    wait = int(e.hdrs.get("retry-after", self.wait))
                    logger.warning("response returned 503, retrying after {} seconds.".format(wait))
                    time.sleep(self.wait)
                    continue
                else:
                    logger.exception("unexpected error from api call")
                    raise
            xml = response.read()
            root = ElementTree.fromstring(xml)
            records = root.findall(OAI + "ListRecords/" + OAI + "record")
            for record in records:
                meta = record.find(OAI + "metadata").find(ARXIV + "arXiv")
                record = Record(meta).output()
                if self.append_all:
                    ds.append(record)
                else:
                    save_record = False
                    for key in self.keys:
                        for word in self.filters[key]:
                            if word.lower() in record[key]:
                                save_record = True

                    if save_record:
                        ds.append(record)

            try:
                token = root.find(OAI + "ListRecords").find(OAI + "resumptionToken")
            except:
                return 1
            if token is None or token.text is None:
                break
            else:
                url = BASE + "resumptionToken=%s" % token.text

            loop_duration = time.time() - loop_start
            lastlog += loop_duration
            if lastlog > self.progress_every:
                logger.info("records fetched so far: {}".format(len(ds)))
                logger.info("created date of latest entry: {}".format(ds[-1]["created"]))
                lastlog = 0

            elapsed += loop_duration
            if self.timeout is not None and elapsed >= self.timeout:
                break

        total_duration = time.time() - start
        logger.info("fetching completed in {:.1f} seconds.".format(total_duration))
        logger.info("total number of records fetched: {:d}".format(len(ds)))
        return ds


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
