"""Minimal, persistent interface translations for ReaDroid (standard library only)."""
from __future__ import annotations
import json
import os
from pathlib import Path

LANGUAGES = {
    "pt": "Português",
    "en": "English",
    "ar": "العربية",
    "hi": "हिन्दी",
}
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "readroid"
CONFIG_FILE = CONFIG_DIR / "settings.json"

# Keys are Portuguese source strings; unknown strings safely remain in Portuguese.
TRANSLATIONS = {
"en": {
"IA opcional · Sem root · Offline por padrão":"Optional AI · No root · Offline by default", "opcional":"optional", "Cancelar":"Cancel",
"Inspecionar estrutura do APK":"Inspect APK structure", "Analisar manifesto e permissões":"Analyze manifest and permissions",
"Buscar URLs, domínios e IPs":"Find URLs, domains and IPs", "Decompilar para Java com JADX":"Decompile to Java with JADX",
"Extrair smali e recursos com Apktool":"Extract smali and resources with Apktool", "Verificar dependências":"Check dependencies",
"Abrir pasta de relatórios":"Open reports folder", "Abrir pasta de resultados":"Open output folder",
"Explorar e abrir arquivos gerados":"Browse and open generated files", "Edições rápidas e renomear pacote (pré-build)":"Quick edits and rename package (pre-build)",
"Reconstruir, alinhar e assinar APK":"Rebuild, align and sign APK", "Gerenciar chave de assinatura":"Manage signing key",
"Idioma / Language / اللغة / भाषा":"Language / Idioma / اللغة / भाषा", "Sair":"Exit", "Assistente IA":"AI assistant",
"Escolha o idioma:":"Choose language:", "Idioma salvo:":"Language saved:", "Opção não reconhecida.":"Unknown option.",
"Até a próxima. ReaDroid encerrado.":"See you next time. ReaDroid closed.", "ReaDroid > ":"ReaDroid > ",
"APKs encontrados nas pastas comuns:":"APKs found in common folders:", "Escolha um APK: ":"Choose an APK: ",
"[P] Informar outro caminho":"[P] Enter another path", "Caminho completo do APK: ":"Full APK path: ",
"Nenhum arquivo informado.":"No file provided.", "Arquivo não encontrado.":"File not found.",
"Seleção não reconhecida; informe o caminho manualmente.":"Selection not recognized; enter the path manually.",
"ENTER para voltar ao menu...":"Press ENTER to return to menu...", "VERIFICAÇÃO DE DEPENDÊNCIAS":"DEPENDENCY CHECK",
"não encontrado":"not found", "APK pronto:":"APK ready:", "Cópia em:":"Copy saved to:",
"A reconstrução não terminou. Veja os passos acima.":"Rebuild did not finish. See the steps above.",
"A assinatura não foi validada; não instale este APK.":"Signature verification failed; do not install this APK.",
},
"ar": {
"IA opcional · Sem root · Offline por padrão":"ذكاء اصطناعي اختياري · دون صلاحيات root · يعمل دون اتصال افتراضيًا", "opcional":"اختياري", "Cancelar":"إلغاء",
"Inspecionar estrutura do APK":"فحص بنية APK", "Analisar manifesto e permissões":"تحليل البيان والأذونات",
"Buscar URLs, domínios e IPs":"البحث عن الروابط والنطاقات وعناوين IP", "Decompilar para Java com JADX":"فك التحويل إلى Java باستخدام JADX",
"Extrair smali e recursos com Apktool":"استخراج smali والموارد باستخدام Apktool", "Verificar dependências":"فحص المتطلبات",
"Abrir pasta de relatórios":"فتح مجلد التقارير", "Abrir pasta de resultados":"فتح مجلد النتائج",
"Explorar e abrir arquivos gerados":"استعراض الملفات الناتجة وفتحها", "Edições rápidas e renomear pacote (pré-build)":"تعديلات سريعة وإعادة تسمية الحزمة",
"Reconstruir, alinhar e assinar APK":"إعادة بناء APK ومحاذاته وتوقيعه", "Gerenciar chave de assinatura":"إدارة مفتاح التوقيع",
"Idioma / Language / اللغة / भाषा":"اللغة / Language / Idioma / भाषा", "Sair":"خروج", "Assistente IA":"مساعد الذكاء الاصطناعي",
"Escolha o idioma:":"اختر اللغة:", "Idioma salvo:":"تم حفظ اللغة:", "Opção não reconhecida.":"خيار غير معروف.",
"Até a próxima. ReaDroid encerrado.":"إلى اللقاء. تم إغلاق ReaDroid.", "ReaDroid > ":"ReaDroid > ",
"APKs encontrados nas pastas comuns:":"ملفات APK الموجودة في المجلدات الشائعة:", "Escolha um APK: ":"اختر ملف APK: ",
"[P] Informar outro caminho":"[P] إدخال مسار آخر", "Caminho completo do APK: ":"المسار الكامل لملف APK: ",
"Nenhum arquivo informado.":"لم يتم إدخال ملف.", "Arquivo não encontrado.":"الملف غير موجود.",
"Seleção não reconhecida; informe o caminho manualmente.":"اختيار غير معروف؛ أدخل المسار يدويًا.",
"ENTER para voltar ao menu...":"اضغط ENTER للعودة إلى القائمة...", "VERIFICAÇÃO DE DEPENDÊNCIAS":"فحص المتطلبات",
"não encontrado":"غير موجود", "APK pronto:":"ملف APK جاهز:", "Cópia em:":"تم حفظ نسخة في:",
"A reconstrução não terminou. Veja os passos acima.":"لم تكتمل إعادة البناء. راجع الخطوات أعلاه.",
"A assinatura não foi validada; não instale este APK.":"فشل التحقق من التوقيع؛ لا تثبّت ملف APK هذا.",
},
"hi": {
"IA opcional · Sem root · Offline por padrão":"वैकल्पिक AI · root के बिना · डिफ़ॉल्ट रूप से ऑफ़लाइन", "opcional":"वैकल्पिक", "Cancelar":"रद्द करें",
"Inspecionar estrutura do APK":"APK संरचना जाँचें", "Analisar manifesto e permissões":"मैनिफेस्ट और अनुमतियाँ जाँचें",
"Buscar URLs, domínios e IPs":"URL, डोमेन और IP खोजें", "Decompilar para Java com JADX":"JADX से Java में डीकंपाइल करें",
"Extrair smali e recursos com Apktool":"Apktool से smali और संसाधन निकालें", "Verificar dependências":"निर्भरताएँ जाँचें",
"Abrir pasta de relatórios":"रिपोर्ट फ़ोल्डर खोलें", "Abrir pasta de resultados":"आउटपुट फ़ोल्डर खोलें",
"Explorar e abrir arquivos gerados":"बनाई गई फ़ाइलें देखें और खोलें", "Edições rápidas e renomear pacote (pré-build)":"त्वरित संपादन और पैकेज का नाम बदलें",
"Reconstruir, alinhar e assinar APK":"APK पुनर्निर्माण, संरेखण और हस्ताक्षर", "Gerenciar chave de assinatura":"हस्ताक्षर कुंजी प्रबंधित करें",
"Idioma / Language / اللغة / भाषा":"भाषा / Language / Idioma / اللغة", "Sair":"बाहर निकलें", "Assistente IA":"AI सहायक",
"Escolha o idioma:":"भाषा चुनें:", "Idioma salvo:":"भाषा सहेजी गई:", "Opção não reconhecida.":"अज्ञात विकल्प।",
"Até a próxima. ReaDroid encerrado.":"फिर मिलेंगे। ReaDroid बंद हो गया।", "ReaDroid > ":"ReaDroid > ",
"APKs encontrados nas pastas comuns:":"सामान्य फ़ोल्डरों में APK मिले:", "Escolha um APK: ":"APK चुनें: ",
"[P] Informar outro caminho":"[P] दूसरा पथ दर्ज करें", "Caminho completo do APK: ":"APK का पूरा पथ: ",
"Nenhum arquivo informado.":"कोई फ़ाइल नहीं दी गई।", "Arquivo não encontrado.":"फ़ाइल नहीं मिली।",
"Seleção não reconhecida; informe o caminho manualmente.":"चयन समझ नहीं आया; पथ स्वयं दर्ज करें।",
"ENTER para voltar ao menu...":"मेनू पर लौटने के लिए ENTER दबाएँ...", "VERIFICAÇÃO DE DEPENDÊNCIAS":"निर्भरता जाँच",
"não encontrado":"नहीं मिला", "APK pronto:":"APK तैयार:", "Cópia em:":"कॉपी यहाँ सहेजी गई:",
"A reconstrução não terminou. Veja os passos acima.":"पुनर्निर्माण पूरा नहीं हुआ। ऊपर दिए गए चरण देखें।",
"A assinatura não foi validada; não instale este APK.":"हस्ताक्षर सत्यापन विफल; इस APK को इंस्टॉल न करें।",
}}

TRANSLATIONS["en"].update({
    "A análise falhou:": "Analysis failed:", "O arquivo original não foi modificado.": "The original file was not modified.",
    "Inspeção APK": "APK inspection", "Manifesto": "Manifest", "Scanner strings": "String scanner",
    "Pastas decodificadas com Apktool:": "Decoded folders from Apktool:", "Escolha a pasta: ": "Choose a folder: ",
    "Pasta não encontrada.": "Folder not found.", "Chave de assinatura": "Signing key", "Verificação": "Verification",
    "Reconstrução (apktool b)": "Rebuild (apktool b)", "Alinhamento (zipalign)": "Alignment (zipalign)", "Assinatura": "Signature",
    "Edições": "Edits", "Nenhuma edição válida selecionada.": "No valid edits selected.",
    "Quando terminar de editar, use a opção 11 para reconstruir, alinhar e assinar.": "When editing is complete, use option 11 to rebuild, align and sign.",
    "Use só em APKs seus ou que você tem autorização para modificar.": "Only use this on APKs you own or are authorized to modify.",
    "A extração pode levar alguns minutos. O APK original não será alterado.": "Extraction may take a few minutes. The original APK will not be modified.",
    "Destino:": "Destination:", "Conteúdo:": "Contents:", "Pasta:": "Folder:",
    "Manifesto não decodificado. Veja a mensagem no relatório.": "Manifest not decoded. See the report message.",
})
TRANSLATIONS["ar"].update({
    "A análise falhou:": "فشل التحليل:", "O arquivo original não foi modificado.": "لم يتم تعديل الملف الأصلي.",
    "Inspeção APK": "فحص APK", "Manifesto": "البيان", "Scanner strings": "فاحص النصوص",
    "Pastas decodificadas com Apktool:": "المجلدات المفكوكة باستخدام Apktool:", "Escolha a pasta: ": "اختر مجلدًا: ",
    "Pasta não encontrada.": "المجلد غير موجود.", "Chave de assinatura": "مفتاح التوقيع", "Verificação": "التحقق",
    "Reconstrução (apktool b)": "إعادة البناء (apktool b)", "Alinhamento (zipalign)": "المحاذاة (zipalign)", "Assinatura": "التوقيع",
    "Edições": "التعديلات", "Nenhuma edição válida selecionada.": "لم يتم اختيار تعديلات صالحة.",
    "Quando terminar de editar, use a opção 11 para reconstruir, alinhar e assinar.": "بعد الانتهاء من التعديل، استخدم الخيار 11 لإعادة البناء والمحاذاة والتوقيع.",
    "Use só em APKs seus ou que você tem autorização para modificar.": "استخدم هذا فقط مع ملفات APK التي تملكها أو لديك إذن بتعديلها.",
    "A extração pode levar alguns minutos. O APK original não será alterado.": "قد يستغرق الاستخراج بضع دقائق. لن يتم تعديل ملف APK الأصلي.",
    "Destino:": "الوجهة:", "Conteúdo:": "المحتويات:", "Pasta:": "المجلد:",
    "Manifesto não decodificado. Veja a mensagem no relatório.": "تعذر فك البيان. راجع الرسالة في التقرير.",
})
TRANSLATIONS["hi"].update({
    "A análise falhou:": "विश्लेषण विफल:", "O arquivo original não foi modificado.": "मूल फ़ाइल में बदलाव नहीं किया गया।",
    "Inspeção APK": "APK निरीक्षण", "Manifesto": "मैनिफ़ेस्ट", "Scanner strings": "स्ट्रिंग स्कैनर",
    "Pastas decodificadas com Apktool:": "Apktool से डिकोड किए गए फ़ोल्डर:", "Escolha a pasta: ": "फ़ोल्डर चुनें: ",
    "Pasta não encontrada.": "फ़ोल्डर नहीं मिला।", "Chave de assinatura": "हस्ताक्षर कुंजी", "Verificação": "सत्यापन",
    "Reconstrução (apktool b)": "पुनर्निर्माण (apktool b)", "Alinhamento (zipalign)": "संरेखण (zipalign)", "Assinatura": "हस्ताक्षर",
    "Edições": "संपादन", "Nenhuma edição válida selecionada.": "कोई मान्य संपादन नहीं चुना गया।",
    "Quando terminar de editar, use a opção 11 para reconstruir, alinhar e assinar.": "संपादन के बाद पुनर्निर्माण, संरेखण और हस्ताक्षर के लिए विकल्प 11 चुनें।",
    "Use só em APKs seus ou que você tem autorização para modificar.": "केवल अपने या अनुमति प्राप्त APK पर उपयोग करें।",
    "A extração pode levar alguns minutos. O APK original não será alterado.": "निकालने में कुछ मिनट लग सकते हैं। मूल APK नहीं बदलेगा।",
    "Destino:": "गंतव्य:", "Conteúdo:": "सामग्री:", "Pasta:": "फ़ोल्डर:",
    "Manifesto não decodificado. Veja a mensagem no relatório.": "मैनिफ़ेस्ट डिकोड नहीं हुआ। रिपोर्ट में संदेश देखें।",
})


def load_language() -> str:
    try:
        lang = json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("language", "pt")
        return lang if lang in LANGUAGES else "pt"
    except (OSError, ValueError, TypeError):
        return "pt"

_language = load_language()

# compact menu labels v1
TRANSLATIONS["en"].update({"Inspec. APK":"APK scan","Decompilar":"Decompile","Extrair smali":"Smali","Dependencias":"Deps","Relatorios":"Reports","Resultados":"Results","Ver arquivos":"Files","Edicoes":"Edits","Assinar APK":"Sign APK","Chave APK":"APK key","Assistente IA":"AI","Idioma":"Lang","Sair":"Exit"})

TRANSLATIONS.setdefault("ar", {}).update({"Inspec. APK":"APK","Decompilar":"تفكيك","Extrair smali":"Smali","Dependencias":"تبعيات","Relatorios":"تقارير","Resultados":"نتائج","Ver arquivos":"ملفات","Edicoes":"تعديل","Assinar APK":"توقيع","Chave APK":"مفتاح","Assistente IA":"AI","Idioma":"لغة","Sair":"خروج"})
TRANSLATIONS.setdefault("hi", {}).update({"Inspec. APK":"APK","Decompilar":"डिकंपाइल","Extrair smali":"Smali","Dependencias":"Deps","Relatorios":"रिपोर्ट","Resultados":"परिणाम","Ver arquivos":"फ़ाइलें","Edicoes":"संपादन","Assinar APK":"साइन APK","Chave APK":"APK कुंजी","Assistente IA":"AI","Idioma":"भाषा","Sair":"बाहर"})

def get_language() -> str:
    return _language

def set_language(lang: str) -> None:
    global _language
    if lang not in LANGUAGES:
        raise ValueError("Idioma inválido")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temp = CONFIG_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps({"language": lang}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(CONFIG_FILE)
    _language = lang

def tr(text: str) -> str:
    table = TRANSLATIONS.get(_language, {})
    if text in table:
        return table[text]
    # Translate known phrases inside coloured/interpolated UI strings too.
    for source in sorted(table, key=len, reverse=True):
        if source and source in text:
            text = text.replace(source, table[source])
    return text
