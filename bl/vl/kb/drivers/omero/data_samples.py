# BEGIN_COPYRIGHT
# END_COPYRIGHT

from bl.vl.kb import mimetypes
import wrapper as wp
from action import Action, OriginalFile
from snp_markers_set import SNPMarkersSet
from utils import assign_vid_and_timestamp


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
    return assign_vid_and_timestamp(conf, time_stamp_field='creationDate')


class DataObject(OriginalFile):

  OME_TABLE = 'DataObject'
  __fields__ = [('sample', DataSample, wp.REQUIRED)]

  def __preprocess_conf__(self, conf):
    conf['name'] = conf['sample'].vid
    return conf

  @property
  def id(self):
    return '%s::%s' % (self.mimetype, self.omero_id)

  @property
  def vid(self):
    return self.id


class MicroArrayMeasure(DataSample):

  OME_TABLE = 'MicroArrayMeasure'
  __fields__ = []


class GenotypeDataSample(DataSample):

  OME_TABLE = 'GenotypeDataSample'
  __fields__ = [('snpMarkersSet', SNPMarkersSet, wp.REQUIRED)]

  def resolve_to_data(self, indices=None):
    dos = self.proxy.get_data_objects(self)
    if not dos:
      raise ValueError('no connected DataObject(s)')
    for do in dos:
      do.reload()
      if do.mimetype == mimetypes.GDO_TABLE:
        set_vid, vid, index = self.proxy.genomics.parse_gdo_path(do.path)
        mset = self.snpMarkersSet
        assert mset.id == set_vid
        mset.reload()
        res = self.proxy.genomics.get_gdo(mset, vid, index, indices=indices)
        return res['probs'], res['confidence']
    else:
      raise ValueError('DataObject is not a %s' % mimetypes.GDO_TABLE)
