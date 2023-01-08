import argparse
import ast


def io_parser():
    parser = argparse.ArgumentParser(description='Input and output files')
    parser.add_argument('indir', type=str, help='Input file dir')
    parser.add_argument('outdir', type=str, help='Output file dir')
    args = parser.parse_args()
    return args.indir, args.outdir


def read_file(file):
    with open(file, 'r', errors='replace') as f:
        text = f.read()
    return text


def read_file_line(file):
    with open(file, 'r') as f:
        orig, plag = f.readline().split()
    return orig, plag


def write_in_file(file, value):
    with open(file, 'a') as f:
        f.write(str(value))


class FileManager:
    def __init__(self):
        self.input_file, self.output_file = io_parser()
        self.inp_orig = None
        self.inp_plag = None
        self._cur_orig_text = None
        self._cur_plag_text = None

    def next_text(self):
        self.inp_orig, self.inp_plag = read_file_line(self.input_file)
        self._cur_orig_text = read_file(self.inp_orig)
        self._cur_plag_text = read_file(self.inp_plag)

    @property
    def orig(self):
        return self._cur_orig_text

    @orig.setter
    def orig(self, value):
        self._cur_orig_text = value

    @property
    def plag(self):
        return self._cur_plag_text

    @plag.setter
    def plag(self, value):
        self._cur_plag_text = value


class Visitor(ast.NodeVisitor):
    """
    Collects list of variables
    """
    def __init__(self):
        self.list = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.list.add(node.id)


class Normalize(ast.NodeTransformer):   # troubles
    """ 
        def visit_Name(self, node):
        if True:    # change if
            return ast.Subscript(
                value=ast.Name(id='y_new', ctx=node.ctx),
                slice=ast.Index(value=ast.Constant(value='something')),
                ctx=node.ctx
            )

    def visit_FunctionDef(self, node):
        print(dir(node.args))
        for i in node.args.args:
            if i.annotation is not None:
                i.annotation = None
        return ast.Subscript(

        )

    """


def processed_prog_text(text):
    tree = ast.parse(text)
    tree = ast.fix_missing_locations(Normalize().visit(tree))
    processed_text = ast.unparse(tree)
    return processed_text


def levenstein_distance(text1, text2):
    a, b = len(text1), len(text2)
    if a > b:
        text1, text2 = text2, text1
        a, b = b, a

    cur_row = range(a + 1)
    for i in range(1, b + 1):
        prev_row, cur_row = cur_row, [i] + [0] * a

        for j in range(1, a + 1):
            add, delete, change = prev_row[j] + 1, cur_row[j - 1] + 1, prev_row[j - 1]

            if text1[j - 1] != text2[i - 1]:
                change += 1

            cur_row[j] = min(add, delete, change)

    return cur_row[a]


def damerau_levenshtein_distance(s1, s2):
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in range(-1, lenstr1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, lenstr2 + 1):
        d[(-1, j)] = j + 1

    for i in range(lenstr1):
        for j in range(lenstr2):
            if s1[i] == s2[j]:
                cost = 0

            else:
                cost = 1

            d[(i, j)] = min(
                d[(i - 1, j)] + 1,  # deletion
                d[(i, j - 1)] + 1,  # insertion
                d[(i - 1, j - 1)] + cost,  # substitution
            )

            if i and j and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + 1)  # transposition

    return d[lenstr1 - 1, lenstr2 - 1]


def run():
    a = FileManager()

    for line in open(a.input_file, 'r'):
        a.inp_orig, a.inp_plag = line.split()
        a.orig = read_file(a.inp_orig)
        a.plag = read_file(a.inp_plag)
        print(a.inp_orig)

        try:
            a.orig = processed_prog_text(a.orig)
            a.plag = processed_prog_text(a.plag)
        except SyntaxError:
            pass

        diff = damerau_levenshtein_distance(a.orig, a.plag)    # may be levenstein_distance
        mlen = len(max(a.orig, a.plag))
        if mlen == 0:
            result = 1.0
            write_in_file(a.output_file, result)
            continue

        result = round((mlen - diff) / mlen, 4)
        write_in_file(a.output_file, result)


run()
