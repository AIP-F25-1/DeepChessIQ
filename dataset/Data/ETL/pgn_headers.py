import re
from typing import Iterator, TextIO, Tuple, Dict

_HDR = re.compile(r'^\[(\w+)\s+"(.*)"\]$')

def read_game_headers_only(fp: TextIO) -> Iterator[Tuple[Dict[str, str], int]]:
    """
    Yield (headers_dict, cookie_after_game) without building SAN/moves.
    Advances fp to the next game's first header (or EOF).
    """
    headers: Dict[str, str] = {}

    while True:
        pos = fp.tell()
        line = fp.readline()
        if not line:
            if headers:
                yield headers, fp.tell()
            return

        s = line.strip("\r\n")
        if not s:
            # end of headers; fast-skip move section until next header or EOF
            if headers:
                while True:
                    pos2 = fp.tell()
                    l2 = fp.readline()
                    if not l2:
                        yield headers, fp.tell()
                        return
                    if l2.startswith("["):
                        fp.seek(pos2)  # rewind to next game's header
                        yield headers, fp.tell()
                        headers = {}
                        break
            continue

        m = _HDR.match(s)
        if m:
            headers[m.group(1)] = m.group(2)
        else:
            # unexpected line; treat as start of moves — scan to next game boundary
            while True:
                pos2 = fp.tell()
                l2 = fp.readline()
                if not l2 or l2.startswith("["):
                    fp.seek(pos2)
                    yield headers, fp.tell()
                    headers = {}
                    break
