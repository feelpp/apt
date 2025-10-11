"""Feel++ Aptly Publisher - Publish Debian packages to APT repository via GitHub Pages."""

__version__ = "1.0.0"
__author__ = "Feel++ Consortium"
__email__ = "contact@feelpp.org"

from .publisher import AptlyPublisher

__all__ = ["AptlyPublisher"]
