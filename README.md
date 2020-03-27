[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.889853.svg)](https://doi.org/10.5281/zenodo.889853)

# arXivScraper
An ArXiV scraper to retrieve records from given categories and date range.

## Install

Use `pip` (or `pip3` for python3):

```bash
$ pip install arxivscraper
```

or download the source and use `setup.py`:

```bash
$ python setup.py install
```

or if you do not want to install the module, copy `arxivscraper.py` into your working
directory.

To update the module using `pip`:
```bash
pip install arxivscraper --upgrade
```

## Examples

### Without filtering

You can directly use `arxivscraper` in your scripts. Let's import `arxivscraper`
and create a scraper to fetch all preprints in condensed matter physics category
from 27 May 2017 until 7 June 2017 (for other categories, see below):

```python
import arxivscraper
scraper = arxivscraper.Scraper(category='physics:cond-mat', date_from='2017-05-27',date_until='2017-06-07')
output = scraper.scrape()
```

If `date_from` and/or `date_until` are omitted (or `None`), then they are effectively set as the earliest
and latest dates available for arxiv records in the category chosen (see 
[OAI2 documentation](http://www.openarchives.org/OAI/2.0/openarchivesprotocol.htm#SelectiveHarvestingandDatestamps))

### With filtering
To have more control over the output, you could supply a dictionary to filter out the results. As an example, let's collect all preprints related to machine learning. This subcategory (`stat.ML`) is part of the statistics (`stat`) category. In addition, we want those preprints that word `learning` appears in their abstract.

```python
import arxivscraper.arxivscraper as ax
scraper = ax.Scraper(category='stat', date_from='2017-08-01', date_until='2017-08-10', 
    filters={'categories':['stat.ml'],'abstract':['learning']})
output = scraper.scrape()
```

> In addition to `categories` and `abstract`, other available keys for `filters` are: `author` and `title`.


## Categories
To get a list of valid `category` arguments to scrape on ArXiv:

```python
from arxivscraper import Category
cat = Category()
print(cat.categories_info())
```
This will return (as of March 2020):
```
cs               Computer Science
econ             Economics
eess             Electrical Engineering and Systems Science
math             Mathematics
physics          Physics
physics:astro-ph Astrophysics
physics:cond-mat Condensed Matter
physics:gr-qc    General Relativity and Quantum Cosmology
physics:hep-ex   High Energy Physics - Experiment
physics:hep-lat  High Energy Physics - Lattice
physics:hep-ph   High Energy Physics - Phenomenology
physics:hep-th   High Energy Physics - Theory
physics:math-ph  Mathematical Physics
physics:nlin     Nonlinear Sciences
physics:nucl-ex  Nuclear Experiment
physics:nucl-th  Nuclear Theory
physics:physics  Physics (Other)
physics:quant-ph Quantum Physics
q-bio            Quantitative Biology
q-fin            Quantitative Finance
stat             Statistics
```

## Contributing
Ideas/bugs/comments? Please open an issue or submit a pull request on Github.

## How to cite
If `arxivscraper` was useful in your work/research, please consider to cite it as :
```
Mahdi Sadjadi (2017). arxivscraper: Zenodo. http://doi.org/10.5281/zenodo.889853
```

or
```
@misc{msadjadi,
  author       = {Mahdi Sadjadi},
  title        = {arxivscraper},
  year         = 2017,
  doi          = {10.5281/zenodo.889853},
  url          = {https://doi.org/10.5281/zenodo.889853}
}
```

## Author
* **Mahdi Sadjadi**, 2017. Updated by **Joe Lyman**, 2020

* Website: [mahdisadjadi.com](http://mahdisadjadi.com), [github.com/Lyalpha](https://github.com/Lyalpha)

* Twitter: [@mahdisadjadi](http://twitter.com/MahdiSadjadi)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
