import json
from datetime import datetime
from pathlib import Path
import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

BASE = Path(__file__).parent
SAVE = BASE / "saved_characters"
SAVE.mkdir(exist_ok=True)
st.set_page_config(page_title="Character Forge", page_icon="🧙", layout="wide")

ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
FA = {"STR": "قدرت", "DEX": "چابکی", "CON": "استقامت", "INT": "هوش", "WIS": "خرد", "CHA": "کاریزما"}
RACES = {
    "انسان": ({"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1}, 30),
    "الف": ({"DEX": 2}, 30), "نیم‌الف": ({"CHA": 2, "STR": 1, "DEX": 1}, 30),
    "کوتوله": ({"CON": 2}, 25), "هف‌لینگ": ({"DEX": 2}, 25),
    "نیم‌اورک": ({"STR": 2, "CON": 1}, 30), "گنوم": ({"INT": 2}, 25),
    "تیفلینگ": ({"CHA": 2, "INT": 1}, 30), "دراگون‌زاده": ({"STR": 2, "CHA": 1}, 30),
}
CLASSES = {
    "بربر": (12, ["STR", "CON"]), "بارد": (8, ["DEX", "CHA"]),
    "کلریک": (8, ["WIS", "CHA"]), "دروید": (8, ["INT", "WIS"]),
    "فایتر": (10, ["STR", "CON"]), "مانک": (8, ["STR", "DEX"]),
    "پالدین": (10, ["WIS", "CHA"]), "رنجر": (10, ["STR", "DEX"]),
    "روگ": (8, ["DEX", "INT"]), "سورسرر": (6, ["CON", "CHA"]),
    "وارلاک": (8, ["WIS", "CHA"]), "ویزارد": (6, ["INT", "WIS"]),
}
BACKGROUNDS = ["آکولایت", "جنایتکار", "قهرمان مردمی", "اشراف‌زاده", "حکیم", "سرباز", "هنرمند", "ولگرد", "صنعتگر صنفی", "دریانورد"]
ALIGNMENTS = ["قانون‌مدار نیک", "خنثی نیک", "آشوب‌گر نیک", "قانون‌مدار خنثی", "خنثی", "آشوب‌گر خنثی", "قانون‌مدار شرور", "خنثی شرور", "آشوب‌گر شرور"]
SKILLS = {
    "Acrobatics": ("آکروباتیک", "DEX"), "Animal Handling": ("رام‌کردن حیوان", "WIS"),
    "Arcana": ("دانش جادو", "INT"), "Athletics": ("ورزش", "STR"), "Deception": ("فریب", "CHA"),
    "History": ("تاریخ", "INT"), "Insight": ("بینش", "WIS"), "Intimidation": ("ارعاب", "CHA"),
    "Investigation": ("تحقیق", "INT"), "Medicine": ("پزشکی", "WIS"), "Nature": ("طبیعت", "INT"),
    "Perception": ("ادراک", "WIS"), "Performance": ("اجرا", "CHA"), "Persuasion": ("متقاعدسازی", "CHA"),
    "Religion": ("مذهب", "INT"), "Sleight of Hand": ("تردستی", "DEX"), "Stealth": ("مخفی‌کاری", "DEX"),
    "Survival": ("بقا", "WIS"),
}
COST = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
ARMOR = {"بدون زره": (10, None), "زره چرمی": (11, None), "زره چرمی میخ‌دار": (12, None),
         "زره پوستین": (12, 2), "زره زنجیری سبک": (13, 2), "زره پولکی": (14, 2),
         "زره سینه‌ای": (14, 2), "زره نیم‌صفحه": (15, 2), "زره زنجیری": (16, 0), "زره صفحه‌ای": (18, 0)}

def mod(score):
    return (int(score) - 10) // 2

def signed(n):
    return f"+{n}" if n >= 0 else str(n)

def local_story(d):
    name = d["name"] or "ماجراجو"
    trait = d["personality"] or "در لحظه‌های سخت به غریزه‌اش تکیه می‌کند."
    goal = d["goal"] or "می‌خواهد حقیقتی را کشف کند که زندگی‌اش را تغییر داده است."
    secret = d["secret"] or "گذشته‌ای دارد که هنوز جرئت تعریف کردنش را پیدا نکرده است."
    return {
        "backstory": f"{name}، {d['race']} و {d['class']}، از دل تجربه‌های {d['background']} برخاسته است. {trait} {goal}",
        "personality_trait": trait, "ideal": f"باور دارد که {goal}",
        "bond": "به کسی که روزی جانش را نجات داده وفادار است.",
        "flaw": "گاهی آن‌قدر به تصمیم خودش مطمئن می‌شود که هشدار دیگران را نادیده می‌گیرد.",
        "secret": secret, "story_hook": f"ردی از گذشتهٔ {name} در شهری دور پیدا شده؛ کسی آنجا نام او را می‌داند، اما دلیلش روشن نیست."
    }

def ai_story(d, key, model):
    if OpenAI is None:
        raise RuntimeError("کتابخانهٔ openai نصب نیست؛ دستور نصب: python -m pip install openai")
    client = OpenAI(api_key=key)
    prompt = ("برای این کاراکتر D&D 5e نسخه ۲۰۱۴ به فارسی داستانی مشخص و قابل‌بازی بساز. "
              "آمار را تغییر نده. فقط JSON معتبر با کلیدهای backstory, personality_trait, ideal, bond, flaw, secret, story_hook بده. "
              "از شخصیت‌های شناخته‌شده کپی نکن.\n" + json.dumps(d, ensure_ascii=False))
    r = client.chat.completions.create(model=model, messages=[
        {"role": "system", "content": "You write original tabletop RPG character stories. Return valid JSON only."},
        {"role": "user", "content": prompt}], response_format={"type": "json_object"}, temperature=0.85)
    story = json.loads(r.choices[0].message.content)
    for k in ["backstory", "personality_trait", "ideal", "bond", "flaw", "secret", "story_hook"]:
        story.setdefault(k, "")
    return story

def markdown(c):
    lines = [f"# {c['name'] or 'کاراکتر تازه'}",
        f"**نژاد:** {c['race']} | **کلاس:** {c['class']} | **سطح:** {c['level']} | **پیشینه:** {c['background']}",
        "", "## ویژگی‌ها"]
    for a in ABILITIES:
        lines.append(f"- {FA[a]}: {c['scores'][a]} ({signed(mod(c['scores'][a]))})")
    lines += ["", "## مقادیر پایه", f"- HP: {c['hp']}", f"- AC: {c['ac']}",
              f"- بونوس تسلط: {signed(c['proficiency'])}", f"- سرعت: {c['speed']} فوت",
              "", "## داستان", c["story"]["backstory"]]
    for k, label in [("personality_trait", "ویژگی شخصیتی"), ("ideal", "آرمان"), ("bond", "پیوند"),
                     ("flaw", "عیب"), ("secret", "راز"), ("story_hook", "قلاب داستانی")]:
        lines += ["", f"## {label}", c["story"].get(k, "")]
    lines += ["", "## مهارت‌های انتخاب‌شده"]
    for s in c["skills"]:
        a = SKILLS[s][1]
        lines.append(f"- {SKILLS[s][0]}: {signed(mod(c['scores'][a]) + c['proficiency'])}")
    lines += ["", "## پرتاب‌های نجات"]
    for a in ABILITIES:
        bonus = mod(c["scores"][a]) + (c["proficiency"] if a in CLASSES[c["class"]][1] else 0)
        lines.append(f"- {FA[a]}: {signed(bonus)}")
    return "\n".join(lines)

st.markdown("""<div style="padding:1.2rem 1.4rem;border-radius:16px;background:linear-gradient(120deg,#171b2e,#35234a);color:white">
<h1 style="color:white;margin:0">🧙 Character Forge</h1><p style="margin:.5rem 0 0;color:#e7e4f2">کاراکترساز D&D 5e (2014) — محاسبات پایه + داستان‌پردازی</p></div>""", unsafe_allow_html=True)
with st.sidebar:
    st.header("⚙️ موتور داستان")
    mode = st.radio("روش داستان‌پردازی", ["داستان داخلی (بدون API)", "هوش مصنوعی (OpenAI API)"])
    key = st.text_input("کلید API", type="password") if mode.startswith("هوش مصنوعی") else ""
    model = st.text_input("نام مدل", value="gpt-4.1-mini") if mode.startswith("هوش مصنوعی") else "gpt-4.1-mini"
    if mode.startswith("هوش مصنوعی"):
        st.caption("استفاده از API ممکن است هزینه داشته باشد و به اعتبار API نیاز دارد.")

with st.form("character_form"):
    st.subheader("۱) هویت")
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("نام کاراکتر", placeholder="مثلاً: آریا خاکستر")
        race = st.selectbox("نژاد", list(RACES))
    with c2:
        cls = st.selectbox("کلاس", list(CLASSES))
        level = st.slider("سطح", 1, 20, 1)
    with c3:
        background = st.selectbox("پیشینه", BACKGROUNDS)
        alignment = st.selectbox("گرایش اخلاقی", ALIGNMENTS, index=4)
    st.subheader("۲) ویژگی‌ها — Point Buy")
    st.caption("ویژگی‌های پایه را بین ۸ تا ۱۵ انتخاب کن. مجموع هزینه نباید از ۲۷ بیشتر شود؛ پاداش نژادی بعداً اعمال می‌شود.")
    defaults = {"STR": 15, "DEX": 14, "CON": 13, "INT": 10, "WIS": 10, "CHA": 8}
    cols = st.columns(3)
    base = {}
    for i, a in enumerate(ABILITIES):
        with cols[i % 3]:
            base[a] = st.select_slider(f"{FA[a]} ({a})", options=list(range(8, 16)), value=defaults[a], key=f"score_{a}")
    st.subheader("۳) داستان و مهارت‌ها")
    personality = st.text_area("ویژگی یا رفتار شاخص", placeholder="مثلاً: به غریبه‌ها اعتماد نمی‌کند اما به قولش پایبند است.")
    goal = st.text_input("هدف اصلی", placeholder="مثلاً: پیدا کردن برادر ناپدیدشده")
    secret = st.text_input("راز پنهان (اختیاری)")
    skills = st.multiselect("مهارت‌های دارای تسلط (انتخاب دستی در نسخهٔ اولیه)",
        list(SKILLS), format_func=lambda s: f"{SKILLS[s][0]} ({s})", max_selections=4)
    armor = st.selectbox("زره برای محاسبهٔ AC", list(ARMOR))
    shield = st.checkbox("سپر (+2 AC؛ بررسی سازگاری با کلاس بر عهدهٔ بازیکن است)")
    submit = st.form_submit_button("✨ ساخت کاراکتر", type="primary", use_container_width=True)

if submit:
    points = sum(COST.get(v, 99) for v in base.values())
    if points > 27:
        st.error(f"هزینهٔ Point Buy شما {points} است؛ سقف مجاز ۲۷ است. چند ویژگی را پایین بیاور.")
        st.stop()
    scores = {a: base[a] + RACES[race][0].get(a, 0) for a in ABILITIES}
    proficiency = 2 + (level - 1) // 4
    hit_die = CLASSES[cls][0]
    con = mod(scores["CON"])
    hp = max(1, hit_die + con + (level - 1) * max(1, hit_die // 2 + 1 + con))
    armor_base, dex_cap = ARMOR[armor]
    dex = mod(scores["DEX"])
    dex_bonus = dex if dex_cap is None else min(dex, dex_cap)
    ac = armor_base + dex_bonus + (2 if shield else 0)
    d = {"name": name.strip(), "race": race, "class": cls, "level": level, "background": background,
         "alignment": alignment, "personality": personality.strip(), "goal": goal.strip(), "secret": secret.strip(),
         "base_scores": base, "scores": scores, "skills": skills, "armor": armor, "shield": shield,
         "hp": hp, "ac": ac, "proficiency": proficiency, "speed": RACES[race][1], "hit_die": hit_die,
         "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    with st.spinner("در حال ساخت داستان کاراکتر..."):
        story_source = "داستان داخلی"
        if mode.startswith("هوش مصنوعی") and key.strip():
            try:
                story = ai_story(d, key.strip(), model.strip() or "gpt-4.1-mini")
                story_source = f"هوش مصنوعی ({model.strip() or 'gpt-4.1-mini'})"
            except Exception as e:
                st.warning(f"API در دسترس نبود؛ داستان داخلی جایگزین شد. جزئیات: {e}")
                story = local_story(d)
                story_source = "داستان داخلی (جایگزین پس از خطا)"
        else:
            story = local_story(d)
            if mode.startswith("هوش مصنوعی"):
                st.info("کلید وارد نشده؛ داستان داخلی استفاده شد.")
        character = {**d, "story": story, "story_source": story_source}
        st.session_state["character"] = character
        st.session_state["character_md"] = markdown(character)

if "character" in st.session_state:
    c = st.session_state["character"]
    st.divider()
    st.title(f"📜 {c['name'] or 'کاراکتر تازه'}")
    st.caption(f"{c['race']} • {c['class']} • سطح {c['level']} • {c['background']} • منبع داستان: {c['story_source']}")
    a, b, cc, d = st.columns(4)
    a.metric("نقاط سلامتی (HP)", c["hp"]); b.metric("زره (AC)", c["ac"])
    cc.metric("بونوس تسلط", signed(c["proficiency"])); d.metric("سرعت", f"{c['speed']} ft")
    tabs = st.tabs(["ویژگی‌ها", "داستان", "مهارت‌ها و نجات", "خروجی و ذخیره"])
    with tabs[0]:
        cols = st.columns(3)
        for i, ab in enumerate(ABILITIES):
            cols[i % 3].metric(FA[ab], c["scores"][ab], f"اصلاح‌کننده {signed(mod(c['scores'][ab]))}")
        st.write(f"**تاس سلامتی کلاس:** d{c['hit_die']} | **زره:** {c['armor']} {'+ سپر' if c['shield'] else ''}")
        st.info("نسخهٔ اولیه است؛ زیرکلاس‌ها، ویژگی‌های نژادی و کلاسی، جادوها، تجهیزات کامل و همهٔ استثناهای قوانین هنوز پیاده‌سازی نشده‌اند.")
    with tabs[1]:
        for k, label in [("backstory", "پیشینه"), ("personality_trait", "ویژگی شخصیتی"), ("ideal", "آرمان"),
                         ("bond", "پیوند"), ("flaw", "عیب"), ("secret", "راز"), ("story_hook", "قلاب داستانی")]:
            st.subheader(label); st.write(c["story"].get(k, ""))
    with tabs[2]:
        st.subheader("مهارت‌ها")
        for s in c["skills"]:
            st.write(f"- {SKILLS[s][0]}: {signed(mod(c['scores'][SKILLS[s][1]]) + c['proficiency'])}")
        st.subheader("پرتاب‌های نجات")
        for ab in ABILITIES:
            bonus = mod(c["scores"][ab]) + (c["proficiency"] if ab in CLASSES[c["class"]][1] else 0)
            st.write(f"- {FA[ab]}: {signed(bonus)}")
    with tabs[3]:
        md = st.session_state["character_md"]
        st.download_button("⬇️ دریافت برگه (Markdown)", md, file_name="character_sheet.md", mime="text/markdown", use_container_width=True)
        st.download_button("⬇️ دریافت داده (JSON)", json.dumps(c, ensure_ascii=False, indent=2), file_name="character.json", mime="application/json", use_container_width=True)
        if st.button("💾 ذخیره روی همین رایانه", use_container_width=True):
            safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (c["name"] or "character"))[:50].strip("_") or "character"
            path = SAVE / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}.json"
            path.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
            st.success(f"ذخیره شد: {path.name}")
        st.caption("فایل‌ها در پوشهٔ saved_characters کنار character_forge.py ذخیره می‌شوند.")
st.divider()
st.caption("Character Forge — نسخهٔ اولیه؛ قبل از استفاده در بازی، قوانین و تجهیزات را با کتاب مرجع گروه تطبیق دهید.")
