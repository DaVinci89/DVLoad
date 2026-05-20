"""
DVLoad – локальний завантажувач медіа для Android
Використовує вбудований Flask-сервер, Kivy UI, yt-dlp та ffmpeg.
"""
import os
import sys
import threading
import requests
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.cardwidget import CardWidget  # використаємо власний
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.app import App
from kivy.core.window import Window

# ---------- Запуск Flask-сервера в окремому потоці ----------
# Додаємо шлях до поточної теки в sys.path, щоб імпортувати app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app as backend

def run_flask():
    # Запускаємо той самий сервер, але без шаблонів (тільки API)
    backend.app.run(host='127.0.0.1', port=8899, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# ---------- Kivy UI ----------
Window.clearcolor = (0.06, 0.08, 0.13, 1)   # темно-синій фон

KV = """
<Card@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(220)
    padding: dp(12)
    spacing: dp(8)

<CardHeader@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(90)
    spacing: dp(12)

<Thumbnail@AsyncImage>:
    size_hint_x: None
    width: dp(130)
    keep_ratio: True
    allow_stretch: True

<CardTitle@Label>:
    font_size: '16sp'
    bold: True
    color: 0.94, 0.96, 1, 1
    size_hint_y: None
    height: self.texture_size[1]
    shorten: True
    shorten_from: 'right'

<CardMeta@Label>:
    font_size: '12sp'
    color: 0.6, 0.66, 0.78, 1
    size_hint_y: None
    height: self.texture_size[1]

<QualityChip@ToggleButton>:
    size_hint_x: None
    width: dp(60)
    height: dp(32)
    background_normal: ''
    background_color: 0.08, 0.12, 0.22, 1
    color: 0.85, 0.88, 0.95, 1
    border_radius: [dp(16)]
    font_size: '12sp'
    group: 'quality'
    on_press: app.select_quality(root, self.text)

<DownloadButton@Button>:
    size_hint_x: None
    width: dp(100)
    height: dp(36)
    background_normal: ''
    background_color: 0.98, 0.48, 0.27, 1   # акцентний оранжевий
    color: 0.08, 0.08, 0.12, 1
    bold: True
    font_size: '13sp'
    border_radius: [dp(18)]

BoxLayout:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(16)

    BoxLayout:
        size_hint_y: None
        height: dp(60)
        Label:
            text: 'DVLoad'
            font_size: '34sp'
            font_name: 'Roboto'
            bold: True
            color: 0.98, 0.48, 0.27, 1
            size_hint_x: 0.4
        Label:
            text: 'безкоштовний завантажувач'
            font_size: '12sp'
            color: 0.7, 0.75, 0.9, 1
            size_hint_x: 0.6
            halign: 'right'
            valign: 'bottom'

    TextInput:
        id: url_input
        hint_text: 'Вставте посилання (YouTube, TikTok, Instagram та ін.)\\nКілька – розділяйте пробілом, комою або новим рядком'
        size_hint_y: None
        height: dp(100)
        background_color: 0.05, 0.07, 0.12, 1
        foreground_color: 0.94, 0.96, 1, 1
        cursor_color: 0.98, 0.48, 0.27, 1
        padding: [dp(12), dp(12), dp(12), dp(12)]
        font_size: '14sp'

    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(12)
        ToggleButton:
            text: 'Відео MP4'
            group: 'format'
            state: 'down'
            background_normal: ''
            background_color: 0.12, 0.18, 0.28, 1 if self.state == 'normal' else 0.98, 0.48, 0.27, 1
            color: 0.94,0.96,1,1 if self.state == 'normal' else 0.08,0.08,0.12,1
            border_radius: [dp(24)]
            on_press: app.set_format('video')
        ToggleButton:
            text: 'Аудіо MP3'
            group: 'format'
            background_normal: ''
            background_color: 0.12, 0.18, 0.28, 1 if self.state == 'normal' else 0.98, 0.48, 0.27, 1
            color: 0.94,0.96,1,1 if self.state == 'normal' else 0.08,0.08,0.12,1
            border_radius: [dp(24)]
            on_press: app.set_format('audio')
        Button:
            text: '✨ Отримати'
            size_hint_x: 1.5
            background_normal: ''
            background_color: 0.98, 0.48, 0.27, 1
            color: 0.08, 0.08, 0.12, 1
            bold: True
            border_radius: [dp(24)]
            on_release: app.fetch_urls()

    ScrollView:
        id: scroll
        do_scroll_x: False
        BoxLayout:
            id: cards_container
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(12)

    BoxLayout:
        size_hint_y: None
        height: dp(50)
        Button:
            text: '⚡ Завантажити все'
            background_normal: ''
            background_color: 0.1, 0.14, 0.24, 1
            color: 0.98, 0.48, 0.27, 1
            border_radius: [dp(24)]
            on_release: app.download_all()

    Label:
        text: 'Made by DaVinci'
        size_hint_y: None
        height: dp(36)
        font_size: '11sp'
        color: 0.45, 0.52, 0.7, 1
        halign: 'center'
"""

class DVLoadApp(App):
    format_choice = 'video'

    def build(self):
        self.title = 'DVLoad'
        self.root = Builder.load_string(KV)
        self.root.ids.url_input.bind(on_text_validate=lambda x: self.fetch_urls())
        self.jobs = {}      # { card_index: job_id }
        self.cards_data = []  # список карток з інформацією
        return self.root

    def set_format(self, fmt):
        self.format_choice = fmt
        # при зміні формату перемальовуємо всі картки (щоб показати якісні кнопки)
        self.refresh_all_cards()

    def fetch_urls(self):
        raw = self.root.ids.url_input.text
        urls = []
        for part in raw.replace(',', ' ').split():
            if part.startswith('http'):
                urls.append(part)
        if not urls:
            return
        container = self.root.ids.cards_container
        container.clear_widgets()
        self.cards_data.clear()
        self.jobs.clear()

        for idx, url in enumerate(urls):
            card = Card(row_data={'url': url, 'status': 'loading', 'index': idx})
            container.add_widget(card)
            self.cards_data.append({'url': url, 'status': 'loading', 'index': idx, 'widget': card})
            self.get_info(idx, url)

    def get_info(self, idx, url):
        def on_success(req, result):
            if 'error' in result:
                self.update_card(idx, status='error', error=result['error'])
            else:
                self.update_card(idx, status='ready', info=result)
        def on_failure(req, error):
            self.update_card(idx, status='error', error=str(error))
        headers = {'Content-Type': 'application/json'}
        UrlRequest('http://127.0.0.1:8899/api/info',
                   req_body=json.dumps({'url': url}),
                   method='POST',
                   on_success=on_success,
                   on_failure=on_failure,
                   req_headers=headers)

    def update_card(self, idx, status, info=None, error=None):
        card = self.cards_data[idx]['widget']
        data = self.cards_data[idx]
        data['status'] = status
        if info:
            data['title'] = info.get('title', '')
            data['thumbnail'] = info.get('thumbnail', '')
            data['uploader'] = info.get('uploader', '')
            data['duration'] = info.get('duration', 0)
            data['formats'] = info.get('formats', [])
            data['selected_format'] = data['formats'][0]['id'] if data['formats'] else None
        elif error:
            data['error'] = error
        # оновлюємо відображення
        self._render_card(card, data)

    def _render_card(self, card, data):
        card.clear_widgets()
        if data['status'] == 'loading':
            card.add_widget(Label(text='Завантаження інформації...', color=(0.7,0.75,0.9,1)))
            return
        if data['status'] == 'error':
            card.add_widget(Label(text=f"❌ Помилка: {data.get('error', 'невідома')}\n{data['url']}",
                                  color=(1,0.5,0.5,1), size_hint_y=None, height=dp(60)))
            return

        # Статус ready – будуємо повну картку
        is_audio = (self.format_choice == 'audio')
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(90), spacing=dp(12))

        # Мініатюра або іконка
        if is_audio:
            thumb = Label(text='🎵', font_size='36sp', size_hint_x=None, width=dp(130))
        else:
            thumb = AsyncImage(source=data.get('thumbnail', ''), size_hint_x=None, width=dp(130))
        header.add_widget(thumb)

        text_box = BoxLayout(orientation='vertical', size_hint_x=1)
        title = Label(text=data.get('title', 'Без назви'), **CardTitle._kwargs)
        meta = Label(text=f"{data.get('uploader', '')}  •  {self._format_duration(data.get('duration', 0))}",
                     **CardMeta._kwargs)
        text_box.add_widget(title)
        text_box.add_widget(meta)
        header.add_widget(text_box)
        card.add_widget(header)

        # Панель якості (тільки для відео)
        if not is_audio and data.get('formats'):
            quality_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
            for fmt in data['formats']:
                chip = QualityChip(text=fmt['label'], group='quality')
                chip.fmt_id = fmt['id']
                chip.bind(on_press=lambda btn, fid=fmt['id']: self.select_quality(data, fid))
                if data.get('selected_format') == fmt['id']:
                    chip.state = 'down'
                quality_box.add_widget(chip)
            card.add_widget(quality_box)

        # Кнопка завантаження та статус
        btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(12))
        dl_btn = DownloadButton(text='Завантажити')
        dl_btn.bind(on_release=lambda x: self.start_download(data))
        btn_row.add_widget(dl_btn)

        if data.get('download_status') == 'downloading':
            status_label = Label(text='⏳ Завантаження...', color=(0.98,0.48,0.27,1))
        elif data.get('download_status') == 'done':
            status_label = Label(text='✅ Готово', color=(0.2,0.8,0.5,1))
            dl_btn.disabled = True
        elif data.get('download_status') == 'error':
            status_label = Label(text=f"❌ {data.get('dl_error', '')[:30]}", color=(1,0.5,0.5,1))
        else:
            status_label = Label(text='')
        btn_row.add_widget(status_label)
        card.add_widget(btn_row)

    def select_quality(self, data, fmt_id):
        data['selected_format'] = fmt_id
        # перемалювати цю картку
        self._render_card(data['widget'], data)

    def start_download(self, data):
        if data.get('download_status') == 'downloading':
            return
        data['download_status'] = 'downloading'
        data['dl_job_id'] = None
        self._render_card(data['widget'], data)

        payload = {
            'url': data['url'],
            'format': self.format_choice,
            'format_id': data.get('selected_format') if self.format_choice == 'video' else None,
            'title': data.get('title', '')
        }
        def on_success(req, result):
            if 'job_id' in result:
                data['dl_job_id'] = result['job_id']
                self.poll_download(data)
            else:
                data['download_status'] = 'error'
                data['dl_error'] = result.get('error', 'Невідома помилка')
                self._render_card(data['widget'], data)
        def on_failure(req, error):
            data['download_status'] = 'error'
            data['dl_error'] = str(error)
            self._render_card(data['widget'], data)

        UrlRequest('http://127.0.0.1:8899/api/download',
                   req_body=json.dumps(payload),
                   method='POST',
                   on_success=on_success,
                   on_failure=on_failure,
                   req_headers={'Content-Type': 'application/json'})

    def poll_download(self, data):
        job_id = data['dl_job_id']
        def check(req, result):
            if result.get('status') == 'done':
                data['download_status'] = 'done'
                data['dl_filename'] = result.get('filename')
                self._render_card(data['widget'], data)
                self.save_file(job_id, data['dl_filename'])
            elif result.get('status') == 'error':
                data['download_status'] = 'error'
                data['dl_error'] = result.get('error', 'Помилка завантаження')
                self._render_card(data['widget'], data)
            else:
                # ще завантажується – повторюємо через 1 секунду
                Clock.schedule_once(lambda dt: self.poll_download(data), 1)
        UrlRequest(f'http://127.0.0.1:8899/api/status/{job_id}',
                   on_success=check, on_failure=lambda req, err: None)

    def save_file(self, job_id, filename):
        # Завантажуємо файл із сервера та зберігаємо в Downloads Android
        from android.storage import primary_external_storage_path
        from android.permissions import request_permissions, Permission
        import shutil
        request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
        download_url = f'http://127.0.0.1:8899/api/file/{job_id}'
        resp = requests.get(download_url, stream=True)
        if resp.status_code == 200:
            downloads_dir = os.path.join(primary_external_storage_path(), 'Download')
            os.makedirs(downloads_dir, exist_ok=True)
            local_path = os.path.join(downloads_dir, filename)
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(resp.raw, f)
            from kivy.utils import platform
            if platform == 'android':
                from jnius import autoclass
                MediaScannerConnection = autoclass('android.media.MediaScannerConnection')
                context = autoclass('org.kivy.android.PythonActivity').mActivity
                MediaScannerConnection.scanFile(context, [local_path], None, None)

    def download_all(self):
        for data in self.cards_data:
            if data.get('status') == 'ready' and data.get('download_status') not in ('downloading', 'done'):
                self.start_download(data)

    def refresh_all_cards(self):
        for data in self.cards_data:
            if data['status'] == 'ready':
                self._render_card(data['widget'], data)

    def _format_duration(self, seconds):
        if not seconds:
            return ''
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f'{m}:{s:02d}'

# Додаткові класи для віджетів (щоб KV посилання працювали)
class Card(BoxLayout): pass
class QualityChip(ToggleButton): pass
class DownloadButton(Button): pass

if __name__ == '__main__':
    DVLoadApp().run()