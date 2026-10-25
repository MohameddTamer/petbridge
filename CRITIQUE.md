# نقد ذاتي وفحص قبول, PetBridge 0.1.0

التاريخ: ٢٠٢٦-١٠-٢٤. الفحص اتعمل على كود المشروع نفسه بقاعدة بيانات مؤقتة جديدة، مش على أرقام من الذاكرة.

## ما تم فحصه بالفعل

### التشغيل والصفحات
- السيرفر أقلع من قاعدة فارغة وزرع البيانات ووصل لرسالة التشغيل.
- الصفحات الأربع رجعت 200 وبنوع HTML صحيح: العميل، الدخول، مقدم الخدمة، الإدارة.
- ملفات CSS و JavaScript الأربع و `manifest.webmanifest` و `sw.js` و `icon.svg` رجعت 200 بأنواع محتوى صحيحة.
- ملفات JavaScript الخمسة عدت `node --check` من غير أخطاء صياغة.
- مسح نصي على الواجهة أكد غياب أي تدرج لوني وكلمات purple و violet. الألوان المستخدمة رملية وتركوازية غامقة وحبر ومغرة.

### الاختبارات
الأمر: `python3 -m unittest discover -s tests -v`

النتيجة: **٢٢ اختبارًا ناجحًا في ٩٫٩٨ ثانية** بعد آخر تعديلات التكامل.

الاختبارات تغطي التصنيف، فشل الدخول وحقن SQL، تشفير كلمات المرور، شكل بيانات الزرع، تأخر التطعيم، بوابة الاعتماد كاملة، عزل الأدوار، منع مقدم الخدمة المعلق من فتح مواعيد، تدفق الحجز والمال، اقتراح موعد بديل، بوابة المنتج وطلب المحاكاة، صدق تسمية Beta في التعرف على السلالة، المجتمع والإشراف، المفقودات والتبني، ثبات سجل التدقيق، الإيقاف والتفعيل، تغيير نسبة العمولة، وصلاحيات الدعم، وملفات PWA.

### بوابة الاعتماد بالأرقام والخطوات
اتعمل حساب مقدم خدمة جديد من API التسجيل، وبعده خدمة جديدة، وكانت النتيجة:
1. الدليل العام فاضي للاسم الجديد قبل أي اعتماد.
2. لوحة الإدارة أظهرت مقدم الخدمة والخدمة في طوابير الانتظار.
3. بعد اعتماد مقدم الخدمة وحده ظل الدليل فاضيًا لأن الخدمة نفسها ما زالت معلقة.
4. بعد اعتماد الخدمة ظهر النشاط بخدمة واحدة مطابقة.
5. سجل التدقيق احتوى على `provider_approved` و `service_approved` لنفس العنصرين.

في بيانات الزرع نفسها: ٨ مقدمي خدمة معتمدين ومقدم واحد معلق، و١٥ خدمة معتمدة وخدمة واحدة معلقة، وطوابير الإدارة عند الفتح فيها مقدم وخدمة ومنتج بانتظار القرار.

### المال مقابل SQL مباشر
حجز التطعيم التجريبي في الاختبار اتحرك من معلق لمقبول لمكتمل وكانت أرقامه في الاستجابة وقاعدة البيانات معا:

| البند | القيمة |
| --- | ---: |
| سعر الخدمة | ٣٥٠ جنيه |
| نسبة العمولة وقت الحجز | ١٢٪ |
| عمولة المنصة | ٤٢ جنيه |
| صافي مقدم الخدمة | ٣٠٨ جنيه |

بعد اكتماله بقت أرباح العيادة في لوحتها: إجمالي ٨٥٠، وعمولة ١٠٢، وصافي ٧٤٨، وهي مجموع الحجز المكتمل المزروع ٥٠٠ وحجز الاختبار ٣٥٠ بنفس النسبة.

بيانات الزرع وحدها قبل أي اختبار: حجز مكتمل ٥٠٠ وعمولته ٦٠ وصافيه ٤٤٠، وطلب متجر ١٧٠ وعمولته ١٧ وصافيه ١٥٣، وإجمالي عمولات الإدارة ٧٧.

### الصحة والدليل
- ملف روكي أظهر سجل «تطعيم السعار» بحالة `overdue` في قائمة المستحقات، وتاريخ الاستحقاق قبل يوم الفحص بـ ٥ أيام نسبيًا لتاريخ الزرع.
- العمر ظهر محسوبًا من تاريخ الميلاد لا مخزنًا كنص ثابت.
- الدليل المزروع رجع ٨ مقدمين في ٣ مدن: طنطا والقاهرة والإسكندرية، و١٥ خدمة معتمدة موزعة على أقسام العيادات والحلاقة والتدريب والإقامة والمحلات والنقل والملاجئ والخدمات الإضافية.

## فجوات وجدت أثناء الفحص واتصلحت

1. مواعيد التوفر العامة التي يفتحها مقدم الخدمة من النموذج من غير ربطها بخدمة واحدة لم تكن تظهر تحت خدماته في الدليل. اتصلحت: الموعد العام يظهر تحت كل خدمات مقدمه، وفحص الحجز يقبله مع بقاء سعته مشتركة.
2. عنوان إحصائية في لوحة مقدم الخدمة كان يسمي كل الخدمات المسجلة «منشورة في الدليل» رغم وجود خدمات معلقة. اتغير العنوان إلى «خدمات مسجلة عندك».
3. خدمات مزروعة كانت ظاهرة في الدليل من غير أي موعد مفتوح فلا تصلح للحجز من الواجهة. أضيفت مواعيد للاستشارة أونلاين والطوارئ والحلاقة المتنقلة والتدريب وتوصيل المحل والنقل والتبني والتصوير.
4. اختبار بدء السيرفر كان ييأس قبل انتهاء زرع حسابات كثيرة ببصمات PBKDF2 قوية. اتصلح زمن الانتظار في harness الاختبار، والمنتج نفسه لم يضعف التشفير.

## ما لم يكتمل، بصراحة

- الصفحات لم تضغط ولم تصور في متصفح حقيقي داخل هذه البيئة، لأنه لا يوجد متصفح Chromium مثبّت فيها. الفحص كان تشغيل خادم وطلبات HTTP وفحص صياغة وربط معرفات، لا فحص عين بشري لقطات شاشة ولا اختبار جهاز أندرويد أو iOS فعلي.
- الدفع محاكاة بالكامل ومكتوب عليه كده. لا توجد بوابة دفع، والتنفيذ قبل الإطلاق يحتاج تعاقدًا ومفاتيح بيئة وحجوزات ويب هوك وتسوية بنكية.
- التعرف على السلالة Beta محلي. الواجهة ترسل اسم الملف والنوع المعلن، ونقطة النهاية تقبل أيضًا Base64 اختياريًا من عميل API، لكن لا يوجد رفع ملف ثنائي متعدد الأجزاء ولا تخزين صور ولا نموذج رؤية مدرب. لا توجد نسبة دقة معلنة في أي مكان.
- مستندات مقدم الخدمة بيانات وصفية بأسماء ملفات وحالات فقط، لا ملفات مرفوعة مخزنة ولا فحص مضمون.
- تعديل ملف مقدم الخدمة يسري فورًا ولا يمر بطابور اعتماد. البوابة الصارمة مطبقة على تسجيل النشاط والخدمات والمنتجات كما هو مخطط لهذه النسخة، واعتماد تعديلات الملف خطوة لاحقة.
- لا توجد محادثة عميل ومقدم خدمة، ولا خريطة تفاعلية، ولا إشعارات بريد أو Push، ولا اشتراك عميل مدفوع، ولا تحصيل فعلي لخطط مقدم الخدمة رغم وجود حقل الخطة ولوحة الأرباح.
- الطلبات حالتها الأولى `placed` فقط ولا توجد دورة حالة توصيل وإلغاء واسترجاع كاملة بعد.
- إدارة المواعيد فيها إنشاء وإغلاق خدمة ضمنيًا بالحجز، لكن لا يوجد حذف موعد من الواجهة الخلفية بعد.
- الجلسات بلا انتهاء تلقائي ولا يوجد حد لمحاولات الدخول. الاثنان موثقان في SECURITY كعمل إطلاق واجب، وليسا مطبقين الآن.
- SQLite وخادم واحد قرار إطلاق أول واع. أي نمو يتجاوز مدينة أو مدينتين يحتاج نقل قاعدة البيانات وخدمة ملفات ومراقبة تشغيل حقيقية.

## Redesign and English conversion, 2026-10-24 (0.2.0)

Everything user-facing was converted to English only and the three portals were rebuilt as three distinct identities of one brand (full rationale in DESIGN.md): the client portal as a Hand-Drawn Companion, the provider portal as a disciplined Bento Studio Console, and the admin console as a Monochrome Swiss Console with a permanent audit rail. FULL-SPEC.md stays as the Arabic planning record, as agreed. Backend logic and money math were not touched.

### What was converted

- Backend display text: the 35-service taxonomy and 8 category labels, the breed profiles and result labels, every API error message, the age label format ("2 years and 3 months"), the simulated payment labels, and all seed display data, people, businesses, cities, areas, addresses, pets, health records, reviews, posts, lost and found, adoptions, articles and products. The Egyptian setting is kept in English words: Nile Veterinary Clinic in Tanta on El Bahr Street, Warda Pet Salon in Cairo, Rizk Dog Training Academy in Alexandria.
- The only Arabic left anywhere in the codebase is inside `breed.py`'s alias lists, where Arabic words act as input matchers for file names, they are never displayed.
- Tests that asserted the old strings were updated to the English ones (clinic name, the rabies record, "Simulated" in the payment label, breed "Baladi", `lang="en"` in test_19).

### Tests before and after

- Before the conversion: `python3 -m unittest discover -s tests`, 22 tests, OK.
- After the backend conversion, before the frontend rewrite: 21 of 22, with the single expected failure being test_19 waiting for `lang="en"` pages.
- After the frontend rewrite: **22 tests, OK.** All five JavaScript files also pass `node --check`, and a live boot served all four pages plus CSS, manifest, service worker and icon at 200 with correct content types.

### Numbers unchanged, proof

Verified against a fresh seed in a throwaway database after the conversion, by direct SQL:

| Item | Before | After |
| --- | ---: | ---: |
| Completed seed booking total / commission / net | 500 / 60 / 440 | 500 / 60 / 440 |
| Seed shop order total / commission / net | 170 / 17 / 153 | 170 / 17 / 153 |
| Admin commission total on seed | 77 | 77 |
| Vaccine booking flow (test_09): total / commission / net | 350 / 42 / 308 | 350 / 42 / 308 |
| Clinic earnings after that flow: gross / commission / net | 850 / 102 / 748 | 850 / 102 / 748 |

Only display strings changed in `seed.py`, `taxonomy.py`, `breed.py` and `app.py`; every price, date, phone, email, password and rate is byte-identical.

### Honest gaps in this pass

- The new portals were verified by HTTP responses, identifier cross-checks between HTML and JS, and syntax checks, not by clicking through a real browser in this environment (no Chromium installed), so the hand-circled confirmation draw, the bento spark bars and the audit rail's sticky behaviour have not been seen rendering live.
- The bento spark bars are computed from the bookings list already returned by the dashboard API; there is no dedicated earnings time-series endpoint, so the bars show per-booking nets in order rather than a calendar series.
- The admin "expand row to inspect" idea from the research was simplified: queue rows carry their decision inline, but there is no expandable detail drawer, the documents list behind a provider registration is not shown inside the queue row.
- Fonts load from Google Fonts CDN with system fallbacks; offline, the portals keep their layout and tone but lose the Nunito/Sora/Inter Tight voices.
- The client paw-print trail is a static drawn path with prints resting on it; the scroll-following draw from the research note was not implemented.
