import os
import datetime
import argparse
from pdf2image import convert_from_path
import cv2
import numpy as np
from PIL import Image
from bs4 import BeautifulSoup

class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        elif self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        self.parent[self.find(x)] = self.find(y)

def overlapping_boxes(boxes):
    uf = UnionFind()

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            box1 = boxes[i]
            box2 = boxes[j]
            if box1[0] < box2[0] + box2[2] and box1[0] + box1[2] > box2[0] and box1[1] < box2[1] + box2[3] and box1[1] + box1[3] > box2[1]:
                uf.union(i, j)

    groups = {}
    for i in range(len(boxes)):
        group = uf.find(i)
        if group not in groups:
            groups[group] = []
        groups[group].append(boxes[i])

    return groups.values()


def compare_images(img1_path, img2_path, output_path):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    
    # Convert the images to grayscale
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # Compute the absolute difference between the two images
    diff = cv2.absdiff(img1_gray, img2_gray)
    
    # Threshold the difference image (this will reveal regions of non-zero pixels)
    _, thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Find contours in the threshold image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Set the amount of padding
    padding = 10

    # Collect the bounding rectangles around each contour, with padding
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        boxes.append((x - padding, y - padding, w + 2 * padding, h + 2 * padding))

    # Group the overlapping boxes
    groups = overlapping_boxes(boxes)


    # Draw the combined bounding rectangles
    for group in groups:
        min_x = min(box[0] for box in group)
        min_y = min(box[1] for box in group)
        max_x = max(box[0] + box[2] for box in group)
        max_y = max(box[1] + box[3] for box in group)

        cv2.rectangle(img2, (min_x, min_y), (max_x, max_y), (0, 0, 255), 3)

    
    # Save the image with the differences highlighted
    cv2.imwrite(output_path, img2)


def main():
    parser = argparse.ArgumentParser(description='Compare two PDFs and generate an HTML page showing the original PDF next to the one with changes highlighted.')
    parser.add_argument('pdf1', help='The path to the first PDF file')
    parser.add_argument('pdf2', help='The path to the second PDF file')
    args = parser.parse_args()

    # Convert the PDFs to images
    pages1 = convert_from_path(args.pdf1)
    pages2 = convert_from_path(args.pdf2)

    # Get the max length for equal number of pages
    max_len = max(len(pages1), len(pages2))
    if len(pages1) < max_len:
        for _ in range(max_len - len(pages1)):
            blank = Image.new('RGB', pages1[0].size, (255, 255, 255))
            pages1.append(blank)
    elif len(pages2) < max_len:
        for _ in range(max_len - len(pages2)):
            blank = Image.new('RGB', pages2[0].size, (255, 255, 255))
            pages2.append(blank)

    # Create the output directories
    output_dir = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)

    # Load the HTML template
    with open('template.html') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Find the columns in the HTML
    columns = soup.find_all(class_='column')
    original_column = columns[0]
    changes_column = columns[1]

    for i in range(max_len):
        # Save the images from the PDFs
        img1_path = os.path.join(output_dir, 'images', f'pdf1_page{i+1}.png')
        img2_path = os.path.join(output_dir, 'images', f'pdf2_page{i+1}.png')
        pages1[i].save(img1_path, 'PNG')
        pages2[i].save(img2_path, 'PNG')

        # Compare the images and save the result
        output_path = os.path.join(output_dir, 'images', f'output_page{i+1}.png')
        compare_images(img1_path, img2_path, output_path)

        # Add the images to the columns
        img1 = soup.new_tag('img', src=f'images/pdf1_page{i+1}.png')
        img2 = soup.new_tag('img', src=f'images/output_page{i+1}.png')
        original_column.append(img1)
        changes_column.append(img2)

    # Save the modified HTML
    with open(os.path.join(output_dir, 'comparison.html'), 'w') as f:
        f.write(str(soup))

if __name__ == "__main__":
    main()
