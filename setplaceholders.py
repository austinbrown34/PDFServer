from PIL import Image
import piexif


def set_image_tag(filename, tag):
    exif_ifd = {
                piexif.ExifIFD.UserComment: unicode(tag)
                }
    exif_dict = {"Exif": exif_ifd}
    exif_bytes = piexif.dump(exif_dict)
    im = Image.open(filename)
    im.save(filename, exif=exif_bytes)


set_image_tag('placeholders/sparkline_placeholder.jpg', 'SparkLine')

set_image_tag('placeholders/datatable_placeholder.jpg', 'DataTable')

set_image_tag('placeholders/samplephoto_placeholder.jpg', 'SamplePhoto')

set_image_tag('placeholders/qr_placeholder.jpg', 'QR')

set_image_tag('placeholders/lablogo_placeholder.jpg', 'LabLogo')

set_image_tag('placeholders/signature_placeholder.jpg', 'Signature')
