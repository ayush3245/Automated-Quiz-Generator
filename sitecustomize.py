import os

# Disable auto-loading external pytest plugins to keep tests hermetic.
# This avoids failures due to user/global plugins or unrelated packages.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")


