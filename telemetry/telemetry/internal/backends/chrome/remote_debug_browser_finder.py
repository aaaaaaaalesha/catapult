from telemetry.core import platform as core_platform
from telemetry.internal.backends.chrome.remote_debug_browser_backend import (
  RemoteDebugBrowserBackend,
)
from telemetry.internal.browser import browser_finder_exceptions
from telemetry.internal.browser.browser import Browser
from telemetry.internal.browser.possible_browser import PossibleBrowser


class RemoteDebugBrowser(PossibleBrowser):
  """Finder для уже запущенного удалённого Chromium по DevTools."""

  def __init__(self, finder_options, device):
    super().__init__('remote_debug', 'any', supports_tab_control=False)
    host = finder_options.remote_debug_host
    port = finder_options.remote_debug_port
    if not host or not port:
      raise browser_finder_exceptions.BrowserFinderException(
        'Для remote_debug нужно указать --remote-debug-host и --remote-debug-port'
      )
    self._host = host
    self._port = port
    self._finder_options = finder_options
    self._device = device

  def Create(self):
    """Создаёт backend, подключает DevTools и возвращает Browser."""

    if not self._platform or not self._platform_backend:
      self._InitPlatformIfNeeded()

    browser_backend = RemoteDebugBrowserBackend(
      platform_backend=self._platform_backend,
      browser_options=self._finder_options.browser_options,
      browser_directory=None,
      profile_directory=None,
      host=self._host,
      port=self._port,
    )
    # Запускаем (подключаемся)
    browser_backend.Start([])
    # Возвращаем полноценный Browser
    return Browser(browser_backend, platform_backend=self._platform_backend, startup_args=[])

  def SupportsOptions(self, browser_options):
    """Разрешаем любые browser_options для удалённого браузера."""
    return True

  def _InitPlatformIfNeeded(self):
    """Инициализация платформы — используем локальный десктоп."""
    if getattr(self, '_platform', None):
      return
    self._platform = core_platform.GetHostPlatform()
    # Здесь ._platform_backend — внутреннее поле Telemetry
    self._platform_backend = self._platform._platform_backend


def IsBrowserTypeRelevant(browser_type):
  """Telemetry вызовет этот finder только если browser_type подходит."""
  return browser_type in ('remote_debug', 'any', 'list')


def CanFindAvailableBrowsers():
  """Всегда разрешаем искать (нет привязки к ChromeOS или Android)."""
  return True


def FindAllBrowserTypes():
  """Типы браузеров, которые этот finder умеет находить."""
  return ['remote_debug']


def FindAllAvailableBrowsers(finder_options, device):
  """Возвращает PossibleRemoteDebugBrowser, если он применим."""
  try:
    return [RemoteDebugBrowser(finder_options, device)]
  except browser_finder_exceptions.BrowserFinderException:
    return []


def SelectDefaultBrowser(possible_browsers):
  """Выбирает первый найденный браузер (единственный) по умолчанию."""
  return possible_browsers[0] if possible_browsers else None
