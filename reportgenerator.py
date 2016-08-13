import os
import sys
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdftypes import resolve1
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter
import lxml.etree
# import gi as gi
# gi.require_version('GExiv2', '0.10')
# from gi.repository.GExiv2 import Metadata
from PIL import Image
import piexif
from fdfgen import forge_fdf
import subprocess
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Image
from reportlab.lib.utils import ImageReader
import urllib2
import shutil

from io import BytesIO
from pdfminer.pdftypes import LITERALS_DCT_DECODE
from pdfminer.pdfcolor import LITERAL_DEVICE_GRAY
from pdfminer.pdfcolor import LITERAL_DEVICE_RGB
from pdfminer.pdfcolor import LITERAL_DEVICE_CMYK

class MyImageWriter(object):
    def __init__(self, outdir):
        self.outdir = outdir
        self.jpgs = []
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
        return
    def get_jpgs(self):
        return self.jpgs
    def export_image(self, image):
        stream = image.stream
        filters = stream.get_filters()
        (width, height) = image.srcsize
        if len(filters) == 1 and filters[0][0] in LITERALS_DCT_DECODE:
            ext = '.jpg'
            self.jpgs.append(image.name+ext)
        elif (image.bits == 1 or
              image.bits == 8 and image.colorspace in (LITERAL_DEVICE_RGB, LITERAL_DEVICE_GRAY)):
            ext = '.%dx%d.bmp' % (width, height)
        else:
            ext = '.%d.%dx%d.img' % (image.bits, width, height)
        name = image.name+ext
        print name
        return name


"""
Get Server Data
"""
serverImageTags = ['SamplePhoto', 'QR', 'LabLogo', 'Signature']
serverData = {
                'Client': 'AB Buds',
                'Address': '1234 Magic Lane, Billings, MT 59102',
                'Email': 'austinbrown34@gmail.com',
                'Phone': '(406) 598-7345',
                'TotalTHC': '24%',
                'TotalCBD': '6%',
                'Moisture': 'N/A',
                'Footnote': 'Total THC = THCa * 0.877 + d9-THC\nTotal CBD = CBDa * 0.877 + CBD\nHPLC analysis; LOQ = Limit of Quantitation; The reported result is based on a sample weight with the applicable moisture content for that sample; Unless otherwise stated all quality control samples performed within specifications established by the Laboratory.',
                'LabAddress': '1111 Labway Place',
                'LabCityStateZip': 'Billings, MT 59101',
                'LabPhone': '(555) 555-5555',
                'LabEmail': 'email@lab.com',
                'SampleID': 'Sample 1607AHA0001.0001',
                'Strain': 'Strain: Sativa',
                'BatchNumber': 'Batch #: 100; Batch Size: 20 - grams',
                'ExpirationDate': 'rdered: 7/14/16; Sampled: 7/14/16; Completed: 7/14/16; Expires: 11/11/16',
                'SampleName': 'Test Sample',
                'Category': 'Plant, Flower - Cured, Outdoor',
                'SignatoryName': 'Mickey Mouse',
                'SignatoryTitle': 'Chief Resident Mouse',
                'Footer': 'This product has been tested by Advanced Herbal Analytics LLC using valid testing methodologies. Values reported relate only to the product tested. Advanced Herbal Analytics makes no claims as to the efficacy, safety or other risks associated with any detected or non-detected levels of any compounds reported herein. This Certificate shall not be reproduced except in full, without the written approval of Advanced Herbal Analytics.',
                'LabData': {
                    'thca': {
                        'loq': .01,
                        'mass1': 12.2,
                        'mass2': 122
                    },
                    'thcv': {
                        'loq': .01,
                        'mass1': 1.2,
                        'mass2': 12
                    },
                    'cbd': {
                        'loq': .01,
                        'mass1': 3.2,
                        'mass2': 32
                    }
                },
                'Images': {
                    'SamplePhoto': 'http://cogni.design/ccpics/weed.jpg',
                    'QR': 'http://cogni.design/ccpics/qr.jpg',
                    'LabLogo': 'http://cogni.design/ccpics/logo.jpg',
                    'Signature': 'http://cogni.design/ccpics/sig.jpg'
                }
            }

def get_acroform_fields(filename):
    fp = open(filename, 'rb')

    parser = PDFParser(fp)
    doc = PDFDocument(parser)
    field_names = []
    fields = resolve1(doc.catalog['AcroForm'])['Fields']
    for i in fields:
        field = resolve1(i)
        name, value = field.get('T'), field.get('V')
        # print '{0}: {1}'.format(name, value)
        field_names.append(name)
    return field_names

def set_image_tag(filename, tag):
    exif_ifd = {
                piexif.ExifIFD.UserComment: unicode(tag)
                }
    exif_dict = {"Exif":exif_ifd}
    exif_bytes = piexif.dump(exif_dict)
    im = Image.open(filename)
    im.save(filename, exif=exif_bytes)

def get_image_tag(filename):
    tag = None
    try:
        exif_dict = piexif.load(filename)
        if piexif.ExifIFD.UserComment in exif_dict['Exif']:
            print exif_dict['Exif'][piexif.ExifIFD.UserComment]
            tag = exif_dict['Exif'][piexif.ExifIFD.UserComment].strip(' \t\r\n\0')
    except Exception as e:
        print filename + " has an unsupported format --- setting tag to None"
        print "Error: " + str(e)
    return tag

def get_images(filename, jpg_names):
    pdf = file(filename, "rb").read()
    startmark = "\xff\xd8"
    startfix = 0
    endmark = "\xff\xd9"
    endfix = 2
    i = 0
    njpg = 0
    while True:
        istream = pdf.find("stream", i)
        if istream < 0:
            break
        istart = pdf.find(startmark, istream, istream+20)
        if istart < 0:
            i = istream+20
            continue
        iend = pdf.find("endstream", istart)
        if iend < 0:
            raise Exception("Didn't find end of stream!")
        iend = pdf.find(endmark, iend-20)
        if iend < 0:
            raise Exception("Didn't find end of JPG!")

        istart += startfix
        iend += endfix
        jpg = pdf[istart:iend]
        jpgfile = file('newstart/temp/' + jpg_names[njpg], "wb")
        jpgfile.write(jpg)
        jpgfile.close()
        njpg += 1
        i = iend

def get_placeholder_image_info(filename, xmlfile, outputdir):
    if not os.path.isdir(outputdir):
        os.makedirs(outputdir)

    image_info = []
    password = ''
    caching = True
    rotation = 0
    fname = filename
    maxpages = 0
    pagenos = set()
    outputdir = outputdir
    placeholder_imgs = []
    outfile = os.path.join(outputdir, xmlfile)
    outfp = file(outfile, 'w')
    codec = 'utf-8'
    laparams = LAParams()
    imagewriter = MyImageWriter(outputdir)
    # imagewriter = None
    rsrcmgr = PDFResourceManager(caching=caching)
    device = XMLConverter(rsrcmgr, outfp, codec=codec, laparams=laparams,
                          imagewriter=imagewriter)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    fp = file(fname, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    for page in PDFPage.get_pages(fp, pagenos,
                                  maxpages=maxpages, password=password,
                                  caching=caching, check_extractable=True):
        page.rotate = (page.rotate+rotation) % 360
        interpreter.process_page(page)

    fp.close()
    device.close()
    outfp.close()
    root = lxml.etree.parse(outfile)
    found_images = root.findall('.//image')
    found_image_boxes = root.xpath('.//figure[image]')
    jpg_count = 0
    get_images(filename, imagewriter.get_jpgs())
    for i, e in enumerate(found_images):
        imgpth = os.path.join(outputdir, found_image_boxes[i].attrib['name'] + '.jpg')
        print imgpth
        if not os.path.exists(imgpth):
            tag = None
        else:
            tag = get_image_tag(imgpth)
        image_info.append({
            "id": i,
            "src": imgpth,
            "height": e.attrib['height'],
            "width": e.attrib['width'],
            "bbox": found_image_boxes[i].attrib['bbox'],
            "tag": tag
            })
        if tag is not None:
            placeholder_imgs.append(jpg_count)
            jpg_count += 1
    return {'image_info': image_info, 'placeholder_imgs': placeholder_imgs}


def remove_all_images(filename, new_filename):
    args = [
        "gs",
        "-o",
        new_filename,
        "-sDEVICE=pdfwrite",
        "-dFILTERIMAGE",
        filename
        ]

    subprocess.call(args)

def repair_pdf(broke_pdf, fixed_pdf):
    call = [
            'pdftk',
            broke_pdf,
            'output',
            fixed_pdf
            ]

    subprocess.call(call)
def remove_placeholder_images(orig, newpdf, placeholder_imgs):
    pdf = file(orig, "rb").read()
    startmark = "\xff\xd8"
    startfix = 0
    endmark = "\xff\xd9"
    endfix = 2
    i = 0
    jpg_ranges = []
    njpg = 0
    mynewpdf = file(newpdf.replace('.pdf', '_temp.pdf'), "wb")
    while True:
        istream = pdf.find("stream", i)
        if istream < 0:
            break
        istart = pdf.find(startmark, istream, istream+20)
        if istart < 0:
            i = istream+20
            continue
        iend = pdf.find("endstream", istart)
        if iend < 0:
            raise Exception("Didn't find end of stream!")
        iend = pdf.find(endmark, iend-20)
        if iend < 0:
            raise Exception("Didn't find end of JPG!")

        istart += startfix
        iend += endfix
        if njpg in placeholder_imgs:
            jpg_ranges.append([njpg, istart, iend])
            jpg = pdf[istart:iend]
            jpgfile = file('newstart/temp/'"jpg%d.jpg" % njpg, "wb")
            jpgfile.write(jpg)
            jpgfile.close()
        njpg += 1
        i = iend

    placeholder = 0
    for jpg_item in jpg_ranges:
        range_start = jpg_item[1]
        range_end = jpg_item[2]
        mynewpdf.write(pdf[placeholder:range_start])
        counter = range_start
        while counter < range_end + 1:
            empty_bytes = bytes(1)
            mynewpdf.write(empty_bytes)
            counter += 1
        placeholder = range_end + 1
    mynewpdf.write(pdf[placeholder:sys.getsizeof(pdf)])
    mynewpdf.close()
    repair_pdf(newpdf.replace('.pdf', '_temp.pdf'), newpdf)
    # mynewpdf = file(newpdf, "rb").read()
    # print "size of orig:" + str(sys.getsizeof(pdf))
    # print "size of newpdf:" + str(sys.getsizeof(mynewpdf))


def generate_fdf(fields, data, fdfname):
    field_value_tuples = []
    for field in fields:
        field_value = (field, data[field])
        field_value_tuples.append(field_value)
    fdf = forge_fdf("", field_value_tuples, [], [], [])
    fdf_file = open(fdfname, "wb")
    fdf_file.write(fdf)
    fdf_file.close()


def fill_out_form(fdfname, template, filledname):
    # call = [
    #     'pdftk',
    #     template,
    #     'fill_form',
    #     fdfname,
    #     'output',
    #     filledname,
    #     'flatten'
    #     ]
    # check_output(call)

    call = [
            'pdftk',
            template,
            'fill_form',
            fdfname,
            'output',
            filledname,
            'flatten'
            ]

    subprocess.call(call)


def update_data_visualization(data_vis_name, data, dimensions, coordinates):
    with open(data_vis_name, 'r') as file:
        content = file.readlines()

    content[1] = str(data) + ';\n'
    content[3] = str(dimensions) + ';\n'
    content[5] = str(coordinates) + ';\n'

    with open(data_vis_name, 'w') as file:
        file.writelines(content)


def generate_visualizations(viz_files):
    for viz in viz_files:
        call = [
            'phantomjs',
            'report3.js',
            viz,
            'newstart/temp/' + viz.replace('html', 'pdf')
            ]
        subprocess.call(call)


def draw_images_on_pdf(images, currentpdf, pdf_with_images):
    first = True
    counter = 1
    temp_imgs = []
    completed_temps = []
    for image in images:
        c = canvas.Canvas('newstart/temp/tempimage' + str(counter) + '.pdf')
        c.drawImage(image['serversource'],
                    int(image['bbox'].split(',')[0].split('.')[0]),
                    int(image['bbox'].split(',')[1].split('.')[0]),
                    width=int(image['width']),
                    height=int(image['height']),
                    mask='auto')
        c.save()
        temp_imgs.append('newstart/temp/tempimage' + str(counter) + '.pdf')
        counter += 1
    counter = 1
    for tempimg in temp_imgs:
        print "tempimg: "
        print tempimg
        imagepdf = PdfFileReader(open(tempimg, 'rb'))
        output_file = PdfFileWriter()
        input_file = PdfFileReader(open(currentpdf, "rb"))
        page_count = input_file.getNumPages()
        for page_number in range(page_count):
            print "Watermarking page {} of {}".format(page_number, page_count)
            input_page = input_file.getPage(page_number)
            input_page.mergePage(imagepdf.getPage(0))
            output_file.addPage(input_page)
        with open('newstart/temp/temp' + str(counter) + '.pdf', "wb") as outputStream:
            output_file.write(outputStream)
            completed_temps.append('newstart/temp/temp' + str(counter) + '.pdf')
        currentpdf = 'newstart/temp/temp' + str(counter) + '.pdf'
        counter += 1

    os.rename(completed_temps[len(completed_temps) - 1], pdf_with_images)


def draw_visualization_on_pdf(vizs, currentpdf, pdf_with_vizs):
    counter = 1
    first = True
    for viz in vizs:
        if first is False:
            currentpdf = 'newstart/temp/temp' + str(counter - 1) + '.pdf'
        vizpdf = PdfFileReader(open(viz, "rb"))
        output_file = PdfFileWriter()
        input_file = PdfFileReader(open(currentpdf, "rb"))
        page_count = input_file.getNumPages()
        for page_number in range(page_count):
            print "Watermarking page {} of {}".format(page_number, page_count)
            input_page = input_file.getPage(page_number)
            input_page.mergePage(vizpdf.getPage(0))
            output_file.addPage(input_page)

        if counter == len(vizs):
            with open(pdf_with_vizs, "wb") as outputStream:
                output_file.write(outputStream)
        else:
            with open('newstart/temp/temp' + str(counter) + '.pdf', "wb") as outputStream:
                output_file.write(outputStream)

        counter += 1
        first = False


fields = get_acroform_fields('newstart/newstart.pdf')
print fields

all_image_data = get_placeholder_image_info('newstart/newstart.pdf', 'newstart.xml', 'newstart/temp')
image_info = all_image_data['image_info']
placeholder_imgs = all_image_data['placeholder_imgs']
print image_info

###
fielddata = {}
for i in fields:
    fielddata[i] = serverData[i]
###

generate_fdf(fields, fielddata, 'newstart/temp/newstart.fdf')

fill_out_form('newstart/temp/newstart.fdf', 'newstart/newstart.pdf', 'newstart/temp/newstart_filled.pdf')

print "Placeholders: " + str(placeholder_imgs)

remove_placeholder_images('newstart/temp/newstart_filled.pdf', 'newstart/temp/newstart_filled_noplaceholders.pdf', placeholder_imgs)
# remove_all_images('datatest_filled.pdf', 'datatest_noimages.pdf')

DTdata = []
DTdimensions = []
DTcoords = []
SLdata = []
SLdimensions = []
SLcoords = []

for analyte in serverData['LabData']:
    DTdata.append([analyte, serverData['LabData'][analyte]['loq'], serverData['LabData'][analyte]['mass1'], serverData['LabData'][analyte]['mass2']])
    SLdata.append(serverData['LabData'][analyte]['mass2'])

###

serverImages = []

for image in image_info:
    img_spec = image
    if img_spec['tag'] == 'DataTable':
        DTdimensions = [int(img_spec['width']), int(img_spec['height'])]
        x = img_spec['bbox'].split(",")[0].split('.')[0]
        y = img_spec['bbox'].split(",")[1].split('.')[0]
        DTcoords = [int(x), int(y)]
    if img_spec['tag'] == 'SparkLine':
        SLdimensions = [int(img_spec['width']), int(img_spec['height'])]
        x = img_spec['bbox'].split(",")[0].split('.')[0]
        y = img_spec['bbox'].split(",")[1].split('.')[0]
        SLcoords = [int(x), int(y)]
    if img_spec['tag'] in serverImageTags:
        ext = '.' + serverData['Images'][img_spec['tag']].split(".")[-1]
        remote_file = urllib2.urlopen(serverData['Images'][img_spec['tag']])
        with open('newstart/temp/' + img_spec['tag'] + ext, 'wb') as local_file:
            shutil.copyfileobj(remote_file, local_file)
        img_spec['serversource'] = 'newstart/temp/' + img_spec['tag'] + ext
        serverImages.append(img_spec)

###

update_data_visualization('datatable.js', DTdata, DTdimensions, DTcoords)
update_data_visualization('sparkline.js', SLdata, SLdimensions, SLcoords)

vizfiles = ['datatable.html', 'sparkline.html']
vizpdfs = ['newstart/temp/datatable.pdf', 'newstart/temp/sparkline.pdf']
generate_visualizations(vizfiles)

draw_images_on_pdf(serverImages, 'newstart/temp/newstart_filled_noplaceholders.pdf', 'newstart/temp/newstart_filled_with_images.pdf')

draw_visualization_on_pdf(vizpdfs, 'newstart/temp/newstart_filled_with_images.pdf', 'newstart/newstart_complete.pdf')

args = ['aws', 's3', 'cp', 'newstart/newstart_complete', 's3://pdfserver']

subprocess.call(args)
