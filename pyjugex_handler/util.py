import requests
import nibabel as nib
import os
import re
import tempfile

def get_pmap(url, json=None):
  '''
  given url as either a string or obj, interpretes, and performs get/post request
  returns resp
  may raise HTTP exception
  '''
  if json is None:
    resp = requests.get(url)
  else:
    resp = requests.post(url, json=json)

  resp.raise_for_status()
  return resp

def get_filename_from_resp(resp):
  # determine the type of the file. look at the disposition header, use PMapURL as a fallback
  content_disposition_header = resp.headers.get('content-disposition')
  filename = re.search(r'filename=(.*?)$', content_disposition_header).group(1) if content_disposition_header is not None and re.search(r'filename=(.*?)$', content_disposition_header) is not None else resp.url
  return filename

def read_byte_via_nib(content, gzip=False):
  fp, fp_name = tempfile.mkstemp(suffix='.nii.gz' if gzip else '.nii')
  os.write(fp, content)
  nii = nib.load(fp_name)
  os.close(fp)
  return nii

def is_gzipped(filename):
  return re.search(r"\.gz$", filename) is not None