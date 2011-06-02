import wrapper as wp

from action import Action, assing_vid_and_timestamp

class DataSampleStatus(wp.OmeroWrapper):
  OME_TABLE = 'DataSampleStatus'
  __enums__ = ["UNKNOWN", "DESTROYED", "CORRUPTED", "USABLE"]


class DataSample(wp.OmeroWrapper):
  OME_TABLE = 'DataSample'
  __fields__ = [('vid', wp.VID, wp.REQUIRED),
                ('label', wp.STRING, wp.REQUIRED),
                ('creationDate', wp.TIMESTAMP, wp.REQUIRED),
                ('status', DataSampleStatus, wp.REQUIRED),
                ('action', Action, wp.REQUIRED)]

  def __preprocess_conf__(self, conf):
    return assing_vid_and_timestamp(conf, time_stamp_field='creationDate')


class DataObject(wp.OmeroWrapper):
  OME_TABLE = 'DataObject'
  __fields__ = [('sample', DataSample, wp.REQUIRED),
                 # following fields come from OriginalFile
                ('name',   wp.STRING,  wp.REQUIRED),
                ('path',   wp.STRING,  wp.REQUIRED),
                ('mimetype', wp.STRING, wp.REQUIRED),
                ('sha1',   wp.STRING, wp.REQUIRED),
                ('size',   wp.LONG,    wp.REQUIRED)]

  def __preprocess_conf__(self, conf):
    conf['name'] = conf['sample'].vid
    return conf

class GenotypingMeasure(DataSample):
  OME_TABLE = 'GenotypingMeasure'
  __fields__ = []

class AffymetrixCelArrayType(wp.OmeroWrapper):
  OME_TABLE="AffymetrixCelArrayType"
  __enums__ = ["UNKNOWN", "GenomeWideSNP_6"]

class AffymetrixCel(GenotypingMeasure):
  OME_TABLE = 'AffymetrixCel'
  __fields__ = [('arrayType', AffymetrixCelArrayType, wp.REQUIRED),
                ('celID',     wp.STRING,              wp.OPTIONAL)]







