import sys, logging, csv, os, subprocess, multiprocessing, platform
from Bio import SeqIO

ASCII = {'!':'0','"':'1','#':'2','$':'3','%':'4','&':'5',"'":'6','(':'7',')':'8','*':'9','+':'10',',':'11','-':'12','.':'13','/':'14','0':'15','1':'16','2':'17','3':'18','4':'19','5':'20','6':'21','7':'22','8':'23','9':'24',':':'25',';':'26','<':'27','=':'28','>':'29','?':'30','@':'31','A':'32','B':'33','C':'34','D':'35','E':'36','F':'37','G':'38','H':'39','I':'40','J':'41','K':'42','L':'43','M':'44','N':'45','O':'46','P':'47','Q':'48','R':'49','S':'50'}

primer_db = {'fITS7': 'GTGARTCATCGAATCTTTG', 'ITS4': 'TCCTCCGCTTATTGATATGC', 'ITS1-F': 'CTTGGTCATTTAGAGGAAGTAA', 'ITS2': 'GCTGCGTTCTTCATCGATGC', 'ITS3': 'GCATCGATGAAGAACGCAGC', 'ITS4-B': 'CAGGAGACTTGTACACGGTCCAG', 'ITS1': 'TCCGTAGGTGAACCTGCGG', 'LR0R': 'ACCCGCTGAACTTAAGC', 'LR2R': 'AAGAACTTTGAAAAGAG', 'JH-LS-369rc': 'CTTCCCTTTCAACAATTTCAC', '16S_V3': 'CCTACGGGNGGCWGCAG', '16S_V4': 'GACTACHVGGGTATCTAATCC', 'ITS3_KYO2': 'GATGAAGAACGYAGYRAA', 'COI-F': 'GGTCAACAAATCATAAAGATATTGG', 'COI-R': 'GGATTTGGAAATTGATTAGTWCC'}

class colr:
    GRN = '\033[92m'
    END = '\033[0m'
    WARN = '\033[93m'

def myround(x, base=10):
    return int(base * round(float(x)/base))

def countfasta(input):
    count = 0
    with open(input, 'rU') as f:
        for line in f:
            if line.startswith (">"):
                count += 1
    return count
    
def countfastq(input):
    lines = sum(1 for line in open(input))
    count = int(lines) / 4
    return count

def line_count(fname):
    with open(fname) as f:
        i = -1
        for i, l in enumerate(f):
            pass
    return i + 1

def line_count2(fname):
    count = 0
    with open(fname, 'rU') as f:
        for line in f:
            if not '*' in line:
                count += 1
    return count
    
def getreadlength(input):
    with open(input) as fp:
        for i, line in enumerate(fp):
            if i == 1:
                read_length = len(line) - 1 #offset to switch to 1 based counts
            elif i > 2:
                break
    return read_length
    
def get_vsearch_version():
    version = subprocess.Popen(['vsearch', '--version'], stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    for v in version:
        if v.startswith('vsearch'):
            vers = v.replace('vsearch v', '')
            vers2 = vers.split('_')[0]
            return vers2
 
def checkvsearch():
    vers = get_vsearch_version().split('.')
    if int(vers[0]) > 1:
        return True
    else:
        if int(vers[1]) > 9:
            return True
        else:
            if int(vers[2]) > 0:
                return True
            else:
                return False

def runSubprocess(cmd, logfile):
    logfile.debug(' '.join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if stdout:
        logfile.debug(stdout)
    if stderr:
        logfile.debug(stderr)


def get_version():
    version = subprocess.Popen(['ufits', 'version'], stdout=subprocess.PIPE).communicate()[0].rstrip()
    return version

def get_usearch_version(usearch):
    try:
        version = subprocess.Popen([usearch, '-version'], stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    except OSError:
        log.error("%s not found in your PATH, exiting." % usearch)
        sys.exit(1)
    vers = version[0].replace('usearch v', '')
    vers2 = vers.split('_')[0]
    return vers2

def check_utax(usearch):
    vers = get_usearch_version(usearch).split('.')
    if int(vers[0]) >= 8:
        return True
    else:
        if int(vers[1]) >= 1:
            return True
        else:
            if int(vers[2]) >= 1756:
                return True
            else:
                return False

def check_unoise(usearch):
    vers = get_usearch_version(usearch).split('.')
    if int(vers[0]) >= 9:
        return True
    else:
        if int(vers[1]) >= 0:
            return True
        else:
            if int(vers[2]) >= 2132:
                return True
            else:
                return False

def MemoryCheck():
    import psutil
    mem = psutil.virtual_memory()
    RAM = int(mem.total)
    return round(RAM / 1024000000)
                   
def systemOS():
    if sys.platform == 'darwin':
        system_os = 'MacOSX '+ platform.mac_ver()[0]
    elif sys.platform == 'linux':
        linux_version = platform.linux_distribution()
        system_os = linux_version[0]+ ' '+linux_version[1]
    else:
        system_os = sys.platform
    return system_os

def SystemInfo():
    system_os = systemOS()
    python_vers = str(sys.version_info[0])+'.'+str(sys.version_info[1])+'.'+str(sys.version_info[2])   
    log.info("OS: %s, %i cores, ~ %i GB RAM. Python: %s" % (system_os, multiprocessing.cpu_count(), MemoryCheck(), python_vers))    


def batch_iterator(iterator, batch_size):
    entry = True #Make sure we loop once
    while entry :
        batch = []
        while len(batch) < batch_size :
            try :
                entry = iterator.next()
            except StopIteration :
                entry = None
            if entry is None :
                #End of file
                break
            batch.append(entry)
        if batch :
            yield batch

def setupLogging(LOGNAME):
    global log
    if 'win32' in sys.platform:
        stdoutformat = logging.Formatter('%(asctime)s: %(message)s', datefmt='[%I:%M:%S %p]')
    else:
        stdoutformat = logging.Formatter(colr.GRN+'%(asctime)s'+colr.END+': %(message)s', datefmt='[%I:%M:%S %p]')
    fileformat = logging.Formatter('%(asctime)s: %(message)s')
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    sth = logging.StreamHandler()
    sth.setLevel(logging.INFO)
    sth.setFormatter(stdoutformat)
    log.addHandler(sth)
    fhnd = logging.FileHandler(LOGNAME)
    fhnd.setLevel(logging.DEBUG)
    fhnd.setFormatter(fileformat)
    log.addHandler(fhnd)
    
def FastMaxEEFilter(input, trunclen, maxee, output):
    from Bio.SeqIO.QualityIO import FastqGeneralIterator
    with open(output, 'w') as out:
        with open(input, 'rU') as file:
            for title, seq, qual in FastqGeneralIterator(file):
                trunclen = int(trunclen)
                Seq = seq[:trunclen]
                Qual = qual[:trunclen]
                ee = 0
                for bp, Q in enumerate(Qual):
                    q = int(ASCII.get(Q))
                    P = 10**(float(-q)/10)
                    ee += P
                if ee <= float(maxee):
                    out.write("@%s\n%s\n+\n%s\n" % (title, Seq, Qual))

def MaxEEFilter(input, maxee):
    from Bio import SeqIO
    with open(input, 'rU') as f:
        for rec in SeqIO.parse(f, "fastq"):
            ee = 0
            for bp, Q in enumerate(rec.letter_annotations["phred_quality"]):
                P = 10**(float(-Q)/10)
                ee += P
            if ee <= float(maxee):
                rec.name = ""
                rec.description = ""
                yield rec
                
def dereplicate(input, output):
    from Bio.SeqIO.QualityIO import FastqGeneralIterator
    seqs = {}
    with open(input, 'rU') as file:
        for title, sequence, qual in FastqGeneralIterator(file):
            if sequence not in seqs:
                if title.endswith(';'):
                    seqs[sequence]=title+'size=1;'
                else:
                    seqs[sequence]=title+';size=1;'
            else:
                count = int(seqs[sequence].split('=')[-1].rstrip(';')) + 1
                formated_string = seqs[sequence].rsplit('=', 1)[0]+'='+str(count)+';'
                seqs[sequence] = formated_string
    with open(output, 'w') as out:
        for sequence in seqs:
            out.write('>'+seqs[sequence]+'\n'+sequence+'\n')

def convertSize(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix) 

def faqual2fastq(fasta, qual, fastq):
    global skipCount
    from Bio.SeqIO.QualityIO import PairedFastaQualIterator
    with open(fastq, 'w') as output:
        records = PairedFastaQualIterator(open(fasta), open(qual))
        for rec in records:
            try:
                SeqIO.write(rec, output, 'fastq')
            except ValueError:
                skipCount +1
    return skipCount
    
def checkfastqsize(input):
    filesize = os.path.getsize(input)
    return filesize
    
def fastqreindex(input, output):
    from Bio.SeqIO.QualityIO import FastqGeneralIterator
    count = 1
    with open(output, 'w') as out:
        with open(input, 'rU') as fastq:
            for title, sequence, qual in FastqGeneralIterator(fastq):
                cols = title.split(';')
                header = 'R_'+str(count)+';'+cols[1]+';'
                count += 1
                out.write("@%s\n%s\n+\n%s\n" % (header, sequence, qual))

def which(name):
    try:
        with open(os.devnull) as devnull:
            diff = ['tbl2asn', 'dustmasker', 'mafft']
            if not any(name in x for x in diff):
                subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
            else:
                subprocess.Popen([name, '--version'], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            return False
    return True

def CheckDependencies(input):
    missing = []
    for p in input:
        if which(p) == False:
            missing.append(p)
    if missing != []:
        error = ", ".join(missing)
        log.error("Missing Dependencies: %s.  Please install missing dependencies and re-run script" % (error))
        sys.exit(1)
        
def fasta_strip_padding(file, output):
    from Bio.SeqIO.FastaIO import FastaIterator
    with open(output, 'w') as outputfile:
        for record in FastaIterator(open(file)):
            Seq = record.seq.rstrip('N')   
            outputfile.write(">%s\n%s\n" % (record.id, Seq))

def fastq_strip_padding(file, output):
    from Bio.SeqIO.QualityIO import FastqGeneralIterator
    with open(output, 'w') as outputfile:
        for title, seq, qual in FastqGeneralIterator(open(file)):
            Seq = seq.rstrip('N')
            Qual = qual[:len(Seq)]
            assert len(Seq) == len(Qual)    
            outputfile.write("@%s\n%s\n+\n%s\n" % (title, Seq, Qual))
            
def ReverseComp(input, output):
    with open(output, 'w') as revcomp:
        with open(input, 'rU') as fasta:
            for rec in SeqIO.parse(fasta, 'fasta'):
                revcomp.write(">%s\n%s\n" % (rec.id, rec.seq.reverse_complement()))

def guess_csv_dialect(header):
    """ completely arbitrary fn to detect the delimiter
    :type header: str
    :raise ValueError:
    :rtype: csv.Dialect
    """
    possible_delims = "\t,"
    lines = header.split("\n")
    if len(lines) < 2:
        raise ValueError("CSV header must contain at least 1 line")

    dialect = csv.Sniffer().sniff(header, delimiters=possible_delims)
    return dialect

def checkfastqsize(input):
    filesize = os.path.getsize(input)
    return filesize

def getCPUS():
    cores = multiprocessing.cpu_count()
    return cores
    
def fasta2list(input):
    seqlist = []
    with open(input, 'rU') as inseq:
        for rec in SeqIO.parse(inseq, 'fasta'):
            if not rec.description in seqlist:
                seqlist.append(rec.description)
    return seqlist
            
