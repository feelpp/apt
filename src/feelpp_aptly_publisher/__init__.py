"""Feel++ Aptly Publisher - Publish Debian packages to APT repository via GitHub Pages.

Copyright (c) 2025 University of Strasbourg
Author: Christophe Prud'homme <christophe.prudhomme@cemosis.fr>

This file is part of Feel++ Aptly Publisher.
"""

__version__ = "1.3.0"
__author__ = "Christophe Prud'homme"
__email__ = "christophe.prudhomme@cemosis.fr"

from .publisher import AptlyPublisher
from .cleaner import AptlyCleaner, RetentionPolicy, PackageInfo

__all__ = ["AptlyPublisher", "AptlyCleaner", "RetentionPolicy", "PackageInfo"]
