You are welcome to use the `converter.py` script to convert the latest `Folkets
Lexikon`_ to the format of an in-book dictionary understandable by Kindle. I find
it useful when reading books in Swedish with my Kindle Paperwhite.

In order to create your own dictionary you need to

 1. download the Swedish-to-English lexikon itself from http://folkets-lexikon.csc.kth.se/folkets/folkets_sv_en_public.xml.

 2. run converter.py to get a dictionary index file::

     $ ./converter.py folkets_sv_en_public.xml dict-index.xml

 3. then create a mobi file with the `kindlegen` utility provided by Amazon::

     $ ./kindlegen folketslexikon.opf -c2 -dont_append_source -o dict.mobi

Those who don't want to bother with the latest and greatest dictionary data
may download the file I use from my Google Drive https://drive.google.com/file/d/0By97zlmvqmPSVFJZaUlveUZtQjQ/view?usp=sharing

.. _Folkets Lexikon: http://folkets-lexikon.csc.kth.se/folkets/folkets.html
