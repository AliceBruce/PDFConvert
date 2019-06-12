# -* - coding:utf-8 -*-
import pdfplumber
import plistlib
import os
import argparse
import tempfile
from pdf2image import convert_from_path
import pprint
from glob import glob
from CutImages import process_image

pp = pprint.PrettyPrinter(indent=4)


# convert pdf to images and save in target dir
def save_iamges(pdfPath, target,nums):
    print('converting pdf to images')
    n = int(nums/100)
    for i in range(n):
        with tempfile.TemporaryDirectory() as path:
            images_from_path = convert_from_path(pdfPath, output_folder=path, last_page=(i+1)*100, first_page=i*100+1)
        for j in range(len(images_from_path)):
            page = images_from_path[j]
            name = os.path.basename(pdfPath).split('.')[0]
            to_file = os.path.join(target_folder, name + '_%d.png') % (i*100+j+1)
            page.save(os.path.join(target, to_file), 'png')
        print('save %d images %d.' % (100,i))

    with tempfile.TemporaryDirectory() as path:
        images_from_path = convert_from_path(pdfPath, output_folder=path, last_page=nums, first_page=n*100+1)
    for j in range(len(images_from_path)):
        page = images_from_path[j]
        name = os.path.basename(pdfPath).split('.')[0]
        to_file = os.path.join(target_folder, name + '_%d.png') % (n*100+j+1)
        page.save(os.path.join(target, to_file), 'png')
    print('save %d images.' % len(images_from_path))
    print('save done')


def process_page(pdfPath, page):
    height, width = int(page.height), int(page.width)
    pl = {}
    pl['imageHeight'] = height
    pl['imageWidth'] = width
    pl['textBoxes'] = []
    line_size = {}
    for i in range(len(page.extract_words())):
        data = page.extract_words()[i]
        pl['textBoxes'].append({'_imageAnnotatorData': {'_isRectangle': True},
                                'box': {'coordinateSpace': 'Image', 'coordinateSpaceOrigin': 'TopLeft',
                                        'point1': (data['x0'], data['top']),
                                        'point2': (data['x1'], data['top']),
                                        'point3': (data['x1'], data['bottom']),
                                        'point4': (data['x0'], data['bottom']),
                                        },
                                'class': 'CRTCompositeTextBox',
                                'needsReview': False,
                                'text': '',
                                'type': 'Line',
                                'textBoxes': []})
    pl['class'] = 'CRTRootTextBox'
    pl['needsReview'] = False
    pl['version'] = 4
    print('---------- 第[%d]页 ----------' % page.page_number)
    chars = page.chars

    name = os.path.basename(pdfPath).split('.')[0]
    to_file = os.path.join(target_folder, name + '_%d.plist') % page.page_number
    pl['text'] = page.extract_text()
    # print(pl['text'])

    for c in chars:
        # ignore the empty word.
        if c['text'] == ' ':
            continue
        line = get_line_number(c, page.extract_words())
        if line is None:
            # pp.pprint(c)
            continue
        if line not in line_size:
            line_size[line] = c['size']
        teach = {'box': {'coordinateSpace': 'Image', 'coordinateSpaceOrigin': 'TopLeft'},
                 'class': 'CRTTextBox',
                 'needsReview': False,
                 'text': c['text'][0],
                 'type': 'Character'}
        tbox = teach['box']

        # resize the box with the size of character for visualization.
        tbox['point1'] = '{%f,%f}' % ((c['x0'] + c['size'] / 12) / width, (c['top'] + c['size'] / 8) / height)
        tbox['point2'] = '{%f,%f}' % ((c['x1'] - c['size'] / 12) / width, (c['top'] + c['size'] / 8) / height)
        tbox['point3'] = '{%f,%f}' % (
            (c['x1'] - c['size'] / 12) / width, (c['bottom'] - c['size'] / 13) / height)
        tbox['point4'] = '{%f,%f}' % (
            (c['x0'] + c['size'] / 12) / width, (c['bottom'] - c['size'] / 13) / height)
        pl['textBoxes'][line]['textBoxes'].append(teach)

    # join each character to get the line words.
    for i in range(len(pl['textBoxes'])):
        line = pl['textBoxes'][i]
        s = ''
        for word in line['textBoxes']:
            s += word['text']
        line['text'] = s
        if i in line_size:
            size = line_size[i]
        else:
            size = 0
        # change size option: 1/12, 1/8, 1/5
        a, b, c = 0, 0, 0
        line['box']['point1'] = '{%f,%f}' % (
        (line['box']['point1'][0] + size * a) / width, (line['box']['point1'][1] + size * b) / height)
        line['box']['point2'] = '{%f,%f}' % (
        (line['box']['point2'][0] - size * a) / width, (line['box']['point2'][1] + size * b) / height)
        line['box']['point3'] = '{%f,%f}' % (
        (line['box']['point3'][0] - size * a) / width, (line['box']['point3'][1] - size * c) / height)
        line['box']['point4'] = '{%f,%f}' % (
        (line['box']['point4'][0] + size * a) / width, (line['box']['point4'][1] - size * c) / height)

    with open(to_file, 'wb') as fp:
        plistlib.dump(pl, fp)


# convert pdf to plist and save according to page number.
def generate_plist(pdfPath):
    with pdfplumber.open(pdfPath) as pdf:
        page_count = len(pdf.pages)
        print(pdfPath, page_count)
        save_iamges(pdfPath, target_folder, page_count)
        for page in pdf.pages:
            try:
                process_page(pdfPath,page)
            except Exception as e:
                print('Error:'+str(e))


# get the line number of the character
def get_line_number(c,words):
    for i in range(len(words)):
        b = words[i]['bottom']
        t = words[i]['top']
        x0 = words[i]['x0']
        x1 = words[i]['x1']
        if (x0 <= c['x0'] <= x1 and x0 <= c['x1'] <= x1
                          and t <= c['top'] <= b and t <= c['bottom'] <= b):
            return i
    return None


if __name__ == '__main__':
    shellparser = argparse.ArgumentParser(description="CTPN Detector Test Options")

    shellparser.add_argument('-s', "--source_folder", dest='source_folder', action='store', required = True, help='The PDF Folder to convert')
    shellparser.add_argument('-t', '--target_folder', dest="target_folder", action='store', required = True, help="The Folder to store results")

    options = shellparser.parse_args()

    source_folder = options.source_folder
    if not os.path.exists(source_folder):
        raise OSError("PDF folder not exists: %s" % source_folder)

    target_folder = options.target_folder
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    for item in os.listdir(source_folder):
        if os.path.isfile(os.path.join(source_folder, item)) and item.endswith(".pdf"):
            try:
                pdf_path = os.path.join(source_folder, item)
                name = os.path.basename(pdf_path).split('.')[0]
                generate_plist(pdf_path)
                export_folder = target_folder+'/'+name
                success_image = export_folder + '/' + 'success'
                fail_image = export_folder + '/' + 'fail'
                image_files = glob(target_folder + '/*.' + 'png')
                for image_file in image_files:
                    process_image(image_file, target_folder, export_folder, success_image, fail_image)
            except Exception as e:
                print('Error:', item, e)
