from PIL import Image
import piexif


def set_image_tag(filename, tag):
    exif_ifd = {
                piexif.ExifIFD.UserComment: tag.encode('UTF-8')
                }
    exif_dict = {"Exif": exif_ifd}
    exif_bytes = piexif.dump(exif_dict)
    im = Image.open(filename)
    im.save(filename, exif=exif_bytes)


set_image_tag('placeholders/sparkline_placeholder.jpg', u'SparkLine')

set_image_tag('placeholders/datatable_placeholder.jpg', u'DataTable')

set_image_tag('placeholders/samplephoto_placeholder.jpg', u'SamplePhoto')

set_image_tag('placeholders/qr_placeholder.jpg', u'QR')

set_image_tag('placeholders/lablogo_placeholder.jpg', u'LabLogo')

set_image_tag('placeholders/signature_placeholder.jpg', u'Signature')
