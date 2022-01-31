""" Python コードのメトリクス計測

* 空白行、コメント行（単一行、複数行）は削除
* radon を使用し、次の項目を計測する
    * ファイルの MI Score
    * function, class, method の行数、Cyclomatic Complexity
* ファイルもしくはフォルダを指定
* フォルダ指定時は、フォルダ直下の *.py を対象とする
"""

import os.path
import glob
from collections import namedtuple
import sys
import re

import radon.visitors
from radon.complexity import cc_visit, cc_rank
from radon.metrics import mi_visit, mi_rank

from csvutil import to_csvline

Stat = namedtuple("Stat", "file mi cc")
CCStats = namedtuple("CCStats", "type name loc complexity")


def to_a(self):
    return [self.type, self.name, self.loc, self.complexity]


setattr(CCStats, "to_a", to_a)


def main(paths):
    stats = anayalize(paths)
    if stats:
        print_result(stats)


def anayalize(paths):
    stats = []
    for path in paths:
        if os.path.isfile(path):
            stats.append(Stat(path, *get_metrics(path)))
        elif os.path.isdir(path):
            for file in glob.glob(os.path.join(path, "*.py")):
                stats.append(Stat(file, *get_metrics(file)))
        else:
            print("# invalid target", path)
    return stats


def print_result(stats):
    print("file,metrics,name,loc,complexity,rank")
    for stat in stats:
        print(to_csvline([stat.file, "mi score", "", "", stat.mi, mi_rank(stat.mi)]))
        for cc in stat.cc:
            print(to_csvline([stat.file] + cc.to_a() + [cc_rank(cc.complexity)]))


def get_metrics(file):
    text = read_text(file)

    cc_stats = []
    for cc in cc_visit(text):
        if isinstance(cc, radon.visitors.Function):
            cc_stats.append(
                CCStats(
                    "method" if cc.is_method else "function",
                    f"{cc.classname}.{cc.name}" if cc.is_method else cc.name,
                    cc.endline - cc.lineno + 1,
                    cc.complexity,
                )
            )
        elif isinstance(cc, radon.visitors.Class):
            cc_stats.append(
                CCStats(
                    "class", cc.name, cc.endline - cc.lineno + 1, cc.real_complexity
                )
            )
        else:
            raise NotImplemented(repr(cc))

    mi = mi_visit(text, False)

    return mi, cc_stats


def read_text(file):
    lines = []
    comment = ""
    for line in open(file, encoding="utf-8"):
        if line.strip() == "":
            pass
        elif re.sub(r"\s*#.*$", "", line) == "":
            pass
        elif comment == "" and re.match(r'\s*"""', line):
            comment = line.strip()
        elif comment == "":
            lines.append(line)
        elif re.search(r'"""\s*$', line):
            # lines.append(comment + line)
            comment = ""
        else:
            pass
    return "".join(lines)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("usage: pystats.py file|dir [file|dir...]")
        exit()
    main(sys.argv[1:])
