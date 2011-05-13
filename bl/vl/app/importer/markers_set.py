"""
Import Markers Set Definitions
=============================

Will read in a tsv file with the following columns::

  rs_label   marker_indx allele_flip
  rs6576700  0            False
  rs6576701  1            False
  rs6576702  2            True
  ...

importer -i taqman.tsv markers_set --maker='CRS4' --model='TaqMan.ms01' --release='1'

"""

from bl.vl.sample.kb import KBError
from core import Core, BadRecord
from version import version

import csv, json
import time, sys
import itertools as it

#-----------------------------------------------------------------------------
#FIXME this should be factored out....

import logging, time
logger = logging.getLogger()
counter = 0
def debug_wrapper(f):
  def debug_wrapper_wrapper(*args, **kv):
    global counter
    now = time.time()
    counter += 1
    logger.debug('%s[%d] in' % (f.__name__, counter))
    res = f(*args, **kv)
    logger.debug('%s[%d] out (%f)' % (f.__name__, counter, time.time() - now))
    counter -= 1
    return res
  return debug_wrapper_wrapper
#-----------------------------------------------------------------------------

class Recorder(Core):
  """
  An utility class that handles the actual recording of marker definitions
  into VL.
  """
  def __init__(self, study_label,
               host=None, user=None, passwd=None, keep_tokens=1,
               operator='Alfred E. Neumann'):
    """
    FIXME
    """
    self.logger = logger
    super(Recorder, self).__init__(host, user, passwd)
    #--
    s = self.skb.get_study_by_label(study_label)
    if not s:
      self.logger.critical('No known study with label %s' % study_label)
      sys.exit(1)
    self.study = s
    #-------------------------
    self.device = self.get_device('importer-0.0', 'CRS4', 'IMPORT', '0.0')
    self.asetup = self.get_action_setup('importer-version-%s-%s-%f' %
                                        (version, "SNPMarkersSet", time.time()),
                                        # FIXME the json below should
                                        # record the app version, and the
                                        # parameters used.  unclear if we
                                        # need to register the file we load
                                        # data from, since it is, most
                                        # likely, a transient object.
                                        json.dumps({'operator' : operator,
                                                    'host' : host,
                                                    'user' : user}))
    self.acat  = self.acat_map['IMPORT']
    self.operator = operator

  def create_action(self, description):
    return self.create_action_helper(self.skb.Action, description,
                                     self.study, self.device, self.asetup,
                                     self.acat, self.operator, None)


  def save_snp_markers_set(self, maker, model, release, ifile):
    if self.gkb.snp_markers_set_exists(maker, model, release):
      self.logger.warn('markers_set (%s,%s,%s) is already in kb, not loading.' %
                       (maker, model, release))
      return
    #--
    self.logger.info('start loading from %s' % ifile.name)
    tsv = csv.DictReader(ifile, delimiter='\t')
    #-
    records = [x for x in tsv]
    rs_labels = [x['rs_label'] for x in records]
    #-
    self.logger.info('done loading')
    #-
    self.logger.info('start preloading related markers')
    selector = '|'.join(["(rs_label == '%s')" % k for k in rs_labels])
    markers = self.gkb.get_snp_marker_definitions(selector=selector)
    if len(markers) != len(records):
      self.logger.warn('no enough markers defined in kb, not loading.')
      return
    rs_to_vid = dict([ x for x in it.izip(markers['rs_label'], markers['vid'])])
    self.logger.info('done preloading related markers')
    #--
    pars = {'maker' : maker, 'model': model, 'release' : release,
            'filename' : ifile.name}
    action = self.create_action(description=json.dumps(pars))
    #--
    self.logger.info('start creating markers set')
    set_vid = self.gkb.add_snp_markers_set(maker, model, release, action.id)
    self.logger.info('done creating markers set')
    #--
    self.logger.info('start loading markers in marker set')
    def snp_set_item(records):
      for x in records:
        x['marker_vid'] = rs_to_vid[x['rs_label']]
        x['allele_flip'] = {'False' : False, 'True' : True}[x['allele_flip']]
        x['marker_indx'] = int(x['marker_indx'])
        yield x
    n = self.gkb.fill_snp_markers_set(set_vid, snp_set_item(records), action.id)
    assert n == len(records)
    self.logger.info('done loading markers in marker set')
    #--
    self.logger.info('start creating gdo repository')
    self.gkb.create_gdo_repository(set_vid, len(records))
    self.logger.info('done creating gdo repository')
    #--
    self.logger.info('start creating SNPMarkersSet')
    snp_markers_set = self.skb.SNPMarkersSet(maker=maker, model=model, release=release,
                                             set_vid=set_vid)
    snp_markers_set.action = action
    snp_markers_set = self.skb.save(snp_markers_set)
    self.logger.info('done creating SNPMarkersSet')
    #--

#------------------------------------------------------------------------------------

help_doc = """
import new markers set definition into VL.
"""

def make_parser_markers_set(parser):
  parser.add_argument('-S', '--study', type=str,
                      help="""context study label""")
  parser.add_argument('--maker', type=str,
                      help="""markers_set maker""")
  parser.add_argument('--model', type=str,
                      help="""markers_set model""")
  parser.add_argument('--release', type=str,
                      help="""markers set release""")

def import_markers_set_implementation(args):
  if not (args.study and args.maker and args.model and args.release):
    msg = 'missing command line options'
    logger.critical(msg)
    sys.exit(1)
  #--
  recorder = Recorder(args.study,
                      host=args.host, user=args.user, passwd=args.passwd,
                      keep_tokens=args.keep_tokens)
  recorder.save_snp_markers_set(args.maker, args.model, args.release,
                                args.ifile)

def do_register(registration_list):
  registration_list.append(('markers_set', help_doc,
                            make_parser_markers_set,
                            import_markers_set_implementation))

