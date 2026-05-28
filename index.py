from pathlib import Path
import sys

plugin_root = Path(__file__).resolve().parent
package_root = plugin_root / "rss_feed"
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

from rss_tab import RSSTab


def register(api):
    api.register_panel("rss-feed.reader", "RSS Reader", lambda: RSSTab())
