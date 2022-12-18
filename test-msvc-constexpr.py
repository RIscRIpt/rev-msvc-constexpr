import os
import string
import itertools
import argparse
import tempfile
import subprocess

PATTERNS = [
    """
        {fn} bool F() {{ {ret} return true; }}
        static_assert(F());
    """,
    """
        {fn_proxy} bool F_proxy() {{ {ret_proxy} return true; }}
        {fn} bool F() {{ {ret} return F_proxy(); }}
        static_assert(F());
    """,
    """
        struct S {{
            {fn_proxy} S() {{}}
            {fn} operator bool() {{ {ret} return true; }}
        }};
        static_assert(S{{}});
    """,
    """
        struct S_proxy {{
            {fn_proxy} S_proxy() {{}}
        }};
        struct S : S_proxy {{
            {fn} operator bool() {{ {ret} return true; }}
        }};
        static_assert(S{{}});
    """,
]

def is_valid_msvc_code(cl, code, verbose=False):
    filename = None
    launcher = [] if os.name == "nt" else ["wine"]
    try:
        fd, filename = tempfile.mkstemp(suffix=".cpp")
        os.write(fd, code.encode("utf-8"))
        os.close(fd)
        params = {}
        if not verbose:
            params["stdout"] = subprocess.DEVNULL
            params["stderr"] = subprocess.DEVNULL
        return subprocess.call(launcher + [cl, "/nologo", "/c", "/utf-8", filename], **params) == 0
    finally:
        if filename:
            os.remove(filename)
            try:
                os.remove(os.path.basename(filename).removesuffix(".cpp") + ".obj")
            except:
                pass

def main(args):
    for pattern in PATTERNS:
        format_args = [f for _, f, _, _ in string.Formatter().parse(pattern) if f]
        format_vals = []
        for arg in format_args:
            if arg.startswith("fn"):
                format_vals.append(["", "constexpr", "[[msvc::constexpr]]"])
            elif arg.startswith("ret"):
                format_vals.append(["", "[[msvc::constexpr]]"])
            else:
                raise RuntimeError("unknown format arg")
        for vals in itertools.product(*format_vals):
            code = pattern.format(**dict(zip(format_args, vals)))
            is_valid = is_valid_msvc_code(args.cl, code, args.verbose)
            if is_valid or args.verbose:
                print("//", "*" * 77)
                print(code)
                if args.verbose:
                    print(">", "Valid" if is_valid else "Invalid")


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--cl")
    args.add_argument("--verbose", action="store_true", default=False)
    main(args.parse_args())
