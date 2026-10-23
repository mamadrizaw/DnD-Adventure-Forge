import json, random, re
from datetime import datetime
from pathlib import Path
import streamlit as st

APP_DIR = Path(__file__).parent
SAVE_DIR = APP_DIR / 'saved_adventures'
SAVE_DIR.mkdir(exist_ok=True)
st.set_page_config(page_title='D&D Adventure Forge', page_icon='🐉', layout='wide')

GENRES = {
 'فانتزی حماسی': {'places':['دژ فراموش‌شده','درهٔ مه‌آلود','معبد زیرزمینی','شهر مرزی'], 'threats':['فرقه‌ای مخفی','جادوگری تبعیدی','ارتشی از مردگان','هیولایی باستانی'], 'moods':['باشکوه و پرخطر','رازآلود','قهرمانانه','تاریک']},
 'ترس و بقا': {'places':['دهکده‌ای منزوی','عمارت متروک','جنگل بی‌صدا','معدنی رهاشده'], 'threats':['موجودی که از تاریکی تغذیه می‌کند','طاعونی جادویی','فرقه‌ای مرموز','شکارچی ناشناس'], 'moods':['خفه و اضطراب‌آور','پارانوئید','تاریک','ناامن']},
 'معمایی و کارآگاهی': {'places':['بندر شلوغ','محلهٔ اشرافی','کتابخانهٔ ممنوعه','کاروانسرای بین‌راهی'], 'threats':['توطئه‌ای سیاسی','سرقتی غیرممکن','قتل زنجیره‌ای','شبکه‌ای از جاسوسان'], 'moods':['پر از سرنخ','فریبنده','شهری و پرتنش','رازآلود']},
 'اکتشاف و ماجراجویی': {'places':['جزیره‌ای ناشناخته','ویرانه‌های مدفون','کوهستان نفرین‌شده','جنگل شناور'], 'threats':['تمدنی گمشده','نگهبان باستانی','رقیب اکتشاف‌گر','ناهنجاری جادویی'], 'moods':['شگفت‌انگیز','پرخطر','حس کشف','ماجراجویانه']},
 'طنز و هرج‌ومرج': {'places':['بازار جادویی','مسافرخانه‌ای عجیب','شهر جشنواره‌ها','قلعه‌ای با قوانین مسخره'], 'threats':['جادویی که از کنترل خارج شده','باندی ناشی','اشراف‌زاده‌ای عجیب','هیولایی بدفهمیده‌شده'], 'moods':['آشفته و بامزه','غیرقابل‌پیش‌بینی','سبک','پر از سوءتفاهم']},
}
HOOKS = [
 'درست پیش از طلوع، تمام زنگ‌های شهر هم‌زمان به صدا درمی‌آیند؛ با این‌که طناب‌هایشان بریده شده‌اند.',
 'یک پیام‌رسان زخمی، شیئی را به گروه می‌سپارد و پیش از توضیح دادن بیهوش می‌شود.',
 'کارفرما به‌جای پول، چیزی را پیشنهاد می‌کند که یکی از شخصیت‌ها مدت‌هاست دنبالش است.',
 'در میانهٔ جشن عمومی، همه برای چند ثانیه نام خود را فراموش می‌کنند؛ جز شخصیت‌های بازیکنان.',
 'فردی بی‌گناه به جرمی متهم شده که شواهدش غیرقابل‌انکار به نظر می‌رسند.',
 'نقشهٔ گروه مسیری تازه را نشان می‌دهد که شب گذشته وجود نداشته است.'
]
TWISTS = [
 'کارفرما همهٔ حقیقت را نگفته؛ می‌خواهد از نتیجه برای پاک کردن ردپای خودش استفاده کند.',
 'تهدید اصلی صرفاً شرور نیست؛ حملهٔ عجولانه ممکن است به بی‌گناهان آسیب بزند.',
 'یکی از سرنخ‌ها درست است، اما برداشت رایج از آن اشتباه است.',
 'رقیب گروه همان هدف را دنبال می‌کند، اما انگیزه‌اش متفاوت است.',
 'راه‌حل آسان پیامدی بلندمدت دارد که در پایان آشکار می‌شود.',
 'شخصیت مورد اعتماد بخشی از حقیقت را برای محافظت از فرد دیگری پنهان کرده است.'
]

def local_generate(cfg):
    random.seed()
    g = GENRES[cfg['genre']]
    place, threat, mood = random.choice(g['places']), random.choice(g['threats']), random.choice(g['moods'])
    hook, twist = random.choice(HOOKS), random.choice(TWISTS)
    theme = cfg['theme'].strip() or 'راز یک نیروی ناشناخته'
    level, players, duration = cfg['level'], cfg['players'], cfg['duration']
    scaling = ('برای سطح پایین، خطرها روشن و قابل‌فرار باشند.' if level <= 2 else
               'یک تهدید ویژه و چند انتخاب تاکتیکی معنادار اضافه کن.' if level <= 5 else
               'منابع محدود، خطرهای چندمرحله‌ای و دشمنانی با قابلیت‌های مکمل در نظر بگیر.' if level <= 10 else
               'برای قدرت بالای گروه، اهداف چندمرحله‌ای و راه‌حل‌های غیررزمی فراهم کن.')
    templates = [
      ('ورود و قلاب داستانی', f'{hook}\nگروه به {place} می‌رسد و درمی‌یابد که «{theme}» با اتفاقات اخیر مرتبط است.', 'از هر بازیکن بپرس چه چیزی توجه شخصیتش را جلب می‌کند.', 'گروه سرنخ نخست را پیدا می‌کند یا متحدی به دست می‌آورد.'),
      ('تحقیق و نخستین انتخاب', f'شاهدان دربارهٔ {threat} روایت‌های متناقضی دارند. یکی حقیقت را می‌گوید، اما بخشی را حذف کرده است.', 'گفت‌وگو، بررسی محیط یا خرج کردن منبع؛ دست‌کم دو مسیر پیشرفت فراهم کن.', 'سرنخ به محل بعدی اشاره می‌کند؛ شکست فقط هزینه ایجاد می‌کند و داستان را متوقف نمی‌کند.'),
      ('مانع و فشار', f'راه گروه با خطر محیطی یا نگهبانی روبه‌رو می‌شود که به «{theme}» پیوند دارد.', f'چالش متناسب با سطح {level}. {scaling}', 'گروه به حقیقت نزدیک می‌شود، اما تهدید متوجه یک فرد یا مکان مهم می‌شود.'),
      ('افشای میانی', f'{twist}\nاکنون گروه باید تصمیم بگیرد به کدام طرف اعتماد کند.', 'اطلاعات تازه را روشن ارائه کن تا تصمیم بازیکنان معنادار باشد.', 'انتخاب گروه، متحدان و منابع مرحلهٔ پایانی را تغییر می‌دهد.'),
      ('رویارویی نهایی', f'در قلب {place}، عامل بحران برای رسیدن به هدفش اقدام می‌کند. پیروزی فقط با شکست دادن دشمن تعریف نمی‌شود.', 'سه راه را آماده کن: نبرد، مذاکره یا خراب کردن منبع قدرت تهدید.', 'با توجه به تصمیم‌ها، تهدید متوقف می‌شود، تغییر شکل می‌دهد یا فرار می‌کند.'),
      ('پیامد و قلاب بعدی', 'مردم و متحدان به انتخاب گروه واکنش نشان می‌دهند؛ نشانه‌ای از ماجرای بزرگ‌تر باقی می‌ماند.', 'به هر شخصیت فرصت بده واکنش کوتاهی نشان دهد.', 'یک پاداش ملموس و یک پرسش باز برای ادامهٔ کمپین ارائه کن.')]
    count = 3 if duration <= 2 else 4 if duration <= 4 else 6
    scenes = [{'name':f'صحنهٔ {i}: {t[0]}','description':t[1],'dm_notes':t[2],'outcome':t[3]} for i,t in enumerate(templates[:count],1)]
    npc_names = random.sample(['مارا وین','اِلدریک فِن','سِرا نُوکس','تومِن خاکستری','ایلیا رِد','وِسک','بانوی آرن','کاپیتان دورن','نِری','فینچ'], 3)
    roles = ['کارفرما یا متحد اولیه','رقیب یا مظنون','شاهد یا راهنمای محلی']
    motivations = ['می‌خواهد بحران حل شود، اما از آشکار شدن سهم خودش می‌ترسد.','می‌خواهد کنترل نتیجه را در دست بگیرد، نه لزوماً همه را نابود کند.','می‌خواهد از شخص یا مکانی خاص محافظت کند.']
    secrets = ['مدرکی دارد که روایت رسمی را زیر سؤال می‌برد.','اطلاعاتی دارد که می‌تواند از فاجعه جلوگیری کند.','سرنخی دیده، اما از پیامد گفتنش می‌ترسد.']
    npcs = [{'name':npc_names[i],'role':roles[i],'look':['لباس سفر خاک‌آلود و نگاهی مراقب','ظاهر مرتب، با جزئیاتی ناسازگار با محیط','خسته، حواس‌جمع و آشنا با مسیرهای فرعی'][i], 'motivation':motivations[i], 'secret':secrets[i], 'voice':['آرام و دقیق؛ دربارهٔ گذشته مکث می‌کند.','با اعتمادبه‌نفس حرف می‌زند و به سؤال‌ها با سؤال جواب می‌دهد.','جمله‌های کوتاه؛ هنگام اضطراب جزئیات حاشیه‌ای می‌گوید.'][i]} for i in range(3)]
    return {
      'title':random.choice([f'راز {place}',f'سایه بر فراز {place}',f'آخرین چراغ {place}',f'آنچه زیر {place} بیدار شد']),
      'system':cfg['system'],'genre':cfg['genre'],'level':level,'players':players,'duration':duration,'tone':mood,'theme':theme,
      'premise':f'در {place} نشانه‌هایی از فعالیت {threat} دیده شده است. گروه برای کشف حقیقت وارد ماجرا می‌شود، اما مسئله به «{theme}» گره خورده و راه‌حل ساده احتمالاً پیامدی ناخواسته دارد.',
      'hook':hook,'dm_summary':f'ماجراجویی برای {players} بازیکن سطح {level} و حدود {duration} ساعت طراحی شده است. هستهٔ درام: {theme}. تهدید مرکزی: {threat}. حال‌وهوا: {mood}.',
      'scenes':scenes,'npcs':npcs,
      'clues':[
        {'clue':'ردیفی از آثار که با روایت شاهد اصلی جور درنمی‌آید','points_to':'زمان یا مسیر واقعی رخداد','if_missed':'شاهد دیگری همان نکته را از زاویه‌ای متفاوت بیان می‌کند.'},
        {'clue':'نماد یا شیئی که در دو مکان مختلف تکرار شده','points_to':'ارتباط میان عامل بحران و محل نهایی','if_missed':'رقیب گروه هنگام معامله ناخواسته به آن اشاره می‌کند.'},
        {'clue':'سند ناقص یا شهادت متناقض','points_to':'انگیزهٔ پنهان یکی از افراد مهم','if_missed':'فرصتی اجتماعی در صحنهٔ بعد حقیقت را آشکار می‌کند.'}],
      'encounters':[
        {'type':'اجتماعی','challenge':'مذاکره با شاهدی که از تلافی می‌ترسد','stakes':'اعتمادسازی، مسیر امن یا اطلاعات اضافه ایجاد می‌کند.'},
        {'type':'اکتشافی','challenge':'عبور از منطقه‌ای ناپایدار با نشانه‌های هشدار قابل کشف','stakes':'شتاب‌زدگی باعث مصرف منابع می‌شود، نه بن‌بست داستانی.'},
        {'type':'رزمی یا جایگزین','challenge':f'رویارویی با نگهبانان یا عاملان {threat}','stakes':'گروه می‌تواند بجنگد، فریب دهد، مخفیانه عبور کند یا هدف دشمن را مختل کند.'}],
      'twist':twist,
      'endings':[{'name':'پیروزی روشن','result':'گروه تهدید را متوقف می‌کند؛ یک مدرک به شبکه‌ای بزرگ‌تر اشاره دارد.'},{'name':'پیروزی پرهزینه','result':'بحران حل می‌شود، اما یک متحد اعتمادش را از دست می‌دهد یا بخشی از مکان آسیب می‌بیند.'},{'name':'توافق خاکستری','result':'خطر فوری کاهش می‌یابد، ولی بدهی یا تعهدی برای آینده شکل می‌گیرد.'}],
      'rewards':['پاداش مالی متناسب با سطح و اقتصاد کمپین','سرنخ یا نقشه‌ای برای ماجرای بعدی','لطف یک متحد محلی یا دسترسی به مکانی بسته'],
      'scaling':scaling,'safety_note':'پیش از بازی، مرزهای محتوایی گروه را بپرس و موضوعات حساس را در صورت نیاز تعدیل کن.',
      'extra_requirements':cfg['extra'],'created_at':datetime.now().strftime('%Y-%m-%d %H:%M'),'generation_mode':'موتور داخلی (الگومحور)'
    }

def ai_generate(cfg, api_key, model):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    prompt = f'''Design an original, playable D&D-compatible adventure in Persian. Do not reproduce published adventure text. Return ONLY valid JSON with keys: title, system, genre, level, players, duration, tone, theme, premise, hook, dm_summary, scenes (objects with name, description, dm_notes, outcome), npcs (name, role, look, motivation, secret, voice), clues (clue, points_to, if_missed), encounters (type, challenge, stakes), twist, endings (name, result), rewards, scaling, safety_note, created_at, generation_mode. Include 3+ distinct NPCs, 3+ clues with alternate paths (no single point of failure), 3+ encounters with noncombat alternatives, private DM information, actionable table notes, choice-driven endings, internal consistency, sensible difficulty for party level and size. Avoid generic filler and do not invent exact official stat blocks. Requirements: {json.dumps(cfg,ensure_ascii=False)}'''
    response = client.chat.completions.create(model=model, messages=[{'role':'system','content':'You are a meticulous tabletop adventure designer. Return valid JSON only.'},{'role':'user','content':prompt}], response_format={'type':'json_object'}, temperature=0.85)
    result = json.loads(response.choices[0].message.content)
    result['generation_mode'] = f'هوش مصنوعی ({model})'
    result.setdefault('created_at', datetime.now().strftime('%Y-%m-%d %H:%M'))
    return result

def to_markdown(a):
    lines=[f"# {a.get('title','ماجراجویی D&D')}", '', f"**سیستم:** {a.get('system','')} | **ژانر:** {a.get('genre','')} | **سطح:** {a.get('level','')} | **بازیکنان:** {a.get('players','')} | **مدت:** {a.get('duration','')} ساعت", '', '## خلاصه برای DM', a.get('dm_summary',''), '', '## ایدهٔ مرکزی', a.get('premise',''), '', '## شروع ماجرا', a.get('hook',''), '', '## صحنه‌ها']
    for s in a.get('scenes',[]): lines += [f"### {s.get('name','صحنه')}",s.get('description',''),'',f"**یادداشت DM:** {s.get('dm_notes','')}",'',f"**نتیجهٔ محتمل:** {s.get('outcome','')}",'']
    lines += ['## شخصیت‌های غیرقابل‌بازی (NPC)']
    for n in a.get('npcs',[]): lines += [f"### {n.get('name','NPC')} — {n.get('role','')}",f"- **ظاهر:** {n.get('look','')}",f"- **انگیزه:** {n.get('motivation','')}",f"- **راز (فقط DM):** {n.get('secret','')}",f"- **نحوهٔ صحبت:** {n.get('voice','')}",'']
    lines += ['## سرنخ‌ها']
    for c in a.get('clues',[]): lines += [f"- **سرنخ:** {c.get('clue','')}",f"  - مسیر: {c.get('points_to','')}",f"  - اگر از دست رفت: {c.get('if_missed','')}"]
    lines += ['', '## برخوردها و چالش‌ها']
    for e in a.get('encounters',[]): lines += [f"### {e.get('type','چالش')}",e.get('challenge',''),f"**اهمیت:** {e.get('stakes','')}",'']
    lines += ['## پیچش داستانی',a.get('twist',''),'','## پایان‌های ممکن']
    for e in a.get('endings',[]): lines.append(f"- **{e.get('name','پایان')}:** {e.get('result','')}" if isinstance(e,dict) else f'- {e}')
    lines += ['', '## پاداش‌ها'] + [f'- {r}' for r in a.get('rewards',[])] + ['', '## تنظیم سختی',a.get('scaling',''),'','## یادآوری ایمنی میز',a.get('safety_note',''),'']
    return '\n'.join(lines)

st.markdown('''<div style="padding:1.3rem 1.5rem;border-radius:18px;background:linear-gradient(120deg,#171b2e,#35234a);color:white"><h1 style="color:white;margin:0">🐉 D&D Adventure Forge</h1><p style="margin:.5rem 0 0;color:#e7e4f2">کارگاه ساخت ماجراجویی؛ از ایدهٔ خام تا راهنمای قابل‌اجرای Dungeon Master</p></div>''', unsafe_allow_html=True)
with st.sidebar:
    st.header('⚙️ موتور تولید')
    mode=st.radio('روش ساخت سناریو',['موتور داخلی (بدون هزینهٔ API)','هوش مصنوعی (کیفیت و تنوع بیشتر)'])
    api_key=''; model='gpt-4.1-mini'
    if mode.startswith('هوش مصنوعی'):
        api_key=st.text_input('کلید API',type='password',help='کلید را در فایل یا کد ذخیره نکن.')
        model=st.text_input('نام مدل',value='gpt-4.1-mini')
        st.caption('استفاده از API ممکن است هزینه داشته باشد.')
    st.divider(); st.caption('نسخهٔ قابل‌اجرا • ذخیرهٔ محلی روی همین رایانه')

st.subheader('۱) مشخصات ماجراجویی')
with st.form('adventure_form'):
    c1,c2,c3=st.columns(3)
    with c1:
        system=st.selectbox('نسخهٔ قوانین',['D&D 5e (2014)','D&D 5e (2024)','سازگار با D&D / قوانین سبک'])
        genre=st.selectbox('ژانر',list(GENRES.keys()))
    with c2:
        level=st.slider('سطح شخصیت‌ها',1,20,3); players=st.slider('تعداد بازیکنان',1,8,4)
    with c3:
        duration=st.select_slider('مدت جلسه (ساعت)',options=[1,2,3,4,5,6,8],value=3)
        complexity=st.selectbox('پیچیدگی داستان',['ساده و مستقیم','متعادل','چندلایه و پرپیچش'],index=1)
    theme=st.text_input('ایده یا عنصر دلخواه (اختیاری)',placeholder='مثلاً: شهری که مردمش خواب‌های یکسان می‌بینند')
    extra=st.text_area('خواسته‌های خاص (اختیاری)',placeholder='مثلاً: بدون نبرد اجباری، یک معمای منطقی، فضای گوتیک...',height=90)
    submitted=st.form_submit_button('✨ ساخت سناریو',type='primary',use_container_width=True)
if submitted:
    cfg={'system':system,'genre':genre,'level':level,'players':players,'duration':duration,'complexity':complexity,'theme':theme,'extra':extra}
    try:
        with st.spinner('در حال طراحی ماجراجویی و آماده‌سازی بخش‌های اجرایی...'):
            if mode.startswith('هوش مصنوعی'):
                if not api_key.strip(): st.error('برای موتور هوش مصنوعی، کلید API را وارد کن یا موتور داخلی را انتخاب کن.'); st.stop()
                adventure=ai_generate(cfg,api_key.strip(),model.strip() or 'gpt-4.1-mini')
            else: adventure=local_generate(cfg)
            st.session_state['adventure']=adventure
            st.session_state['adventure_md']=to_markdown(adventure)
    except Exception as exc:
        st.error(f'ساخت سناریو انجام نشد: {exc}')
        if mode.startswith('هوش مصنوعی'): st.info('کلید API، نام مدل، اتصال اینترنت و دسترسی حساب را بررسی کن.')

if 'adventure' in st.session_state:
    a=st.session_state['adventure']; st.divider(); st.markdown(f"# 📜 {a.get('title','ماجراجویی تازه')}"); st.caption(f"ساخته‌شده در {a.get('created_at','')} • روش تولید: {a.get('generation_mode','')}")
    m1,m2,m3,m4=st.columns(4); m1.metric('سطح',a.get('level','—')); m2.metric('تعداد بازیکنان',a.get('players','—')); m3.metric('مدت',f"{a.get('duration','—')} ساعت"); m4.metric('تعداد صحنه‌ها',len(a.get('scenes',[])))
    tabs=st.tabs(['نمای کلی','صحنه‌ها','NPCها','سرنخ‌ها','برخوردها','پایان‌ها','خروجی و ذخیره'])
    with tabs[0]:
        st.subheader('خلاصه برای Dungeon Master'); st.write(a.get('dm_summary','')); st.subheader('پیش‌فرض داستان'); st.write(a.get('premise','')); st.subheader('قلاب آغازین'); st.info(a.get('hook','')); st.subheader('پیچش اصلی'); st.write(a.get('twist','')); st.subheader('تنظیم سختی'); st.write(a.get('scaling',''))
        if a.get('extra_requirements'): st.subheader('خواسته‌های خاص'); st.write(a['extra_requirements'])
    with tabs[1]:
        for i,s in enumerate(a.get('scenes',[]),1):
            with st.expander(s.get('name',f'صحنه {i}'),expanded=(i==1)):
                st.write(s.get('description','')); st.markdown('**یادداشت DM**'); st.write(s.get('dm_notes','')); st.markdown('**نتیجهٔ محتمل**'); st.write(s.get('outcome',''))
    with tabs[2]:
        for n in a.get('npcs',[]):
            with st.expander(f"{n.get('name','NPC')} — {n.get('role','')}"):
                st.write(f"**ظاهر:** {n.get('look','')}"); st.write(f"**انگیزه:** {n.get('motivation','')}"); st.write(f"**راز (فقط DM):** {n.get('secret','')}"); st.write(f"**نحوهٔ صحبت:** {n.get('voice','')}")
    with tabs[3]:
        for i,c in enumerate(a.get('clues',[]),1):
            with st.expander(f"سرنخ {i}: {c.get('clue','')}"): st.write(f"**به چه چیزی می‌رسد:** {c.get('points_to','')}"); st.write(f"**اگر بازیکنان از دستش دادند:** {c.get('if_missed','')}")
    with tabs[4]:
        for e in a.get('encounters',[]):
            with st.expander(e.get('type','چالش')): st.write(e.get('challenge','')); st.write(f"**اهمیت:** {e.get('stakes','')}")
    with tabs[5]:
        for e in a.get('endings',[]):
            if isinstance(e,dict): st.markdown(f"**{e.get('name','پایان')}**"); st.write(e.get('result',''))
            else: st.write(e)
        st.subheader('پاداش‌ها')
        for r in a.get('rewards',[]): st.write(f'- {r}')
    with tabs[6]:
        md=st.session_state.get('adventure_md',to_markdown(a))
        st.download_button('⬇️ دریافت سناریو (Markdown)',md,file_name='dnd_adventure.md',mime='text/markdown',use_container_width=True)
        st.download_button('⬇️ دریافت دادهٔ سناریو (JSON)',json.dumps(a,ensure_ascii=False,indent=2),file_name='dnd_adventure.json',mime='application/json',use_container_width=True)
        if st.button('💾 ذخیره روی همین رایانه',use_container_width=True):
            safe=re.sub(r'[^A-Za-z0-9آ-ی_-]+','_',a.get('title','adventure')).strip('_')[:60] or 'adventure'
            filename=SAVE_DIR/f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}.json"
            filename.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8'); st.success(f'ذخیره شد: {filename.name}')
        st.caption('فایل‌های ذخیره‌شده در پوشهٔ saved_adventures کنار app.py قرار می‌گیرند.')
st.divider(); st.caption('موتور داخلی الگومحور است؛ برای روایت عمیق‌تر، موتور هوش مصنوعی را با API فعال کن. تعادل برخوردها را پیش از بازی با قوانین و وضعیت واقعی گروه بازبینی کن.')
