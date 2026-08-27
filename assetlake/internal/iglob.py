from __future__ import annotations

import re
from functools import lru_cache
from urllib.parse import ParseResult, urlparse

_WILDCARD_RE = re.compile(r"[*?\[]")
_CLOUD_PATH_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://[^/]*(.*)")


class IGlob:
    @staticmethod
    def standardise(glob: str) -> str:
        if IGlob.is_local(glob) and IGlob.parse_scheme(glob) == "file":
            return glob.split("://", 1)[1]
        return glob

    @staticmethod
    def parse(glob: str) -> ParseResult:
        return urlparse(glob)

    @staticmethod
    def is_local(glob: str) -> bool:
        _parsed = IGlob.parse(glob)
        if _parsed.scheme == "file":
            return True
        if _parsed.scheme == "":
            return True
        return False

    @staticmethod
    def is_cloud(glob: str) -> bool:
        return not IGlob.is_local(glob)

    @staticmethod
    def parse_scheme(glob: str) -> str:
        _parsed = IGlob.parse(glob)
        _scheme = _parsed.scheme
        return _scheme

    @staticmethod
    def parse_full_prefix(glob: str) -> str:
        if IGlob.is_local(glob):
            # return "/path/to/directory" for local
            if IGlob.parse_scheme(glob) == "file":
                _idx = glob.find("://") + 3
                return glob[_idx:]
            return glob
        else:
            # return "bucket/path/to/directory" for cloud
            # avoid urlparse: it splits on '?' treating it as query separator
            _m = _CLOUD_PATH_RE.match(glob)
            return _m.group(1).lstrip("/") if _m else ""

    @staticmethod
    def parse_bucket(glob: str) -> str | None:
        _parsed: ParseResult = IGlob.parse(glob)
        _netloc: str = _parsed.netloc
        if IGlob.is_local(glob):
            return None
        else:
            return _netloc

    @staticmethod
    def parse_common_prefix(glob: str) -> str:
        _full_prefix: str = IGlob.parse_full_prefix(glob)
        if not _full_prefix:
            return ""
        _match = _WILDCARD_RE.search(_full_prefix)
        if _match is None:
            # No wildcard found
            if "/" in _full_prefix:
                return _full_prefix.rsplit("/", 1)[0] + "/"
            else:
                return ""
        else:
            # Cut the path at the first wildcard
            _cut = _full_prefix[: _match.start()]
            if "/" in _cut:
                return _cut.rsplit("/", 1)[0] + "/"
            else:
                return ""

    @staticmethod
    def parse_object_pattern(glob: str) -> str | None:
        _full_prefix: str = IGlob.parse_full_prefix(glob)
        _common_prefix: str = IGlob.parse_common_prefix(glob)
        return _full_prefix[len(_common_prefix) :]

    @staticmethod
    @lru_cache(maxsize=256)
    def _compile(pattern: str) -> re.Pattern:
        i, n = 0, len(pattern)
        out = []
        while i < n:
            c = pattern[i]
            if c == "*":
                if pattern[i : i + 2] == "**":
                    out.append(".*")
                    i += 2
                else:
                    out.append("[^/]*")
                    i += 1
            elif c == "?":
                out.append("[^/]")
                i += 1
            elif c == "[":
                j = pattern.find("]", i)
                if j == -1:
                    out.append(re.escape(c))
                    i += 1
                else:
                    out.append(pattern[i : j + 1])
                    i = j + 1
            else:
                out.append(re.escape(c))
                i += 1
        return re.compile("^" + "".join(out) + "$")

    @staticmethod
    def match(glob: str, uri: str) -> bool:
        # Reject mismatched buckets before path comparison
        if IGlob.parse_bucket(glob) != IGlob.parse_bucket(uri):
            return False
        _full_pattern = IGlob.parse_full_prefix(glob)
        _candidate = IGlob.parse_full_prefix(uri)
        return bool(IGlob._compile(_full_pattern).match(_candidate))
