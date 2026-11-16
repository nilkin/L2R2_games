#!/usr/bin/env python3
"""
Zuzu və Rəqəmlər — voice clip generator.

Generates every phrase the game speaks, in AZ / RU / EN, with Microsoft neural
voices (via edge-tts), trims the silence at both ends and re-encodes to small
mono MP3s:

    reqemler/audio/az/<key>.mp3, audio/ru/<key>.mp3, audio/en/<key>.mp3
    reqemler/audio/manifest.js   ->  window.AUD_PACK = {lang: {key: [text, ms]}}

The game builds sentences as lists of these keys (e.g. ["n47", "find_t"]) and
plays them back-to-back. If you change a text here, delete the matching mp3
(or use --force) and run again.

Setup (outside the repo, e.g. in a venv):
    python -m venv venv
    venv/Scripts/pip install edge-tts miniaudio lameenc      (Windows)
    venv/bin/pip install edge-tts miniaudio lameenc          (macOS / Linux)
Run:
    venv/Scripts/python reqemler/tools/make_audio.py           (only missing clips)
    venv/Scripts/python reqemler/tools/make_audio.py --force   (regenerate all)
    venv/Scripts/python reqemler/tools/make_audio.py --lang az (one language)
"""
import argparse, asyncio, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.normpath(os.path.join(HERE, '..', 'audio'))

VOICES = {
    'az': dict(voice='az-AZ-BanuNeural',     rate='-5%', pitch='+8Hz'),
    'ru': dict(voice='ru-RU-SvetlanaNeural', rate='-5%', pitch='+6Hz'),
    'en': dict(voice='en-US-AnaNeural',      rate='-5%', pitch='+0Hz'),
}
SR = 24000          # edge-tts native sample rate
KBPS = 40           # mono MP3 bitrate
PAD_LEAD = 0.025    # seconds of silence kept before speech
PAD_TRAIL = 0.07    # seconds kept after speech

# ---------------------------------------------------------------- numbers
AZ_U = ['sıfır', 'bir', 'iki', 'üç', 'dörd', 'beş', 'altı', 'yeddi', 'səkkiz', 'doqquz']
AZ_T = ['', 'on', 'iyirmi', 'otuz', 'qırx', 'əlli', 'altmış', 'yetmiş', 'səksən', 'doxsan']
RU_U = ['ноль', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
RU_TEEN = ['десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 'пятнадцать',
           'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать']
RU_T = ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто']
EN_U = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
EN_TEEN = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
EN_T = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']


def word(lang, n):
    t, o = divmod(n, 10)
    if lang == 'az':
        if n == 100: return 'yüz'
        if n < 10: return AZ_U[n]
        return AZ_T[t] + ('' if o == 0 else ' ' + AZ_U[o])
    if lang == 'ru':
        if n == 100: return 'сто'
        if n < 10: return RU_U[n]
        if n < 20: return RU_TEEN[n - 10]
        return RU_T[t] + ('' if o == 0 else ' ' + RU_U[o])
    if n == 100: return 'one hundred'
    if n < 10: return EN_U[n]
    if n < 20: return EN_TEEN[n - 10]
    return EN_T[t] + ('' if o == 0 else '-' + EN_U[o])


# Azerbaijani ablative (-dan/-dən) of 0..10: "beşdən", "ondan"
AZ_ABL = ['sıfırdan', 'birdən', 'ikidən', 'üçdən', 'dörddən', 'beşdən', 'altıdan', 'yeddidən', 'səkkizdən', 'doqquzdan', 'ondan']


def cap(s):
    return s[:1].upper() + s[1:]


# ---------------------------------------------------------------- phrases
def phrases(lang):
    w = lambda n: word(lang, n)
    P = {}
    for n in range(0, 101):
        P['n%d' % n] = w(n)

    if lang == 'az':
        P.update({
            'hello': 'Salam! Mən Zuzuyam. Gəl rəqəmlərlə oynayaq!',
            'few': 'Zuzu hələ acdır! Daha ver!',
            'many': 'Ay-ay, çox oldu! Gəl yenidən sayaq.',
            'count': 'Neçədir? Toxun və say!',
            'train': 'Hansı rəqəm yoxdur?',
            'more': 'Zuzu acdır! Harada çoxdur?',
            'fewer': 'Zuzu toxdur! Harada azdır?',
            'bigger': 'Hansı rəqəm böyükdür?',
            'smaller': 'Hansı rəqəm kiçikdir?',
            'low': 'Qüllə alçaqdır! Kub əlavə et.',
            'high': 'Qüllə çox hündürdür! Kub götür.',
            'eggs': 'Neçə yumurta var?',
            'cubes': 'Neçə kub var? Onluqları və təklikləri say!',
            'giggle': 'Hi-hi!',
            'ask_add': 'Neçə olur?',
            'ask_sub': 'Neçə qaldı?',
            'find_t': 'harada?',
        })
        tries = ['Yenə cəhd et!', 'Bir də bax!', 'Az qaldı!']
        praise = ['Afərin!', 'Əla!', 'Super!', 'Bravo!', 'Çox gözəl!', 'Möhtəşəm!', 'Sən bacarırsan!']
        stars = ['Ura! Bir ulduz!', 'Ura! İki ulduz!', 'Ura! Üç ulduz!']
        for n in range(1, 9): P['feed_%d' % n] = 'Zuzu %s dənə istəyir!' % w(n)
        for n in range(0, 11): P['find_%d' % n] = '%s harada?' % cap(w(n))
        for n in range(1, 7): P['match_%d' % n] = 'Harada %s dənə var?' % w(n)
        for n in range(3, 11): P['tower_%d' % n] = '%s kubdan qüllə qur!' % cap(w(n))
        for b in range(1, 11):
            P['cmp_more_%d' % b] = '%s çoxdur!' % AZ_ABL[b]
            P['cmp_fewer_%d' % b] = '%s azdır!' % AZ_ABL[b]
            P['cmp_bigger_%d' % b] = '%s böyükdür!' % AZ_ABL[b]
            P['cmp_smaller_%d' % b] = '%s kiçikdir!' % AZ_ABL[b]
        for b in range(1, 10): P['plus_%d' % b] = 'üstəgəl %s' % w(b)
        for b in range(1, 11): P['minus_%d' % b] = 'çıx %s' % w(b)
        for c in range(0, 11): P['eq_%d' % c] = '%s edir!' % w(c)
        for k in range(1, 11): P['tens_%d' % k] = 'On və %s — %s!' % (w(k), w(10 + k))
        for t in range(1, 11): P['tn_%d' % t] = '%s onluq' % w(t)
        for o in range(1, 10): P['on_%d' % o] = '%s təklik' % w(o)

    elif lang == 'ru':
        P.update({
            'hello': 'Привет! Я Зузу. Давай играть с цифрами!',
            'few': 'Зузу ещё голодный! Дай ещё!',
            'many': 'Ой, слишком много! Давай посчитаем заново.',
            'count': 'Сколько их? Нажимай и считай!',
            'train': 'Какого числа не хватает?',
            'more': 'Зузу голодный! Где больше?',
            'fewer': 'Зузу сытый! Где меньше?',
            'bigger': 'Какое число больше?',
            'smaller': 'Какое число меньше?',
            'low': 'Башня низкая! Добавь кубик.',
            'high': 'Слишком высокая! Убери кубик.',
            'eggs': 'Сколько яиц?',
            'cubes': 'Сколько кубиков? Считай десятки и единицы!',
            'giggle': 'Хи-хи!',
            'ask_add': 'Сколько будет?',
            'ask_sub': 'Сколько осталось?',
            'find_h': 'Найди число',
        })
        tries = ['Попробуй ещё!', 'Посмотри ещё раз!', 'Почти!']
        praise = ['Молодец!', 'Отлично!', 'Супер!', 'Браво!', 'Здорово!', 'Умница!', 'Ура!']
        stars = ['Ура! Одна звезда!', 'Ура! Две звезды!', 'Ура! Три звезды!']
        for n in range(1, 9): P['feed_%d' % n] = 'Зузу хочет %s!' % w(n)
        for n in range(0, 11): P['find_%d' % n] = 'Где %s?' % w(n)
        for n in range(1, 7): P['match_%d' % n] = 'Где их %s?' % w(n)
        for n in range(3, 11): P['tower_%d' % n] = 'Построй башню: %s!' % w(n)
        for b in range(1, 11):
            P['cmp_more_%d' % b] = P['cmp_bigger_%d' % b] = 'больше, чем %s!' % w(b)
            P['cmp_fewer_%d' % b] = P['cmp_smaller_%d' % b] = 'меньше, чем %s!' % w(b)
        for b in range(1, 10): P['plus_%d' % b] = 'плюс %s' % w(b)
        for b in range(1, 11): P['minus_%d' % b] = 'минус %s' % w(b)
        for c in range(0, 11): P['eq_%d' % c] = 'будет %s!' % w(c)
        for k in range(1, 11): P['tens_%d' % k] = 'Десять и %s — %s!' % (w(k), w(10 + k))
        TN = {1: 'один десяток', 2: 'два десятка', 3: 'три десятка', 4: 'четыре десятка'}
        for t in range(1, 11): P['tn_%d' % t] = TN.get(t, '%s десятков' % w(t))
        ON = {1: 'и одна единица', 2: 'и две единицы', 3: 'и три единицы', 4: 'и четыре единицы'}
        for o in range(1, 10): P['on_%d' % o] = ON.get(o, 'и %s единиц' % w(o))

    else:
        P.update({
            'hello': "Hi! I'm Zuzu. Let's play with numbers!",
            'few': 'Zuzu is still hungry! More, please!',
            'many': "Oops, too many! Let's count again.",
            'count': 'How many? Tap and count!',
            'train': 'Which number is missing?',
            'more': 'Zuzu is hungry! Which has more?',
            'fewer': 'Zuzu is full! Which has fewer?',
            'bigger': 'Which number is bigger?',
            'smaller': 'Which number is smaller?',
            'low': 'Too short! Add a block.',
            'high': 'Too tall! Take one off.',
            'eggs': 'How many eggs?',
            'cubes': 'How many cubes? Count the tens and the ones!',
            'giggle': 'Hee-hee!',
            'ask_add': 'How many?',
            'ask_sub': 'How many are left?',
            'find_h': 'Find the number',
        })
        tries = ['Try again!', 'Look again!', 'Almost!']
        praise = ['Great job!', 'Awesome!', 'Super!', 'Well done!', 'Hooray!', 'You did it!', 'Fantastic!']
        stars = ['Hooray! One star!', 'Hooray! Two stars!', 'Hooray! Three stars!']
        for n in range(1, 9): P['feed_%d' % n] = 'Zuzu wants %s!' % w(n)
        for n in range(0, 11): P['find_%d' % n] = 'Where is %s?' % w(n)
        for n in range(1, 7): P['match_%d' % n] = 'Find %s!' % w(n)
        for n in range(3, 11): P['tower_%d' % n] = 'Build a tower of %s!' % w(n)
        for b in range(1, 11):
            P['cmp_more_%d' % b] = 'is more than %s!' % w(b)
            P['cmp_fewer_%d' % b] = 'is less than %s!' % w(b)
            P['cmp_bigger_%d' % b] = 'is bigger than %s!' % w(b)
            P['cmp_smaller_%d' % b] = 'is smaller than %s!' % w(b)
        for b in range(1, 10): P['plus_%d' % b] = 'plus %s' % w(b)
        for b in range(1, 11): P['minus_%d' % b] = 'take away %s' % w(b)
        for c in range(0, 11): P['eq_%d' % c] = 'is %s!' % w(c)
        for k in range(1, 11): P['tens_%d' % k] = 'Ten and %s is %s!' % (w(k), w(10 + k))
        for t in range(1, 11): P['tn_%d' % t] = 'one ten' if t == 1 else '%s tens' % w(t)
        for o in range(1, 10): P['on_%d' % o] = 'and one one' if o == 1 else 'and %s ones' % w(o)

    for i, s in enumerate(tries): P['try_%d' % i] = s
    for i, s in enumerate(praise): P['praise_%d' % i] = s
    for i, s in enumerate(stars): P['stars_%d' % (i + 1)] = s
    return P


# ---------------------------------------------------------------- audio
def trim_encode(mp3_bytes):
    """Decode, cut leading/trailing silence, re-encode. Returns (bytes, ms)."""
    import miniaudio, lameenc, array
    d = miniaudio.decode(mp3_bytes, output_format=miniaudio.SampleFormat.SIGNED16, nchannels=1, sample_rate=SR)
    s = d.samples
    th = 350
    first = next((i for i, x in enumerate(s) if abs(x) > th), 0)
    last = next((len(s) - i for i, x in enumerate(reversed(s)) if abs(x) > th), len(s))
    a = max(0, first - int(PAD_LEAD * SR))
    b = min(len(s), last + int(PAD_TRAIL * SR))
    cut = array.array('h', s[a:b])
    f = min(len(cut) // 2, int(.006 * SR))        # tiny fades: no clicks
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


def mp3_ms(path):
    import miniaudio
    i = miniaudio.mp3_get_file_info(path)
    return int(i.duration * 1000)


async def build(langs, force, jobs):
    manifest_path = os.path.join(AUDIO, 'manifest.js')
    old = {}
    if os.path.exists(manifest_path):
        try:
            raw = open(manifest_path, encoding='utf-8').read()
            old = json.loads(raw[raw.index('{'):raw.rindex('}') + 1])
        except Exception:
            old = {}
    pack = {}
    sem = asyncio.Semaphore(jobs)
    for lang in ('az', 'ru', 'en'):
        P = phrases(lang)
        if lang not in langs:
            if lang in old: pack[lang] = old[lang]
            continue
        cfg = VOICES[lang]
        d = os.path.join(AUDIO, lang)
        os.makedirs(d, exist_ok=True)
        entry = {}
        prev = old.get(lang, {})

        async def one(key, text):
            path = os.path.join(d, key + '.mp3')
            if not force and os.path.exists(path) and prev.get(key, [None])[0] == text:
                entry[key] = [text, prev[key][1]]
                return
            async with sem:
                for attempt in range(4):
                    try:
                        raw = await tts(text, cfg)
                        data, ms = trim_encode(raw)
                        open(path, 'wb').write(data)
                        entry[key] = [text, ms]
                        print(lang, key, ms, 'ms', len(data), 'B')
                        return
                    except Exception as e:
                        print('retry', lang, key, e, file=sys.stderr)
                        await asyncio.sleep(1.5 * (attempt + 1))
                raise RuntimeError('failed: %s %s' % (lang, key))

        await asyncio.gather(*(one(k, t) for k, t in P.items()))
        # remove clips that are no longer used
        for f in os.listdir(d):
            if f.endswith('.mp3') and f[:-4] not in P:
                os.remove(os.path.join(d, f))
        pack[lang] = {k: entry[k] for k in P}

    js = ('/* Generated by tools/make_audio.py — do not edit by hand.\n'
          '   lang -> key -> [spoken text, duration ms]; file = audio/<lang>/<key>.mp3 */\n'
          'window.AUD_PACK=' + json.dumps(pack, ensure_ascii=False, separators=(',', ':')) + ';\n')
    open(manifest_path, 'w', encoding='utf-8', newline='\n').write(js)
    for lang in pack:
        print(lang, len(pack[lang]), 'clips')


def check():
    """Offline check: phrase list == manifest == files on disk, texts up to date."""
    raw = open(os.path.join(AUDIO, 'manifest.js'), encoding='utf-8').read()
    pack = json.loads(raw[raw.index('{'):raw.rindex('}') + 1])
    ok = True
    for lang in ('az', 'ru', 'en'):
        P = phrases(lang)
        man = pack.get(lang, {})
        d = os.path.join(AUDIO, lang)
        files = {f[:-4] for f in os.listdir(d) if f.endswith('.mp3')} if os.path.isdir(d) else set()
        problems = {
            'not in manifest': sorted(set(P) - set(man)),
            'missing mp3': sorted(k for k in man if k not in files),
            'mp3 not in manifest': sorted(files - set(man)),
            'stale text': sorted(k for k in P if k in man and man[k][0] != P[k]),
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
    ap.add_argument('--lang', choices=['az', 'ru', 'en'], action='append', help='only these languages')
    ap.add_argument('--jobs', type=int, default=6, help='parallel TTS requests')
    ap.add_argument('--check', action='store_true', help='only verify manifest and files (no network)')
    a = ap.parse_args()
    if a.check:
        sys.exit(0 if check() else 1)
    asyncio.run(build(a.lang or ['az', 'ru', 'en'], a.force, a.jobs))
