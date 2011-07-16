import omero.rtypes as ort

import bl.vl.sample.kb as kb

from bl.vl.sample.kb.drivers.omero.sample import DataSample
from bl.vl.sample.kb.drivers.omero.result import Result

import bl.vl.utils.ome_utils as vluo

#------------------------------------------------------------
class AffymetrixCel(DataSample, kb.AffymetrixCel):

  OME_TABLE = "AffymetrixCel"

  LEGAL_ARRAY_TYPES = ['GenomeWideSNP_6']

  def __setup__(self, ome_obj, label, array_type, data_type, **kw):
    if label is None or array_type is None or data_type is None:
      raise ValueError('AffymetrixCel label, array_type and data_type cannot be None')
    if not array_type in self.LEGAL_ARRAY_TYPES:
      raise ValueError('%s not in %s' % (array_type, self.LEGAL_ARRAY_TYPES))
    ome_obj.arrayType = ort.rstring(array_type)
    super(AffymetrixCel, self).__setup__(ome_obj, label, data_type, **kw)

  def __init__(self, from_=None, label=None, array_type=None,
               data_type=None, **kw):
    ome_type = self.get_ome_type()
    if not from_ is None:
      ome_obj = from_
    else:
      ome_obj = ome_type()
      self.__setup__(ome_obj, label, array_type, data_type, **kw)
    super(AffymetrixCel, self).__init__(ome_obj, **kw)

  def __handle_validation_errors__(self):
    if self.arrayType is None:
      raise kb.KBError("AffymetrixCel array_type can't be None")
    else:
      super(AffymetrixCel, self).__handle_validation_errors__()

#------------------------------------------------------------
class SNPMarkersSet(Result, kb.SNPMarkersSet):

  OME_TABLE = "SNPMarkersSet"

  def __setup__(self, ome_obj, maker, model, release, set_vid, **kw):
    if maker is None or model is None or release is None or set_vid is None:
      raise ValueError("SNPMarkersSet maker, model, set_vid cannot be None")
    ome_obj.maker = ort.rstring(maker)
    ome_obj.model = ort.rstring(model)
    ome_obj.release = ort.rstring(release)
    ome_obj.markersSetVID = ort.rstring(set_vid)
    ome_obj.snpMarkersSetUK = vluo.make_unique_key(maker, model, release)
    super(SNPMarkersSet, self).__setup__(ome_obj, **kw)

  def __init__(self, from_=None, maker=None, model=None, release=None,
               set_vid=None, **kw):
    ome_type = self.get_ome_type()
    if not from_ is None:
      ome_obj = from_
    else:
      ome_obj = ome_type()
      self.__setup__(ome_obj, maker, model, release, set_vid, **kw)
    super(SNPMarkersSet, self).__init__(ome_obj, **kw)

  def __handle_validation_errors__(self):
    if self.maker is None:
      raise kb.KBError("SNPMarkersSet maker can't be None")
    elif self.model is None:
      raise kb.KBError("SNPMarkersSet model can't be None")
    elif self.release is None:
      raise kb.KBError("SNPMarkersSet release can't be None")
    elif self.markersSetVID is None:
      raise kb.KBError("SNPMarkersSet marksersSetVID can't be None")
    else:
      super(SNPMarkersSet, self).__handle_validation_errors__()

  def __setattr__(self, name, value):
    if name == 'maker':
      setattr(self.ome_obj, 'snpMarkersSetUK',
              vluo.make_unique_key(value, self.model, self.release))
      return super(SNPMarkersSet, self).__setattr__(name, value)
    elif name == 'model':
      setattr(self.ome_obj, 'snpMarkersSetUK',
              vluo.make_unique_key(self.maker, value, self.release))
      return super(SNPMarkersSet, self).__setattr__(name, value)
    elif name == 'release':
      setattr(self.ome_obj, 'snpMarkersSetUK',
              vluo.make_unique_key(self.maker, self.model, value))
      return super(SNPMarkersSet, self).__setattr__(name, value)
    else:
      return super(SNPMarkersSet, self).__setattr__(name, value)


#------------------------------------------------------------
class GenotypeDataSample(DataSample, kb.GenotypeDataSample):

  OME_TABLE = "GenotypeDataSample"

  def __setup__(self, ome_obj, label, snp_markers_set, data_type, **kw):
    if label is None or snp_markers_set is None or data_type is None:
      raise ValueError('GenotypeDataSample label, snp_markers_set and data_type cannot be None')
    ome_obj.snpMarkersSet = snp_markers_set.ome_obj
    super(GenotypeDataSample, self).__setup__(ome_obj, label, data_type, **kw)

  def __init__(self, from_=None, label=None, snp_markers_set=None, data_type=None, **kw):
    ome_type = self.get_ome_type()
    if not from_ is None:
      ome_obj = from_
    else:
      ome_obj = ome_type()
      self.__setup__(ome_obj, label, snp_markers_set, data_type, **kw)
    super(GenotypeDataSample, self).__init__(ome_obj, **kw)

  def __handle_validation_errors__(self):
    if self.snpMarkersSet is None:
      raise kb.KBError("GenotypeDataSample snpMarkersSet  can't be None")
    else:
      super(GenotypeDataSample, self).__handle_validation_errors__()

  def __setattr__(self, name, value):
    if name == 'snpMarkersSet':
      return setattr(self.ome_obj, name, value.ome_obj)
    else:
      return super(GenotypeDataSample, self).__setattr__(name, value)


  def __getattr__(self, name):
    if name == 'snpMarkersSet':
      return SNPMarkersSet(getattr(self.ome_obj, name), proxy=self.proxy)
    else:
      return super(GenotypeDataSample, self).__getattr__(name)