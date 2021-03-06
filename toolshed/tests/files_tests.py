from toolshed.files import tokens, nopen, reader, header, is_newer_b,\
                            ProcessException
import os.path as op
import os
import glob
import time
import sys

DATA = op.join(op.dirname(__file__), "data")

def test_tokens():
    t = "asdf,2345,678"
    assert tokens(t, sep=",") == t.split(",")
    t = t.replace(",", "\t")
    assert tokens(t) == t.split("\t")


def test_split_None():
    with open('tt.tmp', 'w') as fh:
        fh.write("asdf 123\tabc\n")
        fh.flush()
        toks = next(reader('tt.tmp', header=None, sep=None))
        assert toks == ['asdf', '123', 'abc'], toks
    os.unlink('tt.tmp')

def test_skip_until():

    with open('tta.tmp', 'w') as fh:
        fh.write("""#a\n#b\n#c\na\tb\n""")

    fiter = reader('tta.tmp', header=False, sep="\t",
            skip_while=lambda toks: toks[0].startswith("#"))
    f = list(fiter)
    assert len(f) == 1, f
    assert f[0] == ["a", "b"], f
    #os.unlink('tta.tmp')


def test_split_regex():
    fh = open('tt.tmp', 'w')
    fh.write("asdf123abc\n")
    fh.close()
    toks = next(reader('tt.tmp', header=None, sep="\d+"))
    assert toks == ['asdf', 'abc'], toks
    os.unlink('tt.tmp')

def test_is_newer():

    open('tt.tmp', 'w').close()
    time.sleep(0.5)
    open('uu.tmp', 'w').close()
    assert not is_newer_b('uu.tmp', 'tt.tmp')
    time.sleep(0.5)
    open('tt.tmp', 'w').close()
    os.unlink('tt.tmp')
    os.unlink('uu.tmp')

from nose.tools import raises

@raises(ProcessException)
def test_nopen_raises():
    next(nopen("|asdfasdfasdfasdfasdf"))

def test_process_subst():
    assert not len([x for x in nopen("|cat <(less %s)") if x.strip()])
    assert len([x for x in nopen("|cat <(less %s)" % __file__.rstrip('c')) if x.strip()])

def test_namedtuple_header():
    from collections import namedtuple
    for d in reader(op.join(DATA, "file_data.txt"), header=namedtuple):
        assert hasattr(d, "a"), d
        assert hasattr(d, "b")
        assert hasattr(d, "c")

def test_callable_header():

    class Bed(object):
        def __init__(self, toks):
            self.chrom = toks[0]
            self.start = int(toks[1])
            self.end = int(toks[2])

    fh = nopen(op.join(DATA, "file_data.txt"))
    fh.readline() # drop header.
    for bed in reader(fh, header=Bed):
        assert bed.chrom
        assert isinstance(bed.start, int)

def test_reader_generator():
    """check that reader can accept a generator"""
    r = reader(op.join(DATA, "file_data.txt"), header=False)
    header = next(r)
    for d in reader(r, header=header):
        assert all(l in d for l in "abc")

def test_nopen():
    lines = open(op.join(DATA, "file_data.txt")).readlines()
    for f in glob.glob(op.join(DATA, "*")) + [lines,\
        "http://www.stanford.edu/class/stats191/data/salary.table"]:
        yield check_nopen, f
        yield check_reader, f
        yield check_ordered_reader, f
        yield check_reader_no_header, f
        yield check_header, f
    line_iter = open(op.join(DATA, "file_data.txt"))

    for fn in (check_nopen, check_reader, check_reader_no_header,
            check_header):
        line_iter.seek(0)
        yield fn, line_iter

def check_header(fname):
    assert isinstance(header(fname), list)

def check_nopen(fname):
    d = nopen(fname)
    assert hasattr(d, "__iter__")

def check_reader(fname):
    if not "http:" in fname:
        for d in reader(fname):
            assert all((k in d for k in "abc"))
            assert d['a']
    else:
        for d in reader(fname):
            assert all((k in d for k in "SXEM"))

def check_ordered_reader(fname):
    if not "http:" in fname:
        for d in reader(fname, header="ordered"):
            assert all((k in d for k in "abc"))
            d["0"] = "extra"
            d["_"] = "other"
            assert list(d.keys()) == ["a", "b", "c", "0", "_"]

def check_reader_no_header(fname):
    for l in reader(fname, header=False):
        assert isinstance(l, list), (l, type(l), fname)

