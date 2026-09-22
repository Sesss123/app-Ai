# TripMe Sinhala Travel AI — Version 1 Product Scope

## 1. Product vision

TripMe යනු ශ්‍රී ලංකාවේ සංචාරය සැලසුම් කරන පුද්ගලයන්ට Sinhala, Singlish සහ English
භාවිතයෙන් සංචාරක ස්ථාන සොයාගැනීමට සහ itinerary එකක් සකස් කරගැනීමට උපකාර කරන AI
assistant එකකි.

Version 1 හි ප්‍රධාන වටිනාකම වන්නේ සියලු දේ දන්නා සාමාන්‍ය chatbot එකක් වීම නොව,
ශ්‍රී ලංකා travel domain එකට සීමා වූ, තමන් නොදන්නා දේ පිළිගන්නා, verified information මත
පිළිතුරු දෙන assistant එකක් වීමයි.

## 2. Target users

### Primary users

- ශ්‍රී ලංකාව තුළ සංචාරය කරන දේශීය Sinhala-speaking travelers.
- Sinhala සහ English මිශ්‍ර කර ලියන mobile users.
- පවුලේ, යහළුවන්ගේ හෝ තනි ගමනක් සැලසුම් කරන පුද්ගලයන්.

### Secondary users

- ශ්‍රී ලංකාවට පැමිණෙන English-speaking tourists.
- ශ්‍රී ලංකා සංචාරක ස්ථාන පිළිබඳ මූලික තොරතුරු සොයන students/users.

Version 1 සඳහා Tamil conversation support එක පොරොන්දු නොවේ.

## 3. Supported languages

- Sinhala Unicode — primary language.
- Singlish — common Latin-letter Sinhala prompts තේරුම් ගැනීම.
- Sinhala-English code switching.
- English — secondary language.

Assistant එක හැකි විට user භාවිත කළ භාෂාවෙන් පිළිතුරු දිය යුතුය. User පැහැදිලිව වෙනත්
භාෂාවක් ඉල්ලුවහොත් එයට මාරු විය හැක.

## 4. Version 1 core capabilities

### 4.1 Place discovery

Assistant එකට පහත constraints අනුව places යෝජනා කළ හැක:

- District හෝ area
- Place category
- User interests/activities
- Family-friendly අවශ්‍යතා
- Accessibility information තිබේ නම් එය
- Free/paid යන verified information
- Visit කිරීමට අවශ්‍ය දින ගණන

### 4.2 Place explanation

Verified dataset එකේ ඇති දේ භාවිතයෙන්:

- Place එක කුමක්ද කියා පැහැදිලි කිරීම.
- එහි කළ හැකි activities සඳහන් කිරීම.
- District/category/location details ලබාදීම.
- Data නොමැති field එකක් නොදන්නා බව පැවසීම.

### 4.3 Itinerary generation

- Half-day plan
- One-day plan
- Two-to-three-day basic plan
- Places කිහිපයක් logical order එකකට සංවිධානය කිරීම
- User constraints සහ interests summary කිරීම

Exact travel time සහ route order verified routing service එකක් නොමැති විට estimate නොකළ යුතුය.

### 4.4 Comparison

Dataset එකේ තිබෙන places දෙකක් හෝ කිහිපයක් පහත dimensions අනුව compare කළ හැක:

- Category සහ activities
- Family suitability
- Available facilities
- Accessibility information
- Verified cost information
- District/location

Missing information එක “නොදනී” ලෙස පෙන්විය යුතුය; හොඳ යැයි පෙනෙන answer එකක් සඳහා
facts නිර්මාණය නොකළ යුතුය.

### 4.5 Follow-up questions

Recommendation එකකට ප්‍රමාණවත් context නැත්නම් කෙටි follow-up question එකක් අසන්න:

- යාමට කැමති district/area එක කුමක්ද?
- දින කීයක් තිබේද?
- Budget range එක කුමක්ද?
- Family, children හෝ accessibility needs තිබේද?
- කැමති activities මොනවාද?

එකවර අත්‍යවශ්‍ය ප්‍රශ්න පමණක් අසන්න.

## 5. Information architecture

### Model/adapter එක ඉගෙනගත යුතු දේ

- Sinhala/Singlish conversation style
- User intent සහ constraints හඳුනාගැනීම
- Useful answer structure
- Follow-up questions ඇසීම
- Missing facts ගැන uncertainty දැක්වීම
- Retrieved context එකට සීමා වී පිළිතුරු දීම

### RAG/database එකෙන් ලබාදිය යුතු දේ

- Place facts සහ descriptions
- Coordinates සහ district/category
- Facilities සහ activities
- Source URL සහ verification date
- Opening hours සහ ticket prices
- Weather, closures, alerts සහ current safety information

Places, prices සහ current facts model weights තුළ විශ්වාසදායක knowledge source එකක් ලෙස
memorize කිරීම Version 1 architecture එකේ අරමුණ නොවේ.

## 6. Out of scope for Version 1

- Hotel, flight, train හෝ bus tickets book කිරීම.
- Payment processing.
- Live navigation හෝ turn-by-turn directions.
- Real-time weather service එකක් නොමැතිව current weather කියීම.
- Verified source එකක් නොමැතිව current opening status/price/safety කියීම.
- Emergency response service එකක් ලෙස ක්‍රියා කිරීම.
- Medical, legal, financial හෝ relationship advice.
- User location එක background එකේ track කිරීම.
- Tamil-first assistant support.
- Voice input/output සහ image recognition.
- ලෝකයේ අනෙක් රටවල් සඳහා travel planning.

මෙම features පසුව වෙනම versions ලෙස සැලසුම් කළ හැක.

## 7. Safety and refusal rules

Assistant එක:

- “මෙම ස්ථානය දැන් ආරක්ෂිතයි” කියා current evidence නැතිව සහතික නොකළ යුතුය.
- Road, flood, landslide, wildlife හෝ sea conditions ගැන static data මත current claim නොකළ යුතුය.
- Emergency එකකදී local emergency services/authorities අමතන ලෙස පැහැදිලිව කියන්න.
- Dangerous, illegal හෝ protected-area rules උල්ලංඝනය කරන ක්‍රියාකාරකම් උපදෙස් නොදිය යුතුය.
- Religious සහ cultural places ගැන ගෞරවනීය, neutral language භාවිත කළ යුතුය.
- User ලබා නොදුන් sensitive personal details ඉල්ලා නොසිටිය යුතුය.
- Children හෝ accessibility needs තිබේ නම් missing safety/access information පැහැදිලිව සඳහන් කළ යුතුය.

## 8. Response policy

සාමාන්‍ය response එකක:

1. Userගේ අවශ්‍යතාව කෙටියෙන් පිළිගන්න.
2. හොඳම relevant recommendations කිහිපයක් දෙන්න.
3. සෑම recommendation එකකටම “ඇයි ගැළපෙන්නේ” කියන්න.
4. වැදගත් missing/current information තිබේ නම් warning එකක් දෙන්න.
5. අවශ්‍ය නම් එක් useful follow-up question එකක් අසන්න.

Assistant එක දිගු marketing-style descriptions වලට වඩා clear, actionable answers ලබාදිය යුතුය.

## 9. Example supported requests

- “මහනුවර family එකත් එක්ක දවසකින් බලන්න පුළුවන් තැන් මොනවාද?”
- “Galle wala free places tikak kiyanna.”
- “Wheelchair access ගැන data තියෙන Colombo places දෙකක් compare කරන්න.”
- “Ella අවට nature සහ photography වලට itinerary එකක් හදන්න.”
- “මේ place එකේ ticket price එක දන්නවාද?”

## 10. Example unsupported or restricted requests

- “හෙට උදේ මේ පාර අනිවාර්යයෙන් safe ද?”
- “දැන් entrance ticket එක හරියටම කීයද?” — current source නැත්නම් answer නොකළ යුතුය.
- “මට hotel එක book කර payment කරන්න.”
- “Doctor කෙනෙක් නැතුව මේ අසනීපයට medicine එකක් කියන්න.”
- “Restricted area එකට guards මගහැරලා යන්නේ කොහොමද?”

## 11. Version 1 success metrics

### Quality

- Sinhala naturalness average: අවම `4/5`
- Factual correctness average: අවම `4/5`
- Constraint satisfaction average: අවම `4/5`
- Base model සමඟ pairwise win rate: `>60%`

### Safety and grounding

- Unsupported current/safety claims: `<1%`
- Gold test set තුළ train/test place leakage: `0`
- Retrieved data වලට පටහැනි answers: `<2%`

### Product behavior

- User language matching: `>90%`
- Required context නැති requests වල useful clarification rate: `>90%`
- Normal response latency target: deployment hardware තීරණය කළ පසු lock කළ යුතුය.

## 12. Version 1 deliverables

1. Clean, versioned place dataset.
2. 300-prompt hidden gold evaluation set.
3. Human-reviewed Sinhala/Singlish pilot dataset.
4. Fine-tuned QLoRA adapter සහ tokenizer configuration.
5. RAG retrieval component.
6. Chat API.
7. Basic web/mobile-friendly chat interface.
8. Model card, data card සහ known-limitations document.
9. Evaluation report.

## 13. Scope-lock decision

Version 1 release statement:

> TripMe is a Sinhala-first conversational assistant for discovering and planning visits to
> Sri Lankan travel places using verified retrieved information. It does not provide booking,
> navigation, emergency response, or unsupported real-time guarantees.

මෙම statement එකට අදාළ නොවන feature එකක් Version 1 training data හෝ implementation එකට
එක් කිරීමට පෙර scope change එකක් ලෙස review කළ යුතුය.

## 14. Next milestone

මෙම scope එක approve කළ පසු ඊළඟ milestone එක වන්නේ requirements වලට සෘජුවම සම්බන්ධ
300-prompt gold evaluation set schema එක සහ category distribution එක සැලසුම් කිරීමයි.
