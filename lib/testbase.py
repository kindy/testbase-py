import sys, re


_filters = {}

def add_filter(name, fn):
    _filters[name] = fn

filter_noop = lambda v, a=None: v


class Block(dict):
    _section_order = None
    _filter_map = None
    _is_filtered = False

    def __init__(self, name, desc, _lineno=-1):
        self.name = name
        self.desc = desc
        self._lineno = _lineno

        self['name'] = name
        self['desc'] = desc

    def __attr__(self, name):
        return self.get(name)

    def _run_filters(self):
        assert not self._is_filtered, 'Attempt to filter a block twice'
        self._is_filtered = True

        if not self._filter_map:
            return

        map_ = self._filter_map
        keys = self._section_order
        filters = _filters

        for key in keys:
            val = self[key]
            oval = val
            arg = None
            for filter_ in map_.get(key, []):
                if '=' in filter_:
                    filter_, arg = filter_.split('=', 1)
                filter_ = filters.get(filter_, filter_noop)
                val = filter_(val, arg) if arg else filter_(val)
                # print '- filter: ',  filter_, ' val: ', val
            if val != oval:
                self[key] = val


def parse(src, block_delim='===', data_delim='---', block_class=Block, delay_filters=False):
    lineno = 1;
    hunks = []

    pattern = r'''
          ^(%(cd)s.*?(?=^%(cd)s|\Z))
        | ^([^\n]*\n)
    ''' % {'cd': re.escape(block_delim)}

    def proc(m):
        hunk = m.group(1)
        other = m.group(1)
        if hunk:
            hunks.append(hunk)
        elif other:
            lineno += 1

    re.sub(pattern, proc, src, flags=re.X|re.M|re.S)

    blocks = []
    for hunk in hunks:
        blocks.append(make_class(hunk, lineno,
            block_delim=block_delim, data_delim=data_delim, block_class=block_class))
        lineno += len([c for c in hunk if c == '\n'])

    if not delay_filters:
        for block in blocks:
            if not block._is_filtered:
                block._run_filters()

    return blocks



def make_class(hunk, lineno, block_delim, data_delim, block_class):
    m = re.match(r'%s[ \t]*(.*)\s+' % re.escape(block_delim), hunk)
    assert m, 'Invalid block at line:%d' % lineno

    name = m.group(1).strip()

    hunk = hunk[m.end():]
    parts = re.split(r'^%s +\(?(\w+)\)?([^\n]*)\n' % re.escape(data_delim), hunk, flags=re.M)
    desc = parts.pop(0).strip() if parts else ''
    if not desc:
        desc = name

    block = block_class(name, desc, _lineno=lineno)
    
    filter_map = {}
    section_order = []
    for idx in range(0, len(parts), 3):
        type_, filters, val = parts[idx:idx+3]
        if re.search(r':(\s|\z)', filters):
            assert not val.strip(), "Extra lines not allowed in '%s' section" % type_
            filters, val = re.split(r'\s*:(?:\s+|\z)', filters, maxsplit=2)

        block[type_] = val.strip()
        section_order.append(type_)
        filter_map[type_] = filters.split()

    block._section_order = section_order
    block._filter_map = filter_map

    return block


def init_default_filters():
    from hashlib import md5
    from base64 import b64encode, b64decode
    from simplejson import dumps as json_encode, loads as json_decode
    add_filter('md5', lambda v: md5(v).hexdigest())
    add_filter('md5b', lambda v: md5(v).digest())
    add_filter('b64e', lambda v: b64encode(v))
    add_filter('b64d', lambda v: b64decode(v))
    add_filter('jsone', lambda v: json_encode(v))
    add_filter('jsond', lambda v: json_decode(v))
    add_filter('len', lambda v: len(v))

    _to_num = lambda v: (float(v) if '.' in v else int(v)) if isinstance(v, basestring) else v
    add_filter('add', lambda v, arg: _to_num(v) + _to_num(arg))


init_default_filters()


if __name__ == '__main__':
    print parse('''
=== abc x 
--- a md5
    xadf  

--- b b64e
    yadf 
--- c b64e b64d len add=-6 add=10
    yadf 

=== abc
--- a: xadf
--- b
    yadf
--- c jsond
{
    "a": 123,
    "b": 456
}
    ''')

