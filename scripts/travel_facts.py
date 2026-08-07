"""
Shared general Sri Lanka travel facts for the Oracle Chat scenario (English
+ Sinhala). Unlike every other scenario, this content is not grounded in
places.json at all - the source dataset has no visa/currency/tipping/season
information, so this is a small hand-written fact pool, each entry carrying
both language versions together (single source of truth, unlike the
places-grounded scenarios where 02_/04_ duplicate logic because the digit-
prefixed filenames aren't importable from each other).

Each fact has a few question phrasings per language so the same fact
produces more than one training example without the answer text changing
(the answer is a stated fact, not something that should vary per phrasing).
"""

TRAVEL_FACTS = [
    {
        "topic": "visa",
        "en": {
            "questions": [
                "Do I need a visa to visit Sri Lanka?",
                "What's the visa process like for Sri Lanka?",
                "How do I get a visa for Sri Lanka?",
            ],
            "answer": (
                "Most visitors need an Electronic Travel Authorization (ETA) before arrival, which "
                "you can apply for online in advance. It's approved quickly for most nationalities "
                "and is valid for a short tourist stay, with the option to extend it later at the "
                "Department of Immigration if you decide to stay longer."
            ),
        },
        "si": {
            "questions": [
                "ශ්‍රී ලංකාවට යාමට වීසා බලපත්‍රයක් අවශ්‍යද?",
                "ශ්‍රී ලංකා වීසා ක්‍රියාවලිය කෙසේද?",
                "ශ්‍රී ලංකාවට වීසා බලපත්‍රයක් ලබාගන්නේ කෙසේද?",
            ],
            "answer": (
                "බොහෝ සංචාරකයින්ට පැමිණීමට පෙර ඉලෙක්ට්‍රොනික සංචාරක අවසර පත්‍රයක් (ETA) අවශ්‍ය වේ, "
                "එය අන්තර්ජාලය ඔස්සේ කලින් අයදුම් කළ හැක. බොහෝ රටවල පුරවැසියන් සඳහා එය ඉක්මනින් "
                "අනුමත වන අතර, කෙටි සංචාරක නවාතැන් කාලයක් සඳහා වලංගු වේ. වැඩි කලක් රැඳී සිටීමට "
                "අවශ්‍ය නම් පසුව ආගමන විගමන දෙපාර්තමේන්තුව හරහා එය දීර්ඝ කරගත හැක."
            ),
        },
    },
    {
        "topic": "currency",
        "en": {
            "questions": [
                "What currency is used in Sri Lanka?",
                "Can I pay in US dollars in Sri Lanka?",
                "Where can I exchange money in Sri Lanka?",
            ],
            "answer": (
                "The local currency is the Sri Lankan Rupee (LKR). Most shops and small vendors "
                "expect payment in rupees, though larger hotels sometimes accept US dollars. Banks "
                "and licensed money changers at the airport and in major towns offer fair exchange "
                "rates, and ATMs are widely available in cities for withdrawing rupees directly."
            ),
        },
        "si": {
            "questions": [
                "ශ්‍රී ලංකාවේ භාවිතා කරන මුදල් වර්ගය කුමක්ද?",
                "ශ්‍රී ලංකාවේ ඇමරිකානු ඩොලර් වලින් ගෙවීම් කළ හැකිද?",
                "ශ්‍රී ලංකාවේ මුදල් හුවමාරු කරගත හැක්කේ කොහෙන්ද?",
            ],
            "answer": (
                "ශ්‍රී ලංකාවේ භාවිතා වන්නේ ශ්‍රී ලංකා රුපියල (LKR) ය. බොහෝ වෙළඳසැල් හා කුඩා වෙළෙන්දන් "
                "රුපියල් වලින් ගෙවීම බලාපොරොත්තු වන අතර, විශාල හෝටල් සමහර විට ඇමරිකානු ඩොලර් ද පිළිගනී. "
                "ගුවන්තොටුපළේ සහ ප්‍රධාන නගරවල බැංකු හා බලපත්‍රලාභී මුදල් හුවමාරු ස්ථාන සාධාරණ "
                "විනිමය අනුපාත ලබා දෙන අතර, නගරවල ATM යන්ත්‍ර හරහාද රුපියල් ලබාගත හැක."
            ),
        },
    },
    {
        "topic": "transport",
        "en": {
            "questions": [
                "What's the best way to get around Sri Lanka?",
                "How do tourists usually travel between cities in Sri Lanka?",
                "Should I rent a car or hire a driver in Sri Lanka?",
            ],
            "answer": (
                "Tuk-tuks are convenient for short trips within a town, trains offer scenic (if slow) "
                "routes between major cities, and intercity buses are the cheapest option for longer "
                "distances. Many visitors hire a private driver for multi-day trips, which is more "
                "comfortable and flexible than self-driving, since local traffic and road conditions "
                "take some getting used to."
            ),
        },
        "si": {
            "questions": [
                "ශ්‍රී ලංකාවේ ගමන් කිරීමට වඩාත් සුදුසු ක්‍රමය කුමක්ද?",
                "සංචාරකයින් සාමාන්‍යයෙන් නගර අතර ගමන් කරන්නේ කෙසේද?",
                "මම කාර් රථයක් කුලියට ගත යුතුද නැතහොත් රියදුරෙකු කුලියට ගත යුතුද?",
            ],
            "answer": (
                "නගරයක් තුළ කෙටි ගමන් සඳහා ත්‍රී රෝද රථ පහසුය, දුම්රිය ප්‍රධාන නගර අතර මන්දගාමී වුවත් "
                "සුන්දර මාර්ග ලබා දෙයි, එසේම දුර ගමන් සඳහා අන්තර් නගර බස් රථ අඩුම වියදම් සහිත "
                "විකල්පයයි. බොහෝ සංචාරකයින් දින කිහිපයක සංචාර සඳහා පුද්ගලික රියදුරෙකු කුලියට ගනී, "
                "එය තමන්ම රිය පැදවීමට වඩා පහසු හා නම්‍යශීලීය, මන්ද දේශීය ගමනාගමන තදබදය හා "
                "පාරවල් තත්ත්වයන්ට හුරු වීමට යම් කාලයක් ගතවන බැවිනි."
            ),
        },
    },
    {
        "topic": "tipping",
        "en": {
            "questions": [
                "Is tipping expected in Sri Lanka?",
                "How much should I tip drivers and guides in Sri Lanka?",
            ],
            "answer": (
                "Tipping isn't mandatory but is appreciated and increasingly common, especially for "
                "drivers, guides, and hotel staff. A small amount for good service goes a long way; "
                "many restaurants already add a service charge to the bill, so check before tipping "
                "extra there."
            ),
        },
        "si": {
            "questions": [
                "ශ්‍රී ලංකාවේ ටිප් දීම අනිවාර්යද?",
                "රියදුරන්ට සහ මාර්ගෝපදේශකයින්ට කොපමණ ටිප් දිය යුතුද?",
            ],
            "answer": (
                "ටිප් දීම අනිවාර්ය නොවේ, නමුත් එය අගය කරනු ලබන අතර, විශේෂයෙන් රියදුරන්, "
                "මාර්ගෝපදේශකයින් සහ හෝටල් සේවකයින් සඳහා දිනෙන් දින සුලභ වෙමින් පවතී. හොඳ "
                "සේවාවක් සඳහා කුඩා මුදලක් ලබා දීම ප්‍රමාණවත්ය. බොහෝ අවන්හල් දැනටමත් බිල්පතට "
                "සේවා ගාස්තුවක් එකතු කරන බැවින්, අමතර ටිප් දීමට පෙර එය පරීක්ෂා කර බලන්න."
            ),
        },
    },
    {
        "topic": "best_season",
        "en": {
            "questions": [
                "When's the best time of year to visit Sri Lanka?",
                "Does Sri Lanka have a monsoon season I should plan around?",
            ],
            "answer": (
                "Sri Lanka has two monsoon seasons that hit different coasts at different times, so "
                "there's rarely a single bad time to visit the whole island - it depends which region "
                "you're headed to. Broadly, the west and south coasts and hill country are driest "
                "from December to March, while the east coast is driest from May to September."
            ),
        },
        "si": {
            "questions": [
                "ශ්‍රී ලංකාවට යාමට වඩාත් සුදුසු කාලය කුමක්ද?",
                "ශ්‍රී ලංකාවේ මෝසම් සමය සැලකිල්ලට ගත යුතුද?",
            ],
            "answer": (
                "ශ්‍රී ලංකාවේ විවිධ මුහුදුබඩ ප්‍රදේශවලට විවිධ කාලවලදී බලපාන මෝසම් සමයන් දෙකක් "
                "පවතින බැවින්, මුළු දිවයිනටම නරක කාලයක් යැයි කිව හැකි එක් කාල පරාසයක් "
                "කලාතුරකින් තිබේ - එය රඳා පවතින්නේ ඔබ යන ප්‍රදේශය මතය. සාමාන්‍යයෙන්, බටහිර "
                "හා දකුණු වෙරළබඩ ප්‍රදේශ සහ කඳුකරය දෙසැම්බර් සිට මාර්තු දක්වා වියළි වන අතර, "
                "නැගෙනහිර වෙරළබඩ ප්‍රදේශය මැයි සිට සැප්තැම්බර් දක්වා වියළි වේ."
            ),
        },
    },
    {
        "topic": "safety_norms",
        "en": {
            "questions": [
                "Is Sri Lanka generally safe for tourists?",
                "What general safety precautions should I take as a visitor to Sri Lanka?",
            ],
            "answer": (
                "Sri Lanka is generally considered safe for tourists, with petty theft being more of "
                "a concern than violent crime. Usual travel-sense precautions apply: keep valuables "
                "secure, use registered transport, dress modestly at religious sites, and check local "
                "conditions (weather, road closures) before heading to remote areas."
            ),
        },
        "si": {
            "questions": [
                "සංචාරකයින් සඳහා ශ්‍රී ලංකාව සාමාන්‍යයෙන් ආරක්ෂිතද?",
                "සංචාරකයෙකු ලෙස මා ගත යුතු පොදු ආරක්ෂක පියවර මොනවාද?",
            ],
            "answer": (
                "ශ්‍රී ලංකාව සංචාරකයින් සඳහා සාමාන්‍යයෙන් ආරක්ෂිත රටක් ලෙස සලකනු ලබන අතර, "
                "හිංසාකාරී අපරාධවලට වඩා කුඩා පොලිසි අපරාධ ගැන යම් සැලකිල්ලක් තිබිය යුතුය. "
                "සුපුරුදු සංචාරක ප්‍රවේශම් අදාළ වේ: වටිනා දේ ආරක්ෂිතව තබාගන්න, ලියාපදිංචි "
                "ගමනාගමන සේවා භාවිතා කරන්න, ආගමික ස්ථානවලදී යහපත් ලෙස ඇඳුම් ඇඳගන්න, "
                "සහ දුරස්ථ ප්‍රදේශවලට යාමට පෙර දේශීය තත්ත්වයන් (කාලගුණය, මාර්ග වසා දැමීම්) "
                "පරීක්ෂා කරන්න."
            ),
        },
    },
    {
        "topic": "language",
        "en": {
            "questions": [
                "What languages are spoken in Sri Lanka?",
                "Will I be able to get by with English in Sri Lanka?",
            ],
            "answer": (
                "Sinhala and Tamil are the official languages, but English is widely spoken in "
                "tourist areas, hotels, and by most guides and drivers, so getting by with English "
                "alone is generally not a problem, especially in cities and popular destinations."
            ),
        },
        "si": {
            "questions": [
                "ශ්‍රී ලංකාවේ කතා කරන භාෂා මොනවාද?",
                "ඉංග්‍රීසි භාෂාවෙන් පමණක් ශ්‍රී ලංකාවේ කටයුතු කරගත හැකිද?",
            ],
            "answer": (
                "සිංහල සහ දෙමළ රාජ්‍ය භාෂා වන අතර, සංචාරක ප්‍රදේශවල, හෝටලවල, සහ බොහෝ "
                "මාර්ගෝපදේශකයින් හා රියදුරන් අතර ඉංග්‍රීසි භාෂාව බහුලව භාවිතා වේ. එබැවින් "
                "විශේෂයෙන් නගරවල හා ජනප්‍රිය ගමනාන්තවල ඉංග්‍රීසි භාෂාව පමණක් භාවිතයෙන් "
                "කටයුතු කරගැනීම සාමාන්‍යයෙන් ගැටලුවක් නොවේ."
            ),
        },
    },
    {
        "topic": "electricity_connectivity",
        "en": {
            "questions": [
                "What plug type and voltage does Sri Lanka use?",
                "Can I get a local SIM card easily in Sri Lanka?",
            ],
            "answer": (
                "Sri Lanka runs on 230V with mostly type D and type G sockets, so many travelers "
                "need an adapter. Local SIM cards are cheap and easy to get at the airport or in "
                "towns with just a passport, and coverage for calls and mobile data is generally "
                "good across the island, including most tourist areas."
            ),
        },
        "si": {
            "questions": [
                "ශ්‍රී ලංකාවේ භාවිතා වන විදුලි පේනු වර්ගය සහ වෝල්ටීයතාවය කුමක්ද?",
                "ශ්‍රී ලංකාවේ දේශීය SIM කාඩ්පතක් පහසුවෙන් ලබාගත හැකිද?",
            ],
            "answer": (
                "ශ්‍රී ලංකාව 230V විදුලි බලයෙන් ක්‍රියාත්මක වන අතර, බහුලව භාවිතා වන්නේ D සහ G "
                "වර්ගයේ සොකට්ටු බැවින් බොහෝ සංචාරකයින්ට adapter එකක් අවශ්‍ය වේ. දේශීය SIM "
                "කාඩ්පත් ගුවන්තොටුපළේ හෝ නගරවල ගමන් බලපත්‍රය පමණක් සමඟ ලාභදායීව හා "
                "පහසුවෙන් ලබාගත හැක. දුරකථන ඇමතුම් හා ජංගම දත්ත ආවරණය දිවයින පුරාම, "
                "බොහෝ සංචාරක ප්‍රදේශ ඇතුළුව, සාමාන්‍යයෙන් හොඳින් පවතී."
            ),
        },
    },
]
