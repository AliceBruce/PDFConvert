# -* - coding:utf-8 -*-
import os
from PIL import Image
from glob import glob
from plistlib import *
import numpy as np
import shutil
import argparse


def movefile(srcfile,dstpath):
    if not os.path.isfile(srcfile):
        print("%s not exist!"%(srcfile))
    else:
        if not os.path.exists(dstpath):
            os.makedirs(dstpath)
        shutil.move(srcfile,dstpath)


def process_image(image_file, source_folder, target_folder, success, fail):
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    if not os.path.exists(fail):
        os.makedirs(fail)
    if not os.path.exists(success):
        os.makedirs(success)
    image_name = image_file.split("/")[-1].split(".")[0]
    pdf_name = image_name.split('_')[-2]
    plistfile = image_name + ".plist"
    plist = os.path.join(source_folder, plistfile)
    try:
        if os.path.exists(plist):
            image = Image.open(image_file).convert('RGB')
            shape = np.array(image).shape
            with open(os.path.join(source_folder, plistfile), "rb") as pfile:
                pl = load(pfile)
                width = shape[1]
                height = shape[0]
                textBoxes = pl["textBoxes"]
                with open(os.path.join(target_folder, pdf_name+'.txt'), 'a') as f:
                    for (idx,box) in enumerate(textBoxes):
                        if box['box']['point1'].split(',')[0][1:] == 'inf':
                            continue
                        x0 = int(float(box['box']['point1'].split(',')[0][1:]) * width)
                        top = int(float(box['box']['point1'].split(',')[1][:-1]) * height)
                        x1 = int(float(box['box']['point2'].split(',')[0][1:]) * width)
                        bottom = int(float(box['box']['point3'].split(',')[1][:-1]) * height)
                        text = box['text']
                        imageName = image_name + '_%d'%idx
                        f.write(imageName + "卍" + text + "\n")
                        crop_file = os.path.join(target_folder,imageName+'.jpeg')
                        image.crop((x0, top, x1, bottom)).save(crop_file)
            movefile(image_file,success)
            movefile(plist,success)
    except Exception as e:
        print(e)
        movefile(image_file, fail)
        if os.path.exists(plist):
            movefile(plist, fail)


if __name__ == '__main__':
    shellparser = argparse.ArgumentParser(description="CTPN Detector Test Options")

    shellparser.add_argument('-s', "--source_folder", dest='source_folder', action='store', required = True, help='The PDF Folder to convert')
    shellparser.add_argument('-t', '--target_folder', dest="target_folder", action='store', required = True, help="The Folder to store results")

    options = shellparser.parse_args()

    source_folder = options.source_folder
    target_folder = options.target_folder

    if not os.path.exists(source_folder):
        raise OSError("PDF folder not exists: %s" % source_folder)

    success = '/Users/ocr/Documents/sucessimage'
    fail = '/Users/ocr/Documents/fail'
    image_files = glob(source_folder + '/*.' + 'png')
    for image_file in image_files:
        print(image_file)
        process_image(image_file,source_folder,target_folder,success,fail)




