import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
start = time.time()


def simple_url_func():
    urls = [
      'http://www.python.org',
      'https://docs.python.org/3/',
      'https://docs.python.org/3/whatsnew/3.7.html',
      'https://docs.python.org/3/tutorial/index.html',
      'https://docs.python.org/3/library/index.html',
      'https://docs.python.org/3/reference/index.html',
      'https://docs.python.org/3/using/index.html',
      'https://docs.python.org/3/howto/index.html',
      'https://docs.python.org/3/installing/index.html',
      'https://docs.python.org/3/distributing/index.html',
      'https://docs.python.org/3/extending/index.html',
      'https://docs.python.org/3/c-api/index.html',
      'https://docs.python.org/3/faq/index.html'
      ]

    # results = []
    # for url in urls:
    #     with urllib.request.urlopen(url) as src:
    #         results.append(src)

    with ThreadPoolExecutor(16) as executor:
        results = executor.map(urllib.request.urlopen, urls)


if __name__ == "__main__":


    simple_url_func()

    end = time.time()
    print(end - start)