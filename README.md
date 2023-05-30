# PDFdiffer
A small proof of concept script that takes two PDF files as input, converts them to images, then uses openCV to find and highlight the differences using combined bounding boxes in red.

It then generates image(s) to show the differences, and an HTML files that shows a side-by-side view.

Note: a difference in number of pages is handled by inserting a blank page on the relevant side of the diff.

Happy to review and accept improvements. Ideally, instead of changes being highlighted all in red, you would want removals in red, additions in green, and any other changes in blue. I might get to that in future, I might not.

### Dependencies
- Poppler
- pdf2image
- openCV
- numpy
- Pillow
- BeautifulSoup4

