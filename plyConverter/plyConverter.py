#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
from PIL import Image
import import_ply

class plyConverter:
    def __init__(self, width, height):
        self._width = width
        self._height = height

    def ply2Img(self, path_plyIn, imgDir):
        list_xyz, list_rgb = self._readPly(path_plyIn)
        im_size = (self._width, self._height)

        im_rgb = self._createImg(list_rgb, "RGB", im_size)
        im_xyz = self._createImg(list_xyz, "RGB", im_size)

        cloudID = path_plyIn.split('/')[-1].strip('.ply').strip('cloud').zfill(4) # zero padding
        #self._saveImg(im_rgb, "rgb", imgDir, cloudID)
        self._saveImg(im_xyz, "xyz", imgDir, cloudID, use_lossless=True)

    def _readPly(self, filePath):
        obj_spec, obj, texture = import_ply.read(filePath)
        obj_out = [ e[1] for e in obj.items() ]

        list_xyz, list_rgb = self._getData(obj_out[0])
        return list_xyz, list_rgb

    def _getData(self, obj): # return 2 lists of tuples pixels (compliant with PIL format for image creation)
        min_x = -6.0
        max_x = 6.0
        min_y = -5.0
        max_y = 5.0
        min_z = 0.5
        max_z = 8.0

        range_x = 256.0 / (max_x - min_x)
        range_y = 256.0 / (max_y - min_y)
        range_z = 256.0 / (max_y - min_z)

        l_xyz = []
        l_rgb = []
        for i in obj:
            x = (i[0] - min_x) * range_x
            y = (i[1] - min_y) * range_y
            z = (i[2] - min_z) * range_z
            l_xyz.append((int(x), int(y), int(z)))
            l_rgb.append((i[3], i[4], i[5]))

        return l_xyz, l_rgb

    def _createImg(self, imgData, mode, size):

        # create and display image
        im = Image.new(mode, size)
        im.putdata(imgData)
        # im.getExtrema()
        return im

    def _saveImg(self, img, imgType, outDir, prefix, use_lossless=False):

        imgDir_path = os.path.join(outDir, imgType)
        if not os.path.exists(imgDir_path):
            os.makedirs(imgDir_path) # create image dir next to /cloud..

        if use_lossless:
            img_path = os.path.join(imgDir_path, prefix + ".webp")
            img.save(img_path, lossless=True)
        else:
            img_path = os.path.join(imgDir_path, prefix + ".tga")
            # print(img_path)
            img.save(img_path)


def getFileList(basedir, suffix):
    # return list of files in basedir ending with "suffix"
    fileList = []
    for file in os.listdir(basedir):
        if file.endswith(suffix):
           fileList.append(file)
    return fileList

def progress_bar(item_count, total_count):
   """
   Show text progress bar in the console.
   """
   item_count += 2  # usually counter starts at 0 and is updated after the this call => add 2 to all item_count
   progress = int(item_count / total_count * 100)
   if progress > 100:
       progress = 100  # to ensure the counter stops at 100%

   print('\r{0}%\t[{1}{2}]'.format(progress, '#'*(progress//2), ' '*(50-(progress//2))), sep=' ', end='')
   # \r to rewind cursor


if __name__ == '__main__':

    # Set cloud file name (has to be stored in ../data/)
    cloudDirName = "cloud09-06-2015-stool"

    # Define paths
    basedirScript = os.path.split(os.path.realpath(__file__))
    dataDir = os.path.join(os.path.split(basedirScript[0])[0], "data")

    baseCloudDir = os.path.join(dataDir, cloudDirName)
    baseImgDir = os.path.join(dataDir, cloudDirName + 'img')

    if not os.path.exists(baseImgDir):
        os.makedirs(baseImgDir) # create image dir in /cloud../
    print("Converting .ply files from :\n", baseCloudDir, "to: \n", baseImgDir, '\n')

    # instantiate ply Converter, get ply files
    plyC = plyConverter(512//2, 424//2)
    plyFylesList = getFileList(baseCloudDir, '.ply')

    # # single ply to image convert test
    # path_plyIn = baseCloudDir + '/' + plyFylesList[0]
    # plyC.ply2Img(path_plyIn, baseImgDir)

    # ply to image conversion
    for index, plyFiles in enumerate(plyFylesList):
        path_plyIn = baseCloudDir + '/' + plyFylesList[index]
        plyC.ply2Img(path_plyIn, baseImgDir)
        progress_bar(index,len(plyFylesList))



# The tricky part is:
# you need to store only the depth in the image
# so you need to calculate the depth for a given pixel

### Handy fonctions ###

## round
# obj = [[ round(elem, 2) for elem in obj_item ] for obj_item in obj]

## sort by x[0] then -x[1]
# obj_sort = sorted(obj, key = lambda x : (x[0], -x[1]))

