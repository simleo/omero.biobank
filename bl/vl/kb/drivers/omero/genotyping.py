import time
import bl.vl.utils as vlu
import itertools as it
import numpy     as np


class GenotypingAdapter(object):
  """
  FIXME
  """
  SNP_MARKER_DEFINITIONS_TABLE = 'snp_marker_definitions.h5'
  SNP_ALIGNMENT_TABLE  = 'snp_alignment.h5'
  SNP_SET_DEF_TABLE    = 'snp_set_def.h5'
  SNP_SET_TABLE        = 'snp_set.h5'

  SNP_MARKER_DEFINITIONS_COLS = \
  [('string', 'vid',    'This marker VID', len(vlu.make_vid()), None),
   ('string', 'source', 'Origin of this marker definition.', 16, None),
   ('string', 'context', 'Context of definition.', 16, None),
   ('string', 'release', 'Release within the context.', 16, None),
   ('string', 'label', 'Label of marker in the definition context.', 16, None),
   ('string', 'rs_label', 'dbSNP_id if available', 16, None),
   ('string', 'mask', 'SNP definition mask in the format <FLANK>[A/B]<FLANK>', 69, None),
   ('string', 'op_vid', 'Last operation that modified this row',
    len(vlu.make_vid()), None)]

  SNP_ALIGNMENT_COLS = \
  [('string', 'marker_vid', 'VID of the aligned marker.', len(vlu.make_vid()), None),
   ('string', 'ref_genome', 'Reference alignment genome.', 16, None),
   ('long', 'chromosome',
    'Chromosome where this alignment was found. 1-22, 23(X) 24(Y)', None),
   ('long', 'pos', "Position on the chromosome. Starting from 5'", None),
   ('long', 'global_pos', "Global position in the genome. (chr*10**10 + pos)", None),
   ('bool', 'strand', 'Aligned on reference strand', None),
   # I know that this is in principle a bool, but what happens if we have more than two alleles?
   ('string', 'allele', 'Allele found at this position (A/B)', 1, None),
   ('long', 'copies', "Number of copies found for this marker within this alignment op.", None),
   ('string', 'op_vid', 'Last operation that modified this row', len(vlu.make_vid()), None)]

  SNP_SET_COLS = \
  [('string', 'vid', 'Set VID', len(vlu.make_vid()), None),
   ('string', 'marker_vid', 'Marker VID', len(vlu.make_vid()), None),
   ('long', 'marker_indx',
    "Ordered position of this marker within the set", None),
   ('bool', 'allele_flip',
    'Is this technology flipping our A/B allele convention?', None),
   ('string', 'op_vid',
    'Last operation that modified this row', len(vlu.make_vid()), None)]

  SNP_SET_DEF_COLS = \
  [('string', 'vid', 'Set VID', len(vlu.make_vid()), None),
   ('string', 'maker', 'Maker identifier.', 32, None),
   ('string', 'model', 'Model identifier.', 32, None),
   ('string', 'release', 'Release identifier.', 32, None),
   ('string', 'op_vid', 'Last operation that modified this row',
    len(vlu.make_vid()), None)]

  @classmethod
  def SNP_GDO_REPO_COLS(klass, N):
    cols = [('string', 'vid', 'gdo VID', len(vlu.make_vid()), None),
            ('string', 'op_vid', 'Last operation that modified this row',
             len(vlu.make_vid()), None),
            ('string', 'probs', 'np.zeros((2,N), dtype=np.float32).tostring()',
             2*N*4, None),
            ('string', 'confidence', 'np.zeros((N,), dtype=np.float32).tostring()',
             N*4, None)]
    return cols

  def __init__(self, kb):
    self.kb = kb

  #-- markers definitions
  def create_snp_marker_definitions_table(self):
    self.kb.create_table(self.SNP_MARKER_DEFINITIONS_TABLE,
                         self.SNP_MARKER_DEFINITIONS_COLS)

  def add_snp_marker_definitions(self, stream, op_vid, batch_size=50000):
    vids = []
    def add_vid_filter_and_op_vid(stream, op_vid):
      for x in stream:
        x['vid'] = vlu.make_vid()
        x['op_vid'] = op_vid
        vids.append(x['vid'])
        yield x
    i_s = add_vid_filter_and_op_vid(stream, op_vid)
    self.kb.add_table_rows_from_stream(self.SNP_MARKER_DEFINITIONS_TABLE,
                                       i_s, batch_size)
    return vids

  def get_snp_marker_definitions(self, selector=None, batch_size=50000):
    """
    selector = "(source == 'affymetrix') & (context == 'GW6.0')"
    """
    return self.kb.get_table_rows(self.SNP_MARKER_DEFINITIONS_TABLE,
                                  selector, batch_size)

  #-- marker sets
  def create_snp_markers_set_table(self):
    self.kb.create_table(self.SNP_SET_DEF_TABLE, self.SNP_SET_DEF_COLS)

  def create_snp_set_table(self):
    self.kb.create_table(self.SNP_SET_TABLE, self.SNP_SET_COLS)

  def snp_markers_set_exists(self, maker, model, release='1.0'):
    selector = ("(maker=='%s') & (model=='%s') & (release=='%s')" %
                (maker, model, release))
    if len(self.get_snp_markers_sets(selector)) > 0 :
      return True
    return False

  def add_snp_markers_set(self, maker, model, release, op_vid):
    if self.snp_markers_set_exists(maker, model, release):
      raise ValueError('SNP_MARKERS_SET(%s, %s, %s) is already in kb.' %
                       (maker, model, release))
    set_vid = vlu.make_vid()
    row = {'vid':set_vid, 'maker': maker, 'model' : model, 'release' : release,
           'op_vid':op_vid}
    self.kb.add_table_row(self.SNP_SET_DEF_TABLE, row)
    return set_vid

  def get_snp_markers_sets(self, selector=None, batch_size=50000):
    return self.kb.get_table_rows(self.SNP_SET_DEF_TABLE, selector, batch_size)

  def fill_snp_markers_set(self, set_vid, stream, op_vid, batch_size=50000):
    def add_op_vid(stream, N):
      for x in stream:
        x['vid'], x['op_vid'] = set_vid, op_vid
        N[0] += 1
        yield x
    N = [0]
    i_s = add_op_vid(stream, N)
    self.kb.add_table_rows_from_stream(self.SNP_SET_TABLE, i_s, batch_size)
    return N[0]

  def get_snp_markers_set(self, selector=None, batch_size=50000):
    return self.kb.get_table_rows(self.SNP_SET_TABLE, selector, batch_size)

  #-- alignment
  def create_snp_alignment_table(self):
    self.kb.create_table(self.SNP_ALIGNMENT_TABLE, self.SNP_ALIGNMENT_COLS)

  def add_snp_alignments(self, stream, op_vid, batch_size=50000):
    def add_op_vid(stream):
      for x in stream:
        x['op_vid'] = op_vid
        yield x
    i_s = add_op_vid(stream)
    return self.kb.add_table_rows_from_stream(self.SNP_ALIGNMENT_TABLE,
                                              i_s, batch_size)

  def get_snp_alignments(self, selector=None, batch_size=50000):
    return self.kb.get_table_rows(self.SNP_ALIGNMENT_TABLE, selector,
                                  batch_size)

  #-- gdo
  def _gdo_table_name(self, set_vid):
    return '%s.h5' % set_vid

  def create_gdo_repository(self, set_vid, N):
    table_name = self._gdo_table_name(set_vid)
    self.kb.create_table(table_name, self.SNP_GDO_REPO_COLS(N))
    return set_vid

  def add_gdo(self, set_vid, probs, confidence, op_vid):
    pstr = probs.tostring()
    cstr = confidence.tostring()
    assert len(pstr) == 2*len(cstr)
    #--
    table_name = self._gdo_table_name(set_vid)
    row = {'vid' : vlu.make_vid(), 'op_vid' : op_vid,
           'probs' :  pstr, 'confidence' : cstr}
    self.kb.add_table_row(table_name, row)
    # return (vid, mimetype, path)
    return (table_name, row['vid'])

  def __normalize_size(self, string, size):
    return string + chr(0) * (size - len(string))

  def __unwrap_gdo(self, set_id, row):
    r = {'vid' :  row['vid'], 'op_vid' : row['op_vid'], 'set_id' : set_id}
    #--
    p = np.fromstring(self.__normalize_size(row['probs'],
                                            row.dtype['probs'].itemsize),
                      dtype=np.float32)
    p.shape = (2, p.shape[0]/2)
    r['probs'] = p
    #--
    c = np.fromstring(self.__normalize_size(row['confidence'],
                                            row.dtype['confidence'].itemsize),
                      dtype=np.float32)
    r['confidence'] = c
    #--
    return r

  def get_gdo(self, set_vid, vid):
    table_name = self._gdo_table_name(set_vid)
    rows = self.kb.get_table_rows(table_name, selector='(vid == "%s")' % vid)
    assert len(rows) == 1
    return self.__unwrap_gdo(set_vid, rows[0])

  def get_gdo_iterator(self, set_vid, batch_size=100):
    def iterator(stream):
      for d in stream:
        yield self.__unwrap_gdo(set_vid, d)
    table_name = self._gdo_table_name(set_vid)
    return iterator(self.kb.get_table_rows_iterator(table_name, batch_size))