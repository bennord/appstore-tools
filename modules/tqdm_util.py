# Adapted from https://github.com/tqdm/tqdm#usage

from time import sleep
import contextlib
import sys
from tqdm import tqdm
from tqdm.contrib import DummyTqdmFile


@contextlib.contextmanager
def std_out_err_redirect_tqdm():
    orig_out_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
        yield orig_out_err[0]
    finally:
        sys.stdout, sys.stderr = orig_out_err


@contextlib.contextmanager
def tqdm_with_redirect(*args, **kwargs):
    with std_out_err_redirect_tqdm() as orig_stdout:
        with tqdm(file=orig_stdout, dynamic_ncols=True, *args, **kwargs) as t:
            yield t
