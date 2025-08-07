import json
import urllib.parse
import urllib.request

from telemetry.core import exceptions
from telemetry.internal.backends.chrome.chrome_browser_backend import (
    ChromeBrowserBackend,
)
from telemetry.internal.backends.chrome_inspector import devtools_client_backend

_NODATA_STRING_STUB = '`NO DATA - RemoteDebugBrowserBackend`'


class RemoteDebugBrowserBackend(ChromeBrowserBackend):
  def __init__(self, platform_backend, browser_options,
               browser_directory, profile_directory,
               host, port, supports_extensions=True, supports_tab_control=True):
    super().__init__(platform_backend, browser_options,
                     browser_directory, profile_directory, supports_extensions,
                     supports_tab_control)
    self._host = host
    self._port = port

  def Start(self, startup_args):
    # Не запускаем локальный процесс, просто подключаемся к удалённому
    self._devtools_port = self._port
    self._devtools_host = self._host
    try:
      self.BindDevToolsClient()
    except Exception as e:
      raise exceptions.BrowserConnectionGoneException(
        self.browser,
        'Failed to connect to remote debug port %s:%s: %s' %
        (self._host, self._port, e))

  def _GetDevToolsClient(self):
    # If the agent does not appear to be ready, it could be because we got the
    # details of an older agent that no longer exists. It's thus important to
    # re-read and update the port and target on each retry.
    try:
      devtools_port, browser_target = self._FindDevToolsPortAndTarget()
    except EnvironmentError:
      return None  # Port information not ready, will retry.

    return devtools_client_backend.GetDevToolsBackEndIfReady(
      devtools_port=devtools_port,
      app_backend=self,
      browser_target=browser_target,
      enable_tracing=self._enable_tracing,
      devtools_host=self._host)

  def _FindDevToolsPortAndTarget(self):
    # Собираем URL вида "ws://host:port/devtools/browser/<uuid>"
    url = f'http://{self._host}:{self._port}/json/version'
    with urllib.request.urlopen(url, timeout=1) as resp:
      info = json.load(resp)

    if not (ws_url := info.get('webSocketDebuggerUrl')):
      raise EnvironmentError(f'No webSocketDebuggerUrl in {url}')
    parts = urllib.parse.urlparse(ws_url)
    target = parts.path + (f'?{parts.query}' if parts.query else '')
    return int(self._port), target

  # Переопределим GetBrowserExecutablePath, чтобы не падал
  def _GetBrowserExecutablePath(self):
    return None

  def GetPid(self):
    # Telemetry хочет знать pid, но у нас его нет.
    return None

  def GetStandardOutput(self):
    return _NODATA_STRING_STUB

  # # То же для файлового лога.
  def GetLogFileContents(self):
    return _NODATA_STRING_STUB

  # Проверка "работает ли процесс" — у нас нет процесса, всегда False.
  def IsBrowserRunning(self):
    return False

  # # И, на всякий случай, если кто-то вызовет CollectDebugData:
  def CollectDebugData(self, log_level):
    return {}

  # Telemetry будет пытаться найти и удалить "миндампы".
  def CleanupUnsymbolizedMinidumps(self, fatal=True):
    return None

  # Иногда Telemetry может напрямую спросить пути до дампов,
  # но их у нас нет — возвращаем пустые списки.
  def GetAllMinidumpPaths(self, log=True):
    return [], ''

  def GetAllUnsymbolizedMinidumpPaths(self, log=True):
    return [], ''
