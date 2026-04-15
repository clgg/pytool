import importlib.util
import pkgutil

if not hasattr(pkgutil, "find_loader"):

    def find_loader(fullname: str, path: object = None):
        return importlib.util.find_spec(fullname)

    pkgutil.find_loader = find_loader  # type: ignore[method-assign, assignment]

