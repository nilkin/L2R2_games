#!/usr/bin/env python3
"""
Bubu və Dünya — voice clip generator.

Every phrase the game speaks is defined HERE (single source of truth). The game
shows the same text in its speech bubble, read from audio/manifest.js.

    dunya/audio/az/<key>.mp3, audio/ru/<key>.mp3, audio/en/<key>.mp3
    dunya/audio/manifest.js   ->  window.AUD_PACK = {lang: {key: [text, ms]}}

Setup (outside the repo, e.g. in a venv):
    python -m venv venv
    venv/Scripts/pip install edge-tts miniaudio lameenc      (Windows)
    venv/bin/pip install edge-tts miniaudio lameenc          (macOS / Linux)
Run:
    venv/Scripts/python dunya/tools/make_audio.py           (only changed / missing clips)
    venv/Scripts/python dunya/tools/make_audio.py --force   (regenerate all)
    python dunya/tools/make_audio.py --check                (offline check)
"""
import argparse, asyncio, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.normpath(os.path.join(HERE, '..', 'audio'))
LANGS = ('az', 'ru', 'en')
LI = {l: i for i, l in enumerate(LANGS)}

# Child-like voice: TTS pitch up + a "shift" (render slower, then play faster: raises pitch AND
# formants, so the voice sounds smaller/younger while the tempo stays natural).
# shift 1.0 = off. Final tempo ~ (1 + rate) * shift.
VOICES = {
    'az': dict(voice='az-AZ-BanuNeural',     rate='-17%', pitch='+20Hz', shift=1.20),
    'ru': dict(voice='ru-RU-SvetlanaNeural', rate='-17%', pitch='+18Hz', shift=1.20),
    'en': dict(voice='en-US-AnaNeural',      rate='-10%', pitch='+6Hz',  shift=1.08),   # Ana is already a child voice
}
SR = 24000
KBPS = 40
PAD_LEAD = 0.025
PAD_TRAIL = 0.07

# ------------------------------------------------------------------ data
# id: (az, ru, en)
COLORS = {
    'red':    ('Qırmızı',   'Красный',    'Red'),
    'yellow': ('Sarı',      'Жёлтый',     'Yellow'),
    'blue':   ('Mavi',      'Синий',      'Blue'),
    'green':  ('Yaşıl',     'Зелёный',    'Green'),
    'orange': ('Narıncı',   'Оранжевый',  'Orange'),
    'purple': ('Bənövşəyi', 'Фиолетовый', 'Purple'),
    'pink':   ('Çəhrayı',   'Розовый',    'Pink'),
    'brown':  ('Qəhvəyi',   'Коричневый', 'Brown'),
}
# "X-dır" (az predicate) and ru feminine form, used by the paint stage
COLOR_AZ_IS = {'red': 'qırmızıdır', 'yellow': 'sarıdır', 'blue': 'mavidir', 'green': 'yaşıldır',
               'orange': 'narıncıdır', 'purple': 'bənövşəyidir', 'pink': 'çəhrayıdır', 'brown': 'qəhvəyidir'}
COLOR_RU_F = {'red': 'красная', 'yellow': 'жёлтая', 'blue': 'синяя', 'green': 'зелёная',
              'orange': 'оранжевая', 'purple': 'фиолетовая', 'pink': 'розовая', 'brown': 'коричневая'}

SHAPES = {
    'circle':   ('Dairə',       'Круг',          'Circle'),
    'square':   ('Kvadrat',     'Квадрат',       'Square'),
    'triangle': ('Üçbucaq',     'Треугольник',   'Triangle'),
    'rect':     ('Düzbucaqlı',  'Прямоугольник', 'Rectangle'),
    'star':     ('Ulduz',       'Звезда',        'Star'),
    'heart':    ('Ürək',        'Сердце',        'Heart'),
}
FARM = {
    'cat':     ('Pişik',  'Кошка',  'Cat'),
    'dog':     ('İt',     'Собака', 'Dog'),
    'cow':     ('İnək',   'Корова', 'Cow'),
    'horse':   ('At',     'Лошадь', 'Horse'),
    'sheep':   ('Qoyun',  'Овца',   'Sheep'),
    'goat':    ('Keçi',   'Коза',   'Goat'),
    'hen':     ('Toyuq',  'Курица', 'Hen'),
    'duck':    ('Ördək',  'Утка',   'Duck'),
    'rabbit':  ('Dovşan', 'Кролик', 'Rabbit'),
    'rooster': ('Xoruz',  'Петух',  'Rooster'),
    'frog':    ('Qurbağa', 'Лягушка', 'Frog'),
}
WILD = {
    'lion':     ('Şir',     'Лев',      'Lion'),
    'elephant': ('Fil',     'Слон',     'Elephant'),
    'giraffe':  ('Zürafə',  'Жираф',    'Giraffe'),
    'monkey':   ('Meymun',  'Обезьяна', 'Monkey'),
    'bear':     ('Ayı',     'Медведь',  'Bear'),
    'wolf':     ('Canavar', 'Волк',     'Wolf'),
    'fox':      ('Tülkü',   'Лиса',     'Fox'),
    'zebra':    ('Zebr',    'Зебра',    'Zebra'),
    'tiger':    ('Pələng',  'Тигр',     'Tiger'),
    'croc':     ('Timsah',  'Крокодил', 'Crocodile'),
}
# animal sounds: id: (az, ru, en)
SOUNDS = {
    'cat':     ('miyov-miyov',     'мяу-мяу',  'meow, meow'),
    'dog':     ('hav-hav',         'гав-гав',  'woof, woof'),
    'cow':     ('mö-ö-ö',          'му-у-у',   'moo'),
    'sheep':   ('mə-ə-ə',          'бе-е-е',   'baa'),
    'hen':     ('qıd-qıd-qıdaq',   'ко-ко-ко', 'cluck, cluck'),
    'duck':    ('vaq-vaq',         'кря-кря',  'quack, quack'),
    'frog':    ('qur-qur',         'ква-ква',  'ribbit, ribbit'),
    'rooster': ('quqquluqu',       'кукареку', 'cock-a-doodle-doo'),
}
BODY = {
    'eye':   ('Göz',    'Глаз', 'Eye'),
    'nose':  ('Burun',  'Нос',  'Nose'),
    'ear':   ('Qulaq',  'Ухо',  'Ear'),
    'mouth': ('Ağız',   'Рот',  'Mouth'),
    'hand':  ('Əl',     'Рука', 'Hand'),
    'foot':  ('Ayaq',   'Нога', 'Foot'),
    'tooth': ('Diş',    'Зуб',  'Tooth'),
}
SEASONS = {   # name, "find" prompt, answer
    'spring': (('Yaz', 'Весна', 'Spring'), ('Yazı tap!', 'Найди весну!', 'Find spring!'),
               ('Bu yazdır! Çiçəklər açır.', 'Это весна! Цветут цветы.', 'This is spring! Flowers bloom.')),
    'summer': (('Yay', 'Лето', 'Summer'), ('Yayı tap!', 'Найди лето!', 'Find summer!'),
               ('Bu yaydır! Hava istidir.', 'Это лето! Жарко.', "This is summer! It's hot.")),
    'autumn': (('Payız', 'Осень', 'Autumn'), ('Payızı tap!', 'Найди осень!', 'Find autumn!'),
               ('Bu payızdır! Yarpaqlar tökülür.', 'Это осень! Падают листья.', 'This is autumn! Leaves fall.')),
    'winter': (('Qış', 'Зима', 'Winter'), ('Qışı tap!', 'Найди зиму!', 'Find winter!'),
               ('Bu qışdır! Qar yağır.', 'Это зима! Идёт снег.', "This is winter! It's snowing.")),
}
# fruit / vegetable: id: (name az, ru, en), (answer az, ru, en)
FRUITS = {
    'apple':     ('Alma',     'Яблоко',   'An apple'),
    'pear':      ('Armud',    'Груша',    'A pear'),
    'banana':    ('Banan',    'Банан',    'A banana'),
    'orangef':   ('Portağal', 'Апельсин', 'An orange'),
    'peach':     ('Şaftalı',  'Персик',   'A peach'),
    'lemon':     ('Limon',    'Лимон',    'A lemon'),
    'pineapple': ('Ananas',   'Ананас',   'A pineapple'),
    'kiwi':      ('Kivi',     'Киви',     'A kiwi'),
}
VEG = {
    'carrot':   ('Kök',       'Морковь',  'A carrot'),
    'cucumber': ('Xiyar',     'Огурец',   'A cucumber'),
    'tomato':   ('Pomidor',   'Помидор',  'A tomato'),
    'potato':   ('Kartof',    'Картошка', 'A potato'),
    'eggplant': ('Badımcan',  'Баклажан', 'An eggplant'),
    'corn':     ('Qarğıdalı', 'Кукуруза', 'Corn'),
    'onion':    ('Soğan',     'Лук',      'An onion'),
    'broccoli': ('Brokoli',   'Брокколи', 'Broccoli'),
}
# paint stage: object -> (color, az name, ru name, ru gender, en name, en plural?)
PAINT = {
    'banana':     ('yellow', 'Banan',     'банан',     'm', 'banana',     False),
    'strawberry': ('red',    'Çiyələk',   'клубника',  'f', 'strawberry', False),
    'carrot':     ('orange', 'Kök',       'морковка',  'f', 'carrot',     False),
    'grapes':     ('purple', 'Üzüm',      'виноград',  'm', 'grapes',     True),
    'frog':       ('green',  'Qurbağa',   'лягушка',   'f', 'frog',       False),
    'whale':      ('blue',   'Balina',    'кит',       'm', 'whale',      False),
    'chick':      ('yellow', 'Cücə',      'цыплёнок',  'm', 'chick',      False),
    'tomato':     ('red',    'Pomidor',   'помидор',   'm', 'tomato',     False),
    'orangef':    ('orange', 'Portağal',  'апельсин',  'm', 'orange',     False),
    'eggplant':   ('purple', 'Badımcan',  'баклажан',  'm', 'eggplant',   False),
    'cucumber':   ('green',  'Xiyar',     'огурец',    'm', 'cucumber',   False),
    'flower':     ('pink',   'Çiçək',     'цветок',    'm', 'flower',     False),
    'bear':       ('brown',  'Ayı',       'медведь',   'm', 'bear',       False),
    'drop':       ('blue',   'Damla',     'капля',     'f', 'water drop', False),
    'flamingo':   ('pink',   'Flaminqo',  'фламинго',  'm', 'flamingo',   False),
    'chestnut':   ('brown',  'Şabalıd',   'каштан',    'm', 'chestnut',   False),
}

# names with a recorded voice clip (others are shown on screen only): id: (az, ru, en)
NAMES = {
    'emilya': ('Emilya', 'Эмилия', 'Emilya'),
}

COMMON = {
    'hello':   ('Salam! Mən Bubuyam. Gəl birlikdə öyrənək!', 'Привет! Я Бубу. Давай учиться вместе!', "Hi! I'm Bubu. Let's learn together!"),
    'who':     ('Kim oynayır? Qız, yoxsa oğlan?', 'Кто играет? Девочка или мальчик?', "Who's playing? A girl or a boy?"),
    'girl':    ('Qız!', 'Девочка!', 'A girl!'),
    'boy':     ('Oğlan!', 'Мальчик!', 'A boy!'),
    'giggle':  ('Hu-hu!', 'Ух-ух!', 'Hoo-hoo!'),
    'q_big':   ('Hansı böyükdür?', 'Какой из них большой?', 'Which one is big?'),
    'q_small': ('Hansı kiçikdir?', 'Какой из них маленький?', 'Which one is small?'),
    'q_long':  ('Hansı uzundur?',  'Какой из них длинный?', 'Which one is long?'),
    'q_short': ('Hansı qısadır?',  'Какой из них короткий?', 'Which one is short?'),
    'r_big':   ('Bu böyükdür!',  'Этот большой!',   'This one is big!'),
    'r_small': ('Bu kiçikdir!',  'Этот маленький!', 'This one is small!'),
    'r_long':  ('Bu uzundur!',   'Этот длинный!',   'This one is long!'),
    'r_short': ('Bu qısadır!',   'Этот короткий!',  'This one is short!'),
    'q_fv':    ('Meyvəni səbətə, tərəvəzi qazana qoy!', 'Фрукты — в корзинку, овощи — в кастрюлю!', 'Fruit in the basket, vegetables in the pot!'),
    'q_odd':   ('Hansı artıqdır?', 'Что здесь лишнее?', "Which one doesn't belong?"),
    'q_pat':   ('Sonra hansı gəlir?', 'Что будет дальше?', 'What comes next?'),
    'q_sort':  ('Fiqurları öz yerinə qoy!', 'Поставь фигуры на место!', 'Put the shapes in their places!'),
}
TRIES = (['Yenə cəhd et!', 'Bir də bax!', 'Az qaldı!'],
         ['Попробуй ещё!', 'Посмотри ещё раз!', 'Почти!'],
         ['Try again!', 'Look again!', 'Almost!'])
PRAISE = (['Afərin!', 'Əla!', 'Super!', 'Bravo!', 'Çox gözəl!', 'Möhtəşəm!', 'Sən bacardın!'],
          ['Молодец!', 'Отлично!', 'Супер!', 'Браво!', 'Здорово!', 'Умница!', 'Ура!'],
          ['Great job!', 'Awesome!', 'Super!', 'Well done!', 'Hooray!', 'You did it!', 'Fantastic!'])
STARS = (['Ura! Bir ulduz!', 'Ura! İki ulduz!', 'Ura! Üç ulduz!'],
         ['Ура! Одна звезда!', 'Ура! Две звезды!', 'Ура! Три звезды!'],
         ['Hooray! One star!', 'Hooray! Two stars!', 'Hooray! Three stars!'])


def low(s):
    return s[:1].lower() + s[1:]


def where(lang, name):
    """'X haradadır?' / 'Где X?' / 'Where is the X?'"""
    if lang == 'az': return '%s haradadır?' % name
    if lang == 'ru': return 'Где %s?' % low(name)
    return 'Where is the %s?' % low(name)


# ------------------------------------------------------------------ phrases
def phrases(lang):
    i = LI[lang]
    P = {}
    for k, v in COMMON.items(): P[k] = v[i]
    for n, s in enumerate(TRIES[i]): P['try_%d' % n] = s
    for n, s in enumerate(PRAISE[i]): P['praise_%d' % n] = s
    for n, s in enumerate(STARS[i]): P['stars_%d' % (n + 1)] = s
    for k, v in NAMES.items():
        P['nm_' + k] = v[i] + '!'
        P['hi_' + k] = ('Salam, %s! Mən Bubuyam. Gəl birlikdə öyrənək!', 'Привет, %s! Я Бубу. Давай учиться вместе!',
                        "Hi, %s! I'm Bubu. Let's learn together!")[i] % v[i]

    # colors: name + "where is the <color> balloon?"
    for c, v in COLORS.items():
        P['n_' + c] = v[i]
        P['qb_' + c] = ('%s şar haradadır?' % v[0], 'Где %s шарик?' % low(v[1]), 'Where is the %s balloon?' % low(v[2]))[i]
    # shapes, animals, body parts: name + "where is X?"
    for table in (SHAPES, FARM, WILD, BODY):
        for k, v in table.items():
            P['n_' + k] = v[i]
            P['q_' + k] = where(lang, v[i])
    # animal sounds: "who says moo?" / "the cow says moo!"
    for k, s in SOUNDS.items():
        name = FARM[k][i]
        P['qs_' + k] = ('Kim deyir: %s?' % s[0], 'Кто говорит: %s?' % s[1], 'Who says %s?' % s[2])[i]
        P['rs_' + k] = ('%s deyir: %s!' % (name, s[0]), '%s говорит: %s!' % (name, s[1]), 'The %s says %s!' % (low(name), s[2]))[i]
    # seasons
    for k, (nm, q, r) in SEASONS.items():
        P['n_' + k] = nm[i]; P['q_' + k] = q[i]; P['r_' + k] = r[i]
    # fruit & vegetables
    for table, kind in ((FRUITS, 'f'), (VEG, 'v')):
        for k, v in table.items():
            if lang == 'en':
                bare = v[2].split(' ', 1)[1] if v[2].split(' ', 1)[0] in ('A', 'An') else v[2]
                P['n_' + k] = bare[:1].upper() + bare[1:]
                P['r_' + k] = '%s is a %s!' % (v[2], 'fruit' if kind == 'f' else 'vegetable')
            elif lang == 'ru':
                P['n_' + k] = v[1]
                P['r_' + k] = '%s — это %s!' % (v[1], 'фрукт' if kind == 'f' else 'овощ')
            else:
                P['n_' + k] = v[0]
                P['r_' + k] = '%s %s!' % (v[0], 'meyvədir' if kind == 'f' else 'tərəvəzdir')
    # paint: "what color is X?" / "X is yellow!"
    for k, (c, az, ru, g, en, pl) in PAINT.items():
        if lang == 'az':
            P['pq_' + k] = '%s hansı rəngdədir?' % az
            P['pr_' + k] = '%s %s!' % (az, COLOR_AZ_IS[c])
        elif lang == 'ru':
            col = COLOR_RU_F[c] if g == 'f' else low(COLORS[c][1])
            P['pq_' + k] = 'Какого цвета %s?' % ru
            P['pr_' + k] = '%s %s!' % (ru[:1].upper() + ru[1:], col)
        else:
            P['pq_' + k] = 'What color %s the %s?' % ('are' if pl else 'is', en)
            P['pr_' + k] = 'The %s %s %s!' % (en, 'are' if pl else 'is', low(COLORS[c][2]))
    return P


# ------------------------------------------------------------------ audio
def trim_encode(mp3_bytes, shift=1.0):
    """Decode, optional pitch/formant shift, cut leading/trailing silence, re-encode. Returns (bytes, ms)."""
    import miniaudio, lameenc, array
    F = miniaudio.SampleFormat.SIGNED16
    d = miniaudio.decode(mp3_bytes, output_format=F, nchannels=1, sample_rate=SR)
    s = d.samples
    if shift and abs(shift - 1) > 1e-3:
        # treat the audio as if recorded at SR*shift and resample to SR: higher and faster
        s = array.array('h', bytes(miniaudio.convert_frames(F, 1, int(round(SR * shift)), s.tobytes(), F, 1, SR)))
    th = 350
    first = next((i for i, x in enumerate(s) if abs(x) > th), 0)
    last = next((len(s) - i for i, x in enumerate(reversed(s)) if abs(x) > th), len(s))
    a = max(0, first - int(PAD_LEAD * SR))
    b = min(len(s), last + int(PAD_TRAIL * SR))
    cut = array.array('h', s[a:b])
    f = min(len(cut) // 2, int(.006 * SR))
    for i in range(f):
        cut[i] = int(cut[i] * i / f)
        cut[-1 - i] = int(cut[-1 - i] * i / f)
    enc = lameenc.Encoder()
    enc.set_bit_rate(KBPS); enc.set_in_sample_rate(SR); enc.set_channels(1); enc.set_quality(2)
    out = enc.encode(cut.tobytes()) + enc.flush()
    return out, int(len(cut) * 1000 / SR)


async def tts(text, cfg):
    import edge_tts
    buf = bytearray()
    com = edge_tts.Communicate(text, cfg['voice'], rate=cfg['rate'], pitch=cfg['pitch'])
    async for ch in com.stream():
        if ch['type'] == 'audio':
            buf += ch['data']
    if not buf:
        raise RuntimeError('empty audio')
    return bytes(buf)


def read_manifest():
    path = os.path.join(AUDIO, 'manifest.js')
    if not os.path.exists(path):
        return {}
    raw = open(path, encoding='utf-8').read()
    return json.loads(raw[raw.index('{'):raw.rindex('}') + 1])


async def build(langs, force, jobs):
    try:
        old = read_manifest()
    except Exception:
        old = {}
    pack = {}
    sem = asyncio.Semaphore(jobs)
    for lang in LANGS:
        P = phrases(lang)
        if lang not in langs:
            if lang in old: pack[lang] = old[lang]
            continue
        cfg = VOICES[lang]
        d = os.path.join(AUDIO, lang)
        os.makedirs(d, exist_ok=True)
        entry = {}
        prev = old.get(lang, {})

        sig = '%(voice)s|%(rate)s|%(pitch)s|' % cfg + str(cfg.get('shift', 1.0))   # voice settings: change -> regenerate

        async def one(key, text):
            path = os.path.join(d, key + '.mp3')
            old_e = prev.get(key, [None, 0, None])
            if not force and os.path.exists(path) and old_e[0] == text and (len(old_e) > 2 and old_e[2] == sig):
                entry[key] = [text, old_e[1], sig]
                return
            async with sem:
                for attempt in range(4):
                    try:
                        raw = await tts(text, cfg)
                        data, ms = trim_encode(raw, cfg.get('shift', 1.0))
                        open(path, 'wb').write(data)
                        entry[key] = [text, ms, sig]
                        print(lang, key, ms, 'ms', len(data), 'B')
                        return
                    except Exception as e:
                        print('retry', lang, key, e, file=sys.stderr)
                        await asyncio.sleep(1.5 * (attempt + 1))
                raise RuntimeError('failed: %s %s' % (lang, key))

        await asyncio.gather(*(one(k, t) for k, t in P.items()))
        for f in os.listdir(d):
            if f.endswith('.mp3') and f[:-4] not in P:
                os.remove(os.path.join(d, f))
        pack[lang] = {k: entry[k] for k in P}

    js = ('/* Generated by tools/make_audio.py — do not edit by hand.\n'
          '   lang -> key -> [spoken text, duration ms, voice settings]; file = audio/<lang>/<key>.mp3 */\n'
          'window.AUD_PACK=' + json.dumps(pack, ensure_ascii=False, separators=(',', ':')) + ';\n')
    open(os.path.join(AUDIO, 'manifest.js'), 'w', encoding='utf-8', newline='\n').write(js)
    for lang in pack:
        print(lang, len(pack[lang]), 'clips')


def check():
    """Offline check: phrase list == manifest == files on disk, texts up to date."""
    pack = read_manifest()
    ok = True
    for lang in LANGS:
        P = phrases(lang)
        man = pack.get(lang, {})
        d = os.path.join(AUDIO, lang)
        files = {f[:-4] for f in os.listdir(d) if f.endswith('.mp3')} if os.path.isdir(d) else set()
        problems = {
            'not in manifest': sorted(set(P) - set(man)),
            'missing mp3': sorted(k for k in man if k not in files),
            'mp3 not in manifest': sorted(files - set(man)),
            'stale text': sorted(k for k in P if k in man and man[k][0] != P[k]),
            'old voice settings': sorted(k for k in man if (man[k][2] if len(man[k]) > 2 else None)
                                         != '%(voice)s|%(rate)s|%(pitch)s|' % VOICES[lang] + str(VOICES[lang].get('shift', 1.0)))[:5],
            'empty file': sorted(k for k in files if os.path.getsize(os.path.join(d, k + '.mp3')) < 500),
        }
        size = sum(os.path.getsize(os.path.join(d, k + '.mp3')) for k in files)
        bad = {k: v for k, v in problems.items() if v}
        print('%s: %d phrases, %d clips, %d KB %s' % (lang, len(P), len(files), size // 1024, 'OK' if not bad else bad))
        ok = ok and not bad
    return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='regenerate every clip')
    ap.add_argument('--lang', choices=list(LANGS), action='append', help='only these languages')
    ap.add_argument('--jobs', type=int, default=6, help='parallel TTS requests')
    ap.add_argument('--check', action='store_true', help='only verify manifest and files (no network)')
    ap.add_argument('--list', action='store_true', help='print all phrases (no network)')
    a = ap.parse_args()
    if a.list:
        for lang in LANGS:
            for k, t in phrases(lang).items(): print(lang, k, t)
        sys.exit(0)
    if a.check:
        sys.exit(0 if check() else 1)
    asyncio.run(build(a.lang or list(LANGS), a.force, a.jobs))
