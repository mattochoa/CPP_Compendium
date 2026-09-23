"""Compile (and run) every ```cpp block in a note.

Directive comments anywhere in a block (one or more per line):
    // cc: fragment        not compilable on its own (skip; use sparingly)
    // cc: ill-formed      MUST fail to compile (demonstrates a rule the compiler enforces)
    // cc: ub              compiles; running it exhibits UB. Run under sanitizers, never "expect" output
    // cc: norun           compile + link, do not execute (e.g. waits for input, runs forever)
    // cc: std=c++23       language standard (default c++20)
    // cc: remote          force Compiler Explorer (newer GCC) instead of the local compiler
    // cc: flags=-O2       extra compiler flags
    // expect: <text>      stdout must contain <text> (repeatable)

Blocks with `main` are compiled, linked and run with ASan+UBSan. Blocks without
`main` are compiled to an object only. Local g++ is used when it supports the
requested standard/headers; otherwise Compiler Explorer (godbolt.org) is used.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass


from .notes import CodeBlock, Note

DIRECTIVE_RE = re.compile(r"//\s*cc:\s*([^\n]*)")
EXPECT_RE = re.compile(r"//\s*expect:\s*(.+?)\s*$", re.M)
MAIN_RE = re.compile(r"\bint\s+main\s*\(")
NEW_HEADERS = {"print", "expected", "generator", "stacktrace", "mdspan", "flat_map", "flat_set", "spanstream", "text_encoding", "format"}
NEW_STDS = {"c++23", "c++2b", "c++26", "c++2c"}
REMOTE_COMPILER = os.environ.get("CC_REMOTE_COMPILER", "g142")
GODBOLT = "https://godbolt.org/api/compiler/{cid}/compile"
BASE_FLAGS = ["-Wall", "-Wextra", "-pedantic"]


@dataclass
class Result:
    index: int
    line: int
    status: str      # PASS | FAIL | SKIP | WARN
    how: str         # local | remote | -
    detail: str = ""

    def __str__(self):
        d = ("  " + self.detail.replace("\n", "\n    ")) if self.detail else ""
        return f"  [{self.status}] block {self.index} (line {self.line}, {self.how}){chr(10) + d if d else ''}"


def directives(code: str) -> dict:
    d = {"std": "c++20", "flags": [], "expect": EXPECT_RE.findall(code)}
    for m in DIRECTIVE_RE.finditer(code):
        for tok in m.group(1).split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                if k == "flags":
                    d["flags"].extend(v.split(","))
                else:
                    d[k] = v
            else:
                d[tok] = True
    return d


def _local_gxx() -> str | None:
    return shutil.which("g++") or shutil.which("clang++")


def _local_major() -> int:
    exe = _local_gxx()
    if not exe:
        return 0
    try:
        out = subprocess.run([exe, "-dumpversion"], capture_output=True, text=True, timeout=10).stdout
        return int(out.strip().split(".")[0])
    except Exception:
        return 0


_SAN_CACHE: list[str] | None = None


def _sanitizer_flags() -> list[str]:
    """Best sanitizer flags the local toolchain can actually link.

    MinGW-w64 (WinLibs) ships no libasan/libubsan, so the full ASan+UBSan link
    fails for *every* block. Probe once and degrade: full ASan+UBSan -> UBSan in
    trap mode (no runtime library needed; UB aborts the program) -> none.
    """
    global _SAN_CACHE
    if _SAN_CACHE is not None:
        return _SAN_CACHE
    exe = _local_gxx()
    candidates = [["-fsanitize=address,undefined", "-fno-omit-frame-pointer"],
                  ["-fsanitize=undefined", "-fsanitize-undefined-trap-on-error"],
                  []]
    tmp = tempfile.mkdtemp(prefix="cc-san-")
    try:
        src = os.path.join(tmp, "p.cpp")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write("int main(){return 0;}\n")
        for flags in candidates:
            try:
                cp = subprocess.run([exe, *flags, src, "-o", os.path.join(tmp, "p.out")],
                                    capture_output=True, text=True, timeout=60)
                if cp.returncode == 0:
                    _SAN_CACHE = flags
                    break
            except Exception:
                continue
        else:
            _SAN_CACHE = []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return _SAN_CACHE


def _needs_remote(code: str, d: dict) -> bool:
    if d.get("remote"):
        return True
    if not _local_gxx():
        return True
    headers = set(re.findall(r"#include\s*<([a-z_]+)>", code))
    major = _local_major()
    if d["std"] in NEW_STDS and major < 14:
        return True
    if headers & NEW_HEADERS and major < 14:
        return True
    return False


def _run_local(code: str, d: dict, has_main: bool) -> tuple[bool, bool, str, str]:
    """Returns (compiled, ran_ok, stdout, diagnostics)."""
    exe = _local_gxx()
    tmp = tempfile.mkdtemp(prefix="cc-snip-")   # system temp: fast, executable, invisible to the vault
    try:
        src = os.path.join(tmp, "s.cpp")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(code)
        std = "-std=" + d["std"]
        if has_main and not d.get("ill-formed"):
            out = os.path.join(tmp, "a.out")
            cmd = [exe, std, *BASE_FLAGS, *d["flags"], "-g", *_sanitizer_flags(), src, "-o", out, "-pthread"]
        else:
            cmd = [exe, std, *BASE_FLAGS, *d["flags"], "-c", src, "-o", os.path.join(tmp, "s.o")]
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if cp.returncode != 0:
            return False, False, "", cp.stderr
        if not has_main or d.get("norun") or d.get("ill-formed"):
            return True, True, "", cp.stderr
        env = dict(os.environ, ASAN_OPTIONS="detect_leaks=1", UBSAN_OPTIONS="print_stacktrace=1")
        try:
            rp = subprocess.run([out], capture_output=True, text=True, timeout=15, input="", env=env)
        except subprocess.TimeoutExpired:
            return True, False, "", "timeout (15s) — add `// cc: norun` if intentional"
        return True, rp.returncode == 0 and "runtime error" not in rp.stderr, rp.stdout, rp.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run_remote(code: str, d: dict, has_main: bool) -> tuple[bool, bool, str, str]:
    flags = ["-std=" + d["std"], *BASE_FLAGS, *d["flags"]]
    execute = has_main and not d.get("norun") and not d.get("ill-formed")
    if execute:
        flags += ["-fsanitize=undefined"]
    body = {
        "source": code,
        "options": {
            "userArguments": " ".join(flags),
            "executeParameters": {"args": [], "stdin": ""},
            "compilerOptions": {"executorRequest": execute, "skipAsm": True},
            "filters": {"execute": execute},
        },
    }
    req = urllib.request.Request(GODBOLT.format(cid=REMOTE_COMPILER), data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        r = json.loads(resp.read().decode())
    txt = lambda arr: "\n".join(x.get("text", "") for x in (arr or []))   # noqa: E731
    build = r.get("buildResult", r) if execute else r
    compiled = build.get("code", r.get("code", 1)) == 0
    diag = re.sub(r"\x1b\[[0-9;]*m", "", txt(build.get("stderr")))
    if not compiled:
        return False, False, "", diag
    if not execute:
        return True, True, "", diag
    out, err = txt(r.get("stdout")), re.sub(r"\x1b\[[0-9;]*m", "", txt(r.get("stderr")))
    return True, r.get("code", 1) == 0 and "runtime error" not in err, out, err


def check_block(i: int, b: CodeBlock) -> Result:
    d = directives(b.code)
    if d.get("fragment"):
        return Result(i, b.line, "SKIP", "-", "fragment")
    has_main = bool(MAIN_RE.search(b.code))
    remote = _needs_remote(b.code, d)
    how = f"remote {REMOTE_COMPILER}" if remote else "local"
    try:
        compiled, ran_ok, out, diag = (_run_remote if remote else _run_local)(b.code, d, has_main)
    except Exception as exc:
        return Result(i, b.line, "WARN", how, f"could not verify: {exc}")
    first = lambda s, n=6: "\n".join((s or "").strip().splitlines()[:n])   # noqa: E731
    if d.get("ill-formed"):
        return Result(i, b.line, "PASS" if not compiled else "FAIL", how,
                      "" if not compiled else "marked ill-formed but compiled cleanly")
    if not compiled:
        return Result(i, b.line, "FAIL", how, first(diag, 10))
    if d.get("ub"):
        return Result(i, b.line, "PASS", how, "UB demo: sanitizer fired" if not ran_ok else "UB demo: sanitizer silent (ok)")
    if "warning:" in (diag or ""):
        return Result(i, b.line, "WARN", how, first(diag))
    if not ran_ok:
        return Result(i, b.line, "FAIL", how, first(diag, 10) or "non-zero exit")
    missing = [e for e in d["expect"] if e not in out]
    if missing:
        return Result(i, b.line, "FAIL", how, f"expected output missing: {missing}\n  got: {first(out)}")
    return Result(i, b.line, "PASS", how, "")


def check_note(note: Note) -> list[Result]:
    return [check_block(i + 1, b) for i, b in enumerate(note.cpp_blocks())]


def asm(code: str, flags: str = "-O2 -std=c++20", compiler: str | None = None) -> str:
    """Filtered assembly from Compiler Explorer (for 'Under the Hood' sections)."""
    body = {"source": code, "options": {"userArguments": flags,
            "filters": {"binary": False, "labels": True, "directives": True, "commentOnly": True,
                        "demangle": True, "intel": True, "libraryCode": True, "trim": True}}}
    req = urllib.request.Request(GODBOLT.format(cid=compiler or REMOTE_COMPILER), data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        r = json.loads(resp.read().decode())
    if r.get("code", 0) != 0:
        return "compile error:\n" + "\n".join(x.get("text", "") for x in r.get("stderr", []))
    return "\n".join(x.get("text", "") for x in r.get("asm", []))
