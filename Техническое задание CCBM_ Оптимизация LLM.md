# **Детерминированная оптимизация и математическая верификация контекстного окна больших языковых моделей в архитектуре Certified Context Budget Manager (CCBM)**

Развитие систем искусственного интеллекта к марту 2026 года привело к возникновению фундаментального противоречия между физическим размером контекстного окна современных больших языковых моделей (LLM) и их фактической способностью к удержанию внимания. Несмотря на наличие моделей с контекстом более одного миллиона токенов, эмпирические данные подтверждают сохранение эффекта «потери в середине» (lost-in-the-middle) и феномена «деградации контекста», при котором плотность информационного шума экспоненциально снижает точность логического вывода.1 В условиях жесткого регулирования данных в финансовом, медицинском и юридическом секторах, особенно с учетом вступления в силу Закона Республики Казахстан «Об искусственном интеллекте» и положений Цифрового кодекса, возникла острая необходимость в создании промежуточного слоя (middleware), способного гарантировать математическую целостность критических данных при агрессивном сжатии контекста.3 Проект Certified Context Budget Manager (CCBM) представляет собой решение этой проблемы на уровне L7 модели OSI, обеспечивая детерминированную оптимизацию ресурсов при строгом соблюдении инвариантов данных.

## **1\. Теоретические основы детерминированной оптимизации контекста**

Современная парадигма управления контекстом в 2026 году отходит от простых эвристик в сторону теории информационного узкого горлышка (Information Bottleneck) и методов семантической дистилляции.6 Основная задача CCBM заключается в минимизации целевой функции стоимости, определяемой как разница между количеством входящих и исходящих токенов, при соблюдении ограничений на допустимое искажение критических спанов.8

### **1.1. Проблема избыточности естественного языка и кода**

Естественный язык по своей природе обладает высокой степенью избыточности. Исследования 2025–2026 годов показывают, что до 80% токенов в типичном длинном промпте могут быть удалены без потери семантического ядра, если процесс удаления управляется моделью, понимающей структуру задачи.7 В области программного кода ситуация еще более выражена: удаление «синтаксического сахара» при сохранении графа управления и иерархии классов позволяет сократить объем данных на 66–80%, увеличивая при этом точность работы агентов с 30% до 97% за счет концентрации внимания модели на архитектурных связях, а не на многословных комментариях или форматировании.7

Архитектура CCBM опирается на принцип, согласно которому «дистиллированная информация» всегда эффективнее «зашумленного объема». Для достижения этого используется многоуровневая классификация текстовых спанов, где каждому сегменту присваивается вес критичности $w\_i \\in $.8

### **1.2. Эволюция механизмов токенизации**

Эффективность сжатия контекста в 2026 году напрямую зависит от используемых словарей токенизации. Переход от стандарта cl100k\_base к o200k\_base позволил существенно повысить плотность упаковки информации для кириллических и тюркских языков, что критично для казахстанского сегмента.11 Увеличение словаря до 200 000 токенов снизило коэффициент «токен/слово» для русского и казахского языков, позволяя CCBM оперировать более крупными смысловыми единицами на этапе предварительного анализа.11

| Семейство токенизаторов | Размер словаря | Применимость в 2026 г. | Эффективность для КЗ (RU/KZ) |
| :---- | :---- | :---- | :---- |
| r50k\_base | \~50,000 | Устаревшие модели (Legacy) | Низкая (высокая избыточность) |
| cl100k\_base | \~100,000 | GPT-4, Claude 3.0 | Средняя |
| o200k\_base | \~200,000 | GPT-4o, модели 2026 года | Высокая (оптимальная плотность) |
| BERT-Multilingual | \~110,000 | Локальные NER-системы | Высокая (для задач классификации) |

Использование специализированных движков, таких как LoPace (Lossless Optimized Prompt Accurate Compression Engine), демонстрирует возможность достижения среднего коэффициента сжатия 4.89x при сохранении возможности 100% восстановления исходного текста для аудита.10

## **2\. Математическая верификация целостности данных через границы Чернова**

Ключевым отличием CCBM от существующих решений по сжатию промптов (таких как LLMLingua) является наличие слоя верификации, основанного на концентрационных неравенствах.6 В критических доменах, таких как финансы, недопустимо даже минимальное искажение числовых данных в процессе суммаризации.

### **2.1. Контроль численного дрейфа**

Для каждого набора числовых данных ![][image1] в контексте, CCBM вычисляет математическое ожидание до и после сжатия. Использование аддитивной границы Чернова позволяет установить строгую верхнюю границу вероятности того, что ошибка превысит заданный порог ![][image2].6

Формула проверки имеет вид:

![][image3]  
где ![][image4] — среднее значение до оптимизации, ![][image5] — после, а ![][image6] — размер выборки числовых инвариантов.6

Если вычисленная вероятность ![][image7] превышает уровень значимости ![][image8] (установленный на уровне 0.01 для финансовых транзакций), система автоматически помечает данный блок как COMPROMISED и выполняет откат (fallback) к оригинальному представлению данных.6 Это обеспечивает детерминированную защиту от галлюцинаций на уровне middleware, которые могут возникнуть при попытке модели «округлить» или «упростить» важные финансовые показатели в длинных отчетах.

### **2.2. Метрики семантической сохранности**

Помимо числовой точности, CCBM оценивает сохранение смысла через Information Loss Ratio (ILR). Данная метрика вычисляется как отношение взаимной информации выхода к входу:

![][image9]  
где значение ![][image10] аппроксимируется через перплексию модели.14 В 2026 году стандартом для финансового домена считается ![][image11] для критических секций и ![][image12] для контекстного наполнения.16

Дополнительно применяется BERTScore (F1), который, в отличие от классических метрик типа ROUGE, использует контекстные эмбеддинги для оценки семантического сходства. Для юридических документов в CCBM установлен порог ![][image13], что гарантирует неизменность правовых смыслов при сокращении объема документа.17

## **3\. Компонент Criticality Analyzer (CA): Иерархия спанов**

Эффективность CCBM напрямую зависит от точности модуля CA, который выполняет декомпозицию документа на структурные элементы — спаны. В 2026 году этот процесс перестал быть чисто регулярным и перешел в категорию гибридных систем, сочетающих классический синтаксический разбор с иерархическим скорингом внимания.8

### **3.1. Классификация по уровням важности**

CA распределяет данные по четырем уровням критичности, каждый из которых имеет свой протокол обработки и верификации.10

1. **L1 (Критические числовые данные):** Включает валютные суммы, процентные ставки, даты исполнения обязательств, а также государственные идентификаторы (ИИН/БИН для Казахстана). Для этих данных применяется обязательная проверка контрольных сумм (например, алгоритм модуля 11 для ИИН) и строгая фиксация в контекстном окне.20  
2. **L2 (Политики и Клаузулы):** Юридически значимые условия договоров (форс-мажор, конфиденциальность, подсудность). Анализатор использует семантическое сходство с эталонными шаблонами базы «Адилет» для идентификации критических правовых норм.4  
3. **L3 (Персональные данные \- PII):** Имена, адреса, телефоны. Здесь CA активирует специализированные модели NER (Named Entity Recognition), такие как KazRoBERTa, обученные на казахстанских наборах данных типа KazNERD.23  
4. **L4 (Контекстное наполнение):** Общие описания, пояснительный текст, исторические данные. Этот уровень является основной мишенью для агрессивного сжатия через методы суммаризации и дедупликации.1

| Уровень | Тип данных | Метод обработки | Инструментарий |
| :---- | :---- | :---- | :---- |
| L1 | Числа / ИИН | Zero-loss / Chernoff check | NumPy / SciPy / custom module |
| L2 | Правовые нормы | Template matching | Adilet DB / Embeddings |
| L3 | PII | Masking / Anonymization | KazRoBERTa / Presidio |
| L4 | Текст | Extractive Summarization | TextRank / LLMLingua-2 |

### **3.2. Специфика обработки казахского языка**

Одной из сложнейших задач CA является морфологический анализ казахского языка, который относится к агглютинативным языкам. К марту 2026 года достигнут значительный прогресс в использовании высокопроизводительных конечных автоматов (FST) для деамбигуации токенов.24 Система CCBM сначала проводит морфологический разбор, выделяя корень и аффиксы, что позволяет более точно идентифицировать сущности (например, отличать фамилию в падежной форме от нарицательного существительного).23 Использование mBERT и KazRoBERTa в ансамбле с CRF-слоем (Conditional Random Fields) позволяет достичь точности NER выше 95% для текстов официального стиля.23

## **4\. Optimization Engine (OE): Технологии сжатия и фильтрации**

Модуль OE реализует многоступенчатый процесс сокращения объема данных, применяя различные стратегии в зависимости от типа спана и текущего бюджета токенов.8

### **4.1. Семантическая дедупликация и суммаризация**

Для работы с длинными историями диалогов и массивами документов CCBM применяет MinHash LSH (Locality Sensitive Hashing).8 Этот алгоритм позволяет быстро находить почти идентичные фрагменты текста с порогом сходства по Жаккару ![][image14]. Дубликаты удаляются, оставляя лишь наиболее свежую или информационно насыщенную версию спана.8

Иерархическая суммаризация для L4-спанов выполняется преимущественно экстрактивными методами. В отличие от абстрактивного сжатия, которое часто генерирует новые токенов (и, как следствие, риск галлюцинаций), экстрактивные модели выбирают наиболее значимые предложения из оригинала.8 Это гарантирует, что каждое слово в сжатом промпте физически присутствовало в исходном тексте, что критично для последующего аудита.

Исследования 2026 года в области SWE-Pruner показывают, что для автономных агентов наиболее эффективным является метод «маскирования наблюдений» (Observation Masking).2 Вместо того чтобы просить LLM суммаризировать логи выполнения программы, CCBM заменяет их заглушкой \[Output Omitted\], сохраняя при этом команды агента и его рассуждения. Это предотвращает «удлинение траектории», когда агент теряет фокус из\-за того, что суммаризация сгладила критические ошибки в логах.2

### **4.2. Адаптивное управление бюджетом и стратегия FOCUS**

В условиях высоконагруженных систем CCBM внедряет стратегию FOCUS (Framework for Optimized Compute and Under-sampled Sampling), которая идентифицирует «перспективные» токены на ранних слоях обработки.28 Поскольку в DLLM (Diffusion LLM) только около 10% токенов являются декодируемыми на каждом шаге, FOCUS позволяет отсекать ненужные вычисления, снижая количество обрабатываемых токенов на 65–80% без потери качества генерации.28

Эта стратегия трансформирует инференс из категории memory-bound (ограниченный памятью) в compute-bound (ограниченный вычислениями), что позволяет масштабировать CCBM на кластерах с GPU, эффективно используя блоки параллельных вычислений для обработки только релевантных частей контекста.28

## **5\. Роль Model Context Protocol (MCP) в архитектуре CCBM**

Model Context Protocol (MCP), ставший отраслевым стандартом к началу 2026 года, служит основным интерфейсом взаимодействия между агентом и CCBM.29 Использование JSON-RPC 2.0 обеспечивает типизированный и безопасный обмен сообщениями между хостом (LLM-приложением) и сервером (CCBM).31

### **5.1. Двунаправленное взаимодействие и Sampling**

Обновление спецификации MCP 2026 года привнесло возможность «сэмплирования» — механизма, позволяющего серверу инициировать запросы к LLM через клиент.32 Для CCBM это означает возможность проведения «итеративной оптимизации»:

1. Сервер CCBM получает сырой контекст.  
2. CA выделяет потенциально неважные спаны.  
3. Через sampling/createMessage сервер запрашивает мнение модели: «Могу ли я удалить этот сегмент ![][image15] без ущерба для текущей задачи?».32  
4. Модель подтверждает или отклоняет удаление, обеспечивая динамическое и контекстно-зависимое управление бюджетом.

### **5.2. Безопасность и расширение AttestMCP**

Интеграция с внешними инструментами через MCP порождает новые риски безопасности, включая атаки через вредоносные описания инструментов и инъекции в контекст.33 Протокол AttestMCP решает эту проблему путем внедрения обязательной аттестации возможностей и аутентификации сообщений.36

В CCBM AttestMCP используется для маркировки происхождения каждого оптимизированного спана. Это гарантирует, что данные в контекстном окне не были подменены в процессе передачи или обработки промежуточными слоями.36 Использование origin tagging на уровне протокола позволяет снизить успешность автономных кибератак с 52.8% до 12.4%, добавляя всего 8.3 мс задержки на сообщение.36

## **6\. Audit Engine (AE): Неизменяемость и прослеживаемость**

Для соответствия требованиям регуляторов (SEC, HIPAA, НБ РК), CCBM реализует систему неизменяемого логирования всех трансформаций контекста через построение деревьев Меркла.37

### **6.1. Построение деревьев Меркла и криптографические квитанции**

Каждый запрос к LLM сопровождается VerificationReceipt (квитанцией верификации).4 Листья дерева Меркла формируются из хешей оригинальных спанов, их меток критичности и лога примененных операций (например, SHA-256(Concat(span\_hash, tag, timestamp))).37

Использование структуры дерева позволяет генерировать компактные доказательства включения (inclusion proofs) и доказательства согласованности (consistency proofs), что критично для долгосрочного хранения аудиторских следов.37 В 2026 году для этих целей рекомендуются библиотеки на языке Rust с привязками к Python, такие как rs-merkle-tree, способные обрабатывать до 22 000 вставок в секунду с временем извлечения доказательства около 14 мкс.40

### **6.2. Интеграция с блокчейн-анкорингом**

Для обеспечения абсолютной неоспоримости (non-repudiation) в CCBM реализован опциональный слой анкоринга, где корневой хеш Merkle Root периодически записывается в публичный или приватный блокчейн.37 Это создает временную метку, которую невозможно подделать задним числом, что является ключевым требованием для юридических агентов, проверяющих комлпаенс в банковской сфере Казахстана.3

## **7\. Регуляторный ландшафт Казахстана: AI Law 230-VIII и Digital Code**

К марту 2026 года Казахстан сформировал одну из самых прогрессивных правовых баз в СНГ для регулирования систем ИИ. CCBM спроектирован как инструмент исполнения этих норм «по умолчанию» (compliance by design).4

### **7.1. Требования к высокорисковым системам**

Закон «Об искусственном интеллекте» (№ 230-VIII ЗРК) вводит риск-ориентированный подход.3 Системы, работающие с финансовыми рисками или медицинской диагностикой, классифицируются как высокорисковые.4

Для таких систем обязательными являются:

* **Ежегодный аудит:** Проводится частными аудиторами, имеющими соответствующую аккредитацию.3 CCBM упрощает этот процесс, предоставляя структурированные деревья Меркла, которые подтверждают, что данные не искажались при сжатии.  
* **Национальная платформа ИИ:** Разработка и обучение моделей должны проходить в контролируемой среде.4 CCBM поддерживает развертывание в локальных дата-центрах (Астана, Алматы), обеспечивая суверенитет данных.5  
* **Объяснимость решений:** Пользователь имеет право получить информацию о данных, на основе которых ИИ принял решение.4 Квитанции CCBM сохраняют ссылки на оригинальные источники данных до их суммаризации, выполняя это требование.

### **7.2. Цифровой кодекс и права субъектов данных**

Цифровой кодекс Республики Казахстан, вступающий в силу в июле 2026 года, закрепляет право граждан на удаление, деперсонализацию и ограничение обработки своих данных.45

CCBM реализует механизмы исполнения этих прав через:

* **Citizen’s Digital Space:** Интеграция с государственными порталами через MCP позволяет уведомлять граждан о каждом случае доступа ИИ-агента к их персональным данным.45  
* **Право на «забвение» в контексте:** CCBM позволяет мгновенно удалять спаны L3 (PII) из всех кэшей KV (Key-Value) и исторических логов по запросу пользователя, не нарушая при этом целостность остального контекста.45

## **8\. Рекомендации по реализации: 10 очевидных советов**

1. **Используйте современные токенизаторы:** Стандарт o200k\_base является обязательным для минимизации потерь на кириллице и спецсимволах.11  
2. **Внедрите гибридную NER-систему:** Сочетание KazRoBERTa для казахского языка и регулярных выражений для структурированных данных (ИИН/БИН) обеспечивает максимальный охват.23  
3. **Стандартизируйте интерфейсы через MCP:** Использование Model Context Protocol гарантирует совместимость с широким стеком инструментов и моделями разных провайдеров.29  
4. **Соблюдайте правила маркировки ИИ-контента:** Согласно ст. 21 Закона РК об ИИ, все результаты работы системы должны быть помечены как созданные ИИ в машиночитаемом и визуальном форматах.3  
5. **Локализуйте инфраструктуру:** Для обработки данных казахстанских резидентов используйте отечественные облачные решения (например, Tier-III дата-центры в Астане) для соблюдения принципа технологического суверенитета.5  
6. **Применяйте экстрактивную суммаризацию:** Это единственный способ гарантировать отсутствие галлюцинаций в сжатом контексте на этапе middleware.8  
7. **Оптимизируйте TTFT (Time To First Token):** Используйте мягкое сжатие сегментов и кэширование KV-кэша для часто используемых документов в RAG-системах.42  
8. **Шифруйте PII-данные на всех этапах:** Все спаны уровня L3 должны быть защищены алгоритмами AES-256-GCM перед записью в аудиторские логи.33  
9. **Используйте BERTScore для оценки качества:** Это более надежная метрика семантического сходства, чем BLEU или ROUGE, особенно в финансовом домене.17  
10. **Регулярно обновляйте реестр рисков:** Согласно ст. 18 Закона об ИИ, управление рисками — это непрерывный процесс, требующий ежегодной актуализации документации.4

## **9\. Рекомендации по реализации: 10 неочевидных инсайтов**

1. **Применяйте e-процессы для остановки генерации:** Использование последовательного тестирования гипотез через e-процессы позволяет сократить длину вывода на 22–28%, определяя момент достижения «информационной достаточности» с δ-уровнем контроля ошибок.49  
2. **Используйте AST-дистилляцию для кода:** Вместо удаления токенов на основе перплексии, проводите синтаксический разбор кода и удаляйте избыточные узлы абстрактного синтаксического дерева, сохраняя логический граф нетронутым.7  
3. **Диагностируйте «визуальную амнезию»:** При работе с мультимодальными данными (MLLM) отслеживайте дивергенцию Кульбака-Лейблера (KL), чтобы убедиться, что сжатие визуальных токенов не привело к потере ключевых областей изображения после первых слоев.51  
4. **Разделяйте «достаточность» и «фактическую точность»:** CCBM подтверждает наличие нужной информации в контексте, но не гарантирует отсутствие галлюцинаций модели. Всегда используйте «гибридные ворота корректности» с легковесным верификатором на финальном выходе.49  
5. **Внедрите «конфликтно-зависимое укрупнение» памяти:** При формировании долгосрочной памяти агента объединяйте статические дубликаты, но сохраняйте переходы состояний как временные ребра в графе знаний.53  
6. **Используйте BBoxER для обобщения границ:** Применяйте эволюционные методы оптимизации черного ящика для получения невакуумных границ обобщения, которые зависят от сложности траектории оптимизации, а не от количества параметров модели.6  
7. **Перейдите к «compute-bound» режиму инференса:** С помощью системы FOCUS отсекайте недекодируемые токены на ранних этапах диффузионного процесса в LLM, что позволяет повысить пропускную способность до 3.52x.28  
8. **Маскируйте наблюдения вместо суммаризации логов:** Для агентов программной инженерии простое скрытие вывода инструментов с сохранением их имен эффективнее с точки зрения точности выполнения задачи, чем интеллектуальное сжатие лога.2  
9. **Обучайте CI-агентов через RL:** Вместо статических фильтров используйте обучение с подкреплением (RL), чтобы научить модель рассуждать о «контекстуальной целостности» (CI) и уместности раскрытия конкретной информации в данном сценарии.55  
10. **Интегрируйте Direct-to-Cell для распределенных узлов:** В удаленных регионах Казахстана используйте спутниковые технологии для синхронизации локальных CCBM-узлов в условиях ограниченной наземной связи.44

## **10\. Исследование GitHub-экосистемы для CCBM (март 2026\)**

Для успешной реализации MVP CCBM необходимо опираться на проверенные open-source компоненты, оптимизированные под требования производительности и безопасности.

### **10.1. Библиотеки сжатия и оптимизации контекста**

* **microsoft/LLMLingua** ([GitHub](https://github.com/microsoft/LLMLingua)): Отраслевой стандарт для сжатия промптов. Реализует алгоритмы LongLLMLingua и LLMLingua-2, обеспечивающие до 20x сжатия при сохранении точности.9  
* **liyucheng09/Selective\_Context** ([GitHub](https://github.com/liyucheng09/Selective_Context)): Библиотека для оценки информативности лексических единиц на основе self-information базовой модели.58  
* **connectaman/LoPace** ([GitHub](https://github.com/connectaman/LoPace)): Движок для безпотерьного сжатия промптов, сочетающий Zstandard и токенизацию BPE с бинарной упаковкой.10  
* **atjsh/llmlingua-2-js** ([GitHub](https://github.com/atjsh/llmlingua-2-js)): Порт LLMLingua-2 на TypeScript/JavaScript, позволяющий выполнять сжатие контекста непосредственно в браузере с использованием WebGPU.18

### **10.2. Математическая верификация и аудит**

* **vpaliy/merklelib** ([GitHub](https://github.com/vpaliy/merklelib)): Высокопроизводительная Python-библиотека для работы с деревьями Меркла. Поддерживает генерацию доказательств аудита и проверку целостности версий БД.37  
* **clockinchain/chrono-merkle** ([GitHub](https://github.com/clockinchain/chrono-merkle)): Реализация «временно-зависимых» деревьев Меркла (Time-aware Merkle trees), обеспечивающая в 10–100 раз более быстрое обновление для логов аудита.59  
* **OffchainLabs/hashtree** ([GitHub](https://github.com/OffchainLabs/hashtree)): Ассемблерная реализация SHA-256, оптимизированная под векторные инструкции (AVX-512), обеспечивающая запредельную скорость хеширования для Merkle Proofs.60

### **10.3. Решения для PII и безопасности данных**

* **IS2AI/KazNERD** ([GitHub](https://github.com/IS2AI/KazNERD)): Крупнейший датасет и код для Named Entity Recognition на казахском языке. Включает поддержку BERT и XLM-RoBERTa моделей.23  
* **HydroXai/pii-masker** ([GitHub](https://github.com/HydroXai/pii-masker)): Система на базе DeBERTa-v3 для обнаружения и маскирования PII с поддержкой контекстов до 1024 токенов.61  
* **mddunlap924/PII-Detection** ([GitHub](https://github.com/mddunlap924/PII-Detection)): Фреймворк для создания синтетических PII-датасетов и дообучения моделей на специфические failure-моды детектирования.62

### **10.4. Middleware и LLM-шлюзы**

* **Helicone/helicone** ([GitHub](https://github.com/Helicone/helicone)): Легковесный прокси на Rust для мониторинга и маршрутизации запросов к LLM. Обеспечивает детальную обсервабилити и управление стоимостью.63  
* **LiteLLM** ([GitHub](https://github.com/berriai/litellm)): Универсальный шлюз, позволяющий использовать единый формат OpenAI API для взаимодействия с более чем 100 провайдерами моделей.64  
* **mcp-sdk/python** ([GitHub](https://github.com/modelcontextprotocol/python-sdk)): Официальный SDK для реализации серверов Model Context Protocol, обеспечивающий бесшовную интеграцию CCBM в современные агентские циклы.32

## **11\. Заключение: Переход к «сертифицированному» интеллекту**

Анализ состояния технологий и регуляторной среды на 6 марта 2026 года подтверждает, что успех внедрения LLM в корпоративный сектор больше не определяется только мощностью модели. Решающим фактором становится наличие слоя верификации, способного доказать математическую точность и юридическую чистоту данных, на которых базируется вывод ИИ.6

Архитектура Certified Context Budget Manager (CCBM) предлагает сбалансированный подход, объединяющий агрессивную оптимизацию контекста для снижения затрат и криптографический аудит для обеспечения доверия.5 Для казахстанских компаний этот путь является безальтернативным ввиду строгих требований Цифрового кодекса и необходимости обеспечения технологического суверенитета в условиях глобальной конкуренции моделей.4

Реализация CCBM на базе Model Context Protocol с использованием границ Чернова для контроля численного дрейфа позволяет создавать системы, которые не просто «рассуждают», но и несут ответственность за каждое слово в своем контекстном окне.3 Будущее за детерминированным и проверяемым ИИ, где каждый потраченный токен является инвестицией в обоснованный и безопасный результат.

#### **Источники**

1. Characterizing Prompt Compression Methods for Long Context Inference \- arXiv, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2407.08892v1](https://arxiv.org/html/2407.08892v1)  
2. Context Length Management in LLM Applications by cbarkinozer | Softtech \- Medium, дата последнего обращения: марта 6, 2026, [https://medium.com/softtechas/context-length-management-in-llm-applications-89bfc210489f](https://medium.com/softtechas/context-length-management-in-llm-applications-89bfc210489f)  
3. Kazakhstan: New Law Introduces Rules for AI Systems Operating in the Country, дата последнего обращения: марта 6, 2026, [https://www.loc.gov/item/global-legal-monitor/2026-01-12/kazakhstan-new-law-introduces-rules-for-ai-systems-operating-in-the-country/](https://www.loc.gov/item/global-legal-monitor/2026-01-12/kazakhstan-new-law-introduces-rules-for-ai-systems-operating-in-the-country/)  
4. AI Regulation and the Ministry of Artificial Intelligence in Kazakhstan \- Unicase Law Firm, дата последнего обращения: марта 6, 2026, [https://www.unicaselaw.com/blog/ai-regulation-and-ministry-of-ai-eng](https://www.unicaselaw.com/blog/ai-regulation-and-ministry-of-ai-eng)  
5. Kazakhstan Adopts Pragmatic AI Regulation in Financial Sector \- The Times Of Central Asia, дата последнего обращения: марта 6, 2026, [https://timesca.com/kazakhstan-adopts-pragmatic-ai-regulation-in-financial-sector/](https://timesca.com/kazakhstan-adopts-pragmatic-ai-regulation-in-financial-sector/)  
6. Tuning without Peeking: Provable Generalization Bounds and Robust LLM Post-Training \- arXiv.org, дата последнего обращения: марта 6, 2026, [https://arxiv.org/pdf/2507.01752](https://arxiv.org/pdf/2507.01752)  
7. \[Research\] I achieved 97% accuracy with 80% context compression \- BETTER than using full context (30%) : r/ClaudeAI \- Reddit, дата последнего обращения: марта 6, 2026, [https://www.reddit.com/r/ClaudeAI/comments/1qdxmu3/research\_i\_achieved\_97\_accuracy\_with\_80\_context/](https://www.reddit.com/r/ClaudeAI/comments/1qdxmu3/research_i_achieved_97_accuracy_with_80_context/)  
8. LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression | Request PDF \- ResearchGate, дата последнего обращения: марта 6, 2026, [https://www.researchgate.net/publication/384217654\_LLMLingua-2\_Data\_Distillation\_for\_Efficient\_and\_Faithful\_Task-Agnostic\_Prompt\_Compression](https://www.researchgate.net/publication/384217654_LLMLingua-2_Data_Distillation_for_Efficient_and_Faithful_Task-Agnostic_Prompt_Compression)  
9. LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression \- arXiv, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2310.06839v2](https://arxiv.org/html/2310.06839v2)  
10. LoPace: A Lossless Optimized Prompt Accurate Compression Engine for Large Language Model Applications \- ResearchGate, дата последнего обращения: марта 6, 2026, [https://www.researchgate.net/publication/400855054\_LoPace\_A\_Lossless\_Optimized\_Prompt\_Accurate\_Compression\_Engine\_for\_Large\_Language\_Model\_Applications](https://www.researchgate.net/publication/400855054_LoPace_A_Lossless_Optimized_Prompt_Accurate_Compression_Engine_for_Large_Language_Model_Applications)  
11. LoPace: A Lossless Optimized Prompt Accurate Compression Engine for Large Language Model Applications \- arXiv, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2602.13266v1](https://arxiv.org/html/2602.13266v1)  
12. Tuning without Peeking: Provable Privacy and Generalization Bounds for LLM Post-Training, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2507.01752v1](https://arxiv.org/html/2507.01752v1)  
13. TEST-TIME SCALING VIA METRIC GEOMETRY FOR LLM, дата последнего обращения: марта 6, 2026, [https://openreview.net/pdf/f499e85cd366fe71ff5a840d089252deeef19c66.pdf](https://openreview.net/pdf/f499e85cd366fe71ff5a840d089252deeef19c66.pdf)  
14. CCF: A Context Compression Framework for Efficient Long-Sequence Language Modeling, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2509.09199v1](https://arxiv.org/html/2509.09199v1)  
15. Waiting to Decompress:The Economics of LLM-Based Compression \- VLDB Endowment, дата последнего обращения: марта 6, 2026, [https://www.vldb.org/cidrdb/papers/2026/p34-kipf.pdf](https://www.vldb.org/cidrdb/papers/2026/p34-kipf.pdf)  
16. Compressing Context to Enhance Inference Efficiency of Large Language Models \- ResearchGate, дата последнего обращения: марта 6, 2026, [https://www.researchgate.net/publication/376401484\_Compressing\_Context\_to\_Enhance\_Inference\_Efficiency\_of\_Large\_Language\_Models](https://www.researchgate.net/publication/376401484_Compressing_Context_to_Enhance_Inference_Efficiency_of_Large_Language_Models)  
17. Retrieval-based neural source code summarization | Request PDF \- ResearchGate, дата последнего обращения: марта 6, 2026, [https://www.researchgate.net/publication/346018520\_Retrieval-based\_neural\_source\_code\_summarization](https://www.researchgate.net/publication/346018520_Retrieval-based_neural_source_code_summarization)  
18. JavaScript/TypeScript implementation of LLMLingua-2 (Experimental) \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/atjsh/llmlingua-2-js](https://github.com/atjsh/llmlingua-2-js)  
19. FTP: Efficient Prefilling for Long-Context LLM Inference via FFN Token Pruning, дата последнего обращения: марта 6, 2026, [https://openreview.net/forum?id=fL8Zp8o6RL](https://openreview.net/forum?id=fL8Zp8o6RL)  
20. Avoid UUID Version 4 Primary Keys in Postgres \- Hacker News, дата последнего обращения: марта 6, 2026, [https://news.ycombinator.com/item?id=46272487](https://news.ycombinator.com/item?id=46272487)  
21. vonlab/kz-iin: A PHP library for working with Kazakhstan Individual Identification Numbers (IIN). \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/vonlab/kz-iin](https://github.com/vonlab/kz-iin)  
22. Kazakhstan: An Overview Law | Chambers and Partners, дата последнего обращения: марта 6, 2026, [https://chambers.com/content/item/7088](https://chambers.com/content/item/7088)  
23. An open-source Kazakh named entity recognition dataset (KazNERD), annotation guidelines, and baseline NER models. \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/IS2AI/KazNERD](https://github.com/IS2AI/KazNERD)  
24. Hybrid artificial intelligence architectures for automatic text correction in the Kazakh language \- Frontiers, дата последнего обращения: марта 6, 2026, [https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1708566/full](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1708566/full)  
25. Solutions of the problems NER and RE in the domain of business documents with the BERT+CRF model. \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/borisshapa/bert-crf](https://github.com/borisshapa/bert-crf)  
26. LCLM-Horizon/A-Comprehensive-Survey-For-Long-Context-Language-Modeling \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/LCLM-Horizon/A-Comprehensive-Survey-For-Long-Context-Language-Modeling](https://github.com/LCLM-Horizon/A-Comprehensive-Survey-For-Long-Context-Language-Modeling)  
27. Learn Compression Target via Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression \- LLMLingua-2, дата последнего обращения: марта 6, 2026, [https://llmlingua.com/llmlingua2.html](https://llmlingua.com/llmlingua2.html)  
28. FOCUS: DLLMs Know How to Tame Their Compute Bound \- arXiv, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2601.23278v1](https://arxiv.org/html/2601.23278v1)  
29. Specification \- Model Context Protocol, дата последнего обращения: марта 6, 2026, [https://modelcontextprotocol.io/specification/2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)  
30. Term: Model Context Protocol (MCP) \- Global Advisors | Quantified Strategy Consulting, дата последнего обращения: марта 6, 2026, [https://globaladvisors.biz/2026/02/23/term-model-context-protocol-mcp/](https://globaladvisors.biz/2026/02/23/term-model-context-protocol-mcp/)  
31. What is the Model Context Protocol (MCP)? \- Elastic, дата последнего обращения: марта 6, 2026, [https://www.elastic.co/what-is/mcp](https://www.elastic.co/what-is/mcp)  
32. MCP Protocol Guide (2026): Build AI-Powered Agent Tools | PythonAlchemist, дата последнего обращения: марта 6, 2026, [https://www.pythonalchemist.com/blog/mcp-protocol](https://www.pythonalchemist.com/blog/mcp-protocol)  
33. Security Analysis of the Model Context Protocol Specification and Prompt Injection Vulnerabilities in Tool-Integrated LLM Agents \- arXiv.org, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2601.17549v1](https://arxiv.org/html/2601.17549v1)  
34. 4 Scam Trends That Will Define 2026 (And How to Protect Yourself) \- ScamWatchHQ, дата последнего обращения: марта 6, 2026, [https://www.scamwatchhq.com/4-scam-trends-that-will-define-2026-and-how-to-protect-yourself/](https://www.scamwatchhq.com/4-scam-trends-that-will-define-2026-and-how-to-protect-yourself/)  
35. Why the Model Context Protocol Won \- The New Stack, дата последнего обращения: марта 6, 2026, [https://thenewstack.io/why-the-model-context-protocol-won/](https://thenewstack.io/why-the-model-context-protocol-won/)  
36. Security Analysis of the Model Context Protocol Specification and Prompt Injection Vulnerabilities in Tool-Integrated LLM Agents \- arXiv.org, дата последнего обращения: марта 6, 2026, [https://www.arxiv.org/pdf/2601.17549](https://www.arxiv.org/pdf/2601.17549)  
37. vpaliy/merklelib: Merkle trees for easier data verification. \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/vpaliy/merklelib](https://github.com/vpaliy/merklelib)  
38. The Law of the Republic of Kazakhstan dated November 17, 2025 No. 230-VIII “On Artificial Intelligence” was adopted \- Legal 500, дата последнего обращения: марта 6, 2026, [https://www.legal500.com/developments/press-releases/the-law-of-the-republic-of-kazakhstan-dated-november-17-2025-no-230-viii-on-artificial-intelligence-was-adopted/](https://www.legal500.com/developments/press-releases/the-law-of-the-republic-of-kazakhstan-dated-november-17-2025-no-230-viii-on-artificial-intelligence-was-adopted/)  
39. fmerg/pymerkle: Merkle-tree in Python \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/fmerg/pymerkle](https://github.com/fmerg/pymerkle)  
40. Introducing rs-merkle-tree, a modular, high-performance Merkle Tree library for Rust. : r/rust, дата последнего обращения: марта 6, 2026, [https://www.reddit.com/r/rust/comments/1occ7un/introducing\_rsmerkletree\_a\_modular/](https://www.reddit.com/r/rust/comments/1occ7un/introducing_rsmerkletree_a_modular/)  
41. Kazakhstan Advances Human-Centered AI With New Law, Governance Program, and UNESCO Assessment \- The Astana Times, дата последнего обращения: марта 6, 2026, [https://astanatimes.com/2026/01/kazakhstan-advances-human-centered-ai-with-new-law-governance-program-and-unesco-assessment/](https://astanatimes.com/2026/01/kazakhstan-advances-human-centered-ai-with-new-law-governance-program-and-unesco-assessment/)  
42. The Law of the Republic of Kazakhstan “On Artificial Intelligence” has been adopted \- EY, дата последнего обращения: марта 6, 2026, [https://www.ey.com/en\_kz/technical/tax-alerts/2025/12/law-on-artificial-intelligence-kazakhstan](https://www.ey.com/en_kz/technical/tax-alerts/2025/12/law-on-artificial-intelligence-kazakhstan)  
43. deeppavlov/Slavic-BERT-NER: Shared BERT model for 4 languages of Bulgarian, Czech, Polish and Russian. Slavic NER model. \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/deeppavlov/Slavic-BERT-NER](https://github.com/deeppavlov/Slavic-BERT-NER)  
44. Year of Digitalization and AI: Kazakhstan accelerates its digital breakthrough \- el.kz, дата последнего обращения: марта 6, 2026, [https://el.kz/en/year-of-digitalization-and-ai-kazakhstan-accelerates-its-digital-breakthrough\_400044858/](https://el.kz/en/year-of-digitalization-and-ai-kazakhstan-accelerates-its-digital-breakthrough_400044858/)  
45. What Kazakhstan's Digital Code Brings to Citizens and Businesses \- The Astana Times, дата последнего обращения: марта 6, 2026, [https://astanatimes.com/2026/02/what-kazakhstans-digital-code-brings-to-citizens-and-businesses/](https://astanatimes.com/2026/02/what-kazakhstans-digital-code-brings-to-citizens-and-businesses/)  
46. Kazakhstan passes legislation to enhance digital rights \- Xinhua, дата последнего обращения: марта 6, 2026, [https://english.news.cn/asiapacific/20260110/c5fdd9a844f74543982b4eff76b127da/c.html](https://english.news.cn/asiapacific/20260110/c5fdd9a844f74543982b4eff76b127da/c.html)  
47. CompLLM: Compression for Long Context Q\&A \- arXiv, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2509.19228v1](https://arxiv.org/html/2509.19228v1)  
48. What It Takes to Run MCP (Model Context Protocol) in Production | by ByteBridge \- Medium, дата последнего обращения: марта 6, 2026, [https://bytebridge.medium.com/what-it-takes-to-run-mcp-model-context-protocol-in-production-3bbf19413f69](https://bytebridge.medium.com/what-it-takes-to-run-mcp-model-context-protocol-in-production-3bbf19413f69)  
49. Valid Stopping for LLM Generation via Empirical Dynamic Formal Lift \- arXiv.org, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2510.06478v1](https://arxiv.org/html/2510.06478v1)  
50. Code vs Serialized AST Inputs for LLM-Based Code Summarization: An Empirical Study, дата последнего обращения: марта 6, 2026, [https://www.researchgate.net/publication/400583918\_Code\_vs\_Serialized\_AST\_Inputs\_for\_LLM-Based\_Code\_Summarization\_An\_Empirical\_Study](https://www.researchgate.net/publication/400583918_Code_vs_Serialized_AST_Inputs_for_LLM-Based_Code_Summarization_An_Empirical_Study)  
51. Token Reduction Should Go Beyond Efficiency in Generative Models – From Vision, Language to Multimodality \- arXiv.org, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2505.18227v3](https://arxiv.org/html/2505.18227v3)  
52. Chain-of-Thought Compression Should Not Be Blind: V-Skip for Efficient Multimodal Reasoning via Dual-Path Anchoring \- arXiv, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2601.13879v2](https://arxiv.org/html/2601.13879v2)  
53. Computer Science \- arXiv.org, дата последнего обращения: марта 6, 2026, [https://arxiv.org/list/cs/new](https://arxiv.org/list/cs/new)  
54. Tuning without Peeking: Provable Generalization Bounds and Robust LLM Post-Training, дата последнего обращения: марта 6, 2026, [https://arxiv.org/html/2507.01752v3](https://arxiv.org/html/2507.01752v3)  
55. Contextual Integrity in LLMs via Reasoning and Reinforcement Learning \- arXiv.org, дата последнего обращения: марта 6, 2026, [https://arxiv.org/pdf/2506.04245](https://arxiv.org/pdf/2506.04245)  
56. LLMLingua Series \- Microsoft Research: Llmlingua 2, дата последнего обращения: марта 6, 2026, [https://www.microsoft.com/en-us/research/project/llmlingua/llmlingua-2/](https://www.microsoft.com/en-us/research/project/llmlingua/llmlingua-2/)  
57. Issues · microsoft/LLMLingua \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/microsoft/LLMLingua/issues](https://github.com/microsoft/LLMLingua/issues)  
58. liyucheng09/Selective\_Context: Compress your input to ChatGPT or other LLMs, to let them process 2x more content and save 40% memory and GPU time. \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/liyucheng09/Selective\_Context](https://github.com/liyucheng09/Selective_Context)  
59. clockinchain/chrono-merkle: Time-aware Merkle trees for blockchain, audit trails, and secure data verification \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/clockinchain/chrono-merkle](https://github.com/clockinchain/chrono-merkle)  
60. OffchainLabs/hashtree: SHA256 library highly optimized for Merkle tree computations \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/OffchainLabs/hashtree](https://github.com/OffchainLabs/hashtree)  
61. PII Masker is an open-source tool for protecting sensitive data by automatically detecting and masking PII using advanced AI, powered by DeBERTa-v3. It provides high-precision detection, scalable performance, and a simple Python API for seamless integration into workflows, ensuring privacy compliance in various industries. \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/HydroXai/pii-masker](https://github.com/HydroXai/pii-masker)  
62. mddunlap924/PII-Detection: Personal Identifiable Information (PII) entity detection and performance enhancement with synthetic data generation \- GitHub, дата последнего обращения: марта 6, 2026, [https://github.com/mddunlap924/PII-Detection](https://github.com/mddunlap924/PII-Detection)  
63. 6 Best LLM Gateways in 2026 \- TrueFoundry, дата последнего обращения: марта 6, 2026, [https://www.truefoundry.com/blog/best-llm-gateways](https://www.truefoundry.com/blog/best-llm-gateways)  
64. Top 5 AI Gateways in 2026 \- Maxim AI, дата последнего обращения: марта 6, 2026, [https://www.getmaxim.ai/articles/top-5-ai-gateways-in-2026/](https://www.getmaxim.ai/articles/top-5-ai-gateways-in-2026/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJEAAAAZCAYAAAAxO8yWAAADzUlEQVR4Xu2aTchNQRjHH6HId0SixEKxoeRbskAsSLEgdpSIUgrJ4pUVSwlJyVZ2EiLuSmIjEYkFKUWIIh/5eH7NzHvnTufrnnvfe6/T/OrfnZnnnHPPzH3OzPPMuSKRSCQSaQ+DVJNVQ0NDpDRuTAeHhqpBR3+qPqumBrZI64xV3Vf9VV0IbKmMV70Wc5LTO9VIa78XtHNsNzkp5l4iA8skMeM8ITRkMV3MSTjNGK+dcrcdx+ei6mvYGGk7TCL4A8tbYVgmOOmPao3Xfk21wKt3m+hEnaGUE8F1MSe+sfU+1cZ+a28QnagzlHaiKVKPf3aoDjSae4IiTrRCtdqrb1Ct8+pVhP7Ns2Wyq02q5XVz05R2Ivgh5uSroaFHyHIiluTvYtL+pWL68lHMoG5TPakfWhmIWZ+K6fsR1TPVbdVo1RkxiUgZWnKi51KfjcpyrgmdtucUBQe6EjZaSAqG2DJZBX1gdsXxXNJQNb545ZVi+olDvbLlPs/eLJx/LGzM45ZqoeqUmAssbjR3De7ppph7ynqyJnrlrZL/IMxWrQ0b/zPY13FclkanahVmdLZ1XkjBceKET7aM8/AD4Ey9wFkx90PmyL5WEc6rfoWNluGqE2KuWaVY6aXqQdjYItvFjBMrVCZMfww4n45Wl7SBAEfnnvaHhgR4Inkys6hJtZyIsWEGbhdMKsRXhcCBwndQrSxpZAZFRebUDAT8aYH1I9U+qe95LfNss1TrvTrUJN2JCCzDMQnJmxXz7FzfX4KT4Bj39iCEfn5TzZF6Zj3Os++07TBCzOwLS8SEBXym4QLr3FdLdJID54cGMV+Kze0Z9Qpp2RlZBPdLhkImRtllFux1kbWF1CTZiQjO82Zilg3sBLNJuCCX4/wf1sd9x+HQYHFxHUpyJO4d2yLVJVt2kLSwvDmYlQ+KiXEA5+C3Tbou5GZnbsB9+Rfbm2Dv8+zdJM2J4L2Yez2ummvLaIskv5muSbITwV0xWwRpg8z1f0tjCOBDO3aOS+OGmDjPf83kwyxEX5ht3B6Qj5txEYHvbq9O0uBDtsoWxwxbx8n57rT7z3Wi/5ksJ2qWmqQ7ERCcpw1yJ8FBcpeVAuAUDhzqg1cPiU5UkJpkO1GvvHhuR0jBTPTWq+MgmyV9ham8E/lPVBmYXRicx6pdtjys4QiRaVJio20AYEnj/z2twnLo3kIQ8/Eg0nan/4hGRkmFnYhshs4dCg1tJmtTs1Pg7HvCxpLgjH5cyEzDf4aSWCUmvnT7hpWFTbCHqpmhIVIaZmMyuqNitkQikUgkEqky/wDeP+Gq118E6gAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAYCAYAAADH2bwQAAAAYElEQVR4XmNgGAXYgDAQXwHi/1CMArYD8S8gZkaXAIFiBogOVnQJGPjHgDAWhnmQFYAETgNxCBJGASAF5eiCyOA9EM9HF0QG/AwQUwyg/DogzkVII4AyEPsCMSO6xDAHAHvdE3tKOpgCAAAAAElFTkSuQmCC>

[image3]: <data:image/png;base64,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>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAYCAYAAADOMhxqAAAAqUlEQVR4XmNgGAWDEVwE4p1oYmpA/AtNDA7+A3E0mthWIH6AJgYG0gwQDYJo4v+AuApNDAzKGSAakAE3VEwJTRwMQFa/RRMDKQRpAGnEACCr56CJtTIgbHVAEmfgYIBIgJyFDH4C8WEo+zSyhAsDRMN7KN8ViB8xQBQfAOIEIFaByoEBzP08QBzCALERBkyAWBiJDwbY3I8TsDBAnKOJLoELGDNghv+wBgDv5CC5KmK7bwAAAABJRU5ErkJggg==>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAZCAYAAAA4/K6pAAAAzUlEQVR4XmNgGKpAF4g50QVJAf+BeD66ILGAhwFigCC6BLHAD4jfowuSAlqBeDm6ICngOQMe50sCsTy6IBrA6/zfQDwJTawcKk4QsDBAQlcTSUyJAeLkrUhiOIENA8QAZAAKMJCYC5o4VgByKroBe6BiIJcQBA+A+DSaGEgzuqE4AUghyBUwAEtxb6H8l0hyGECaAaJ4CpLYLajYQiDmB+IGJDkMAPM/DP8CYlYgfoTExwseMGD6nyQAsiUaXZBYgC0BkQSMGUiIqlGACQB1mC0gt/SewQAAAABJRU5ErkJggg==>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAYCAYAAADOMhxqAAAAnUlEQVR4XmNgGAWDCQQD8Scg/grlHwfi/0D8BYh/ATEjVBwOTkBpkCJ0Bd+AuAqJz2AMxC5ALMMA0SCGLAkVK0cTAwOQKSBJZCAIFVNEEweDrUD8Fk3MkgGigQVNHAz+AfEkNLHTQPwEyrZDluBggJikiSwIFfNggNiwA1nCBiqJDkBioMC4BcSsyBIgjhqyABQwA7EvA5Z4GAVUBQC8Oh0pILbnOwAAAABJRU5ErkJggg==>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAZCAYAAADuWXTMAAAAqUlEQVR4XmNgGAVqQPwIiP9D8S8oH4SfQMU+wlXjAL+B+BMQ66OJMzJADDiBJo4CQApOA7EgugQDRA5kOFYgzgBREI0uwYCwGafmdAaIAmy2ejBA5IrRJWDgKgNEATpgZYCI70SXQAawkEbHf4FYHUkdBhBhgCgsR5cgBtgwQDSDaJLBGgaIZhZ0CWIAKApwRgM+wMEAsRVkO9GAiwEzZEGYB1nRKBi5AABfRS8IzE/i4gAAAABJRU5ErkJggg==>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAbCAYAAACuj6WAAAAAuElEQVR4XmNgGPyAFYhnAfFcIP4PxQ7ICkDAF4ifI/EbgZgRiQ8GmkD8Fohl0SWQAScQ72CAWIkXKDJA3GKGLgED5kB8nAHhaAz3cEMlTgHxNCgbZCocgLwOEuSH8jmg/Fa4CiA4AcXIAKRoIbLAPyAuRxZggCiqgnFAjgMJyMClIQAkZgzjwBTxwKUhbgOJoYBnQGyLxN8FxMFIfDAACdxlgJgKCnWQG0E+xgDMDJAIxhnSowA/AAA1FCG0o0Q6AwAAAABJRU5ErkJggg==>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAA1CAYAAAD8i7czAAAJIElEQVR4Xu3dW6h22xjA8SEUbdtxOxObnZJjOewU+i4QOSTs0rbdcMGFXBCitAlRSkKU6CMXDrlQKId9sWw3yg1FSslHbFEoRQ45zL85n/2N9/nGmO9c6z2ttb7/r0Zrvc+c72GO8a5vPt8zxnzfUiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJ0rnz4qG9MgeP4RFD+3QOngPfGdpDcnCN+w3tLTl4DJuOxaH8KQcm9xra7TkoSTrb/ji0X6f2/pU9SvlwtS3aHUO7pt6p8syh/WFo/50av8f9Pje0u9+552E8Jgf2jP65mIOTP5cr+/q1K3uUcp+h/SLFzhP6gGNcir4kScmW9OXcWNx1aHfJwVOEPuIYWziu23JQknS2kcCQWL0pb0jY52c5OONvQ/tXir2wjI/z9hTftfsO7ZYyPvfR6qa9IgHgNcx5dhn3oa9a/lHaCco2kVT/Pgd34AtDe3qKPWhof02xOb2kBXN9uW4s2HZaEuPeeHx0aO/MwclPhnZjDkqSzq4PlPHkxNRSTyR1r8kbZrD/V3OwjCfjuRPltt1jaO8d2sPK+NxHK1v36xNTm0Of0T93yxvKmHgcJ2k+qXeU3Y9RJEwkVdlvhvb8HGx4Ypl/T8715bqxuKmMVbbToDceHBfxViXw+qH9OwclSWfX70r7ZFBbktTVnlL6J2Pi655vVw6dsHHc1+VgQlUyVyYDY/W8HNwBEqYf5uCWPaP0k6mXlfE1rPOD0k5WwlxfLhmL02JuPC4N7dU5OOEYSdwkSecA/6j3TgZhSVJX+1hpn4yfMMWZyjmEQyZsDy7r+zAqJq3KJNhGxXDOC4b2qnJldeiRQ3tpivXwPDen2D3L+LiRID1+aC+/vPn/eE72WbJO8WIZp3dbri3r+wpz1ca5vpwbC177kv7jMdivtd6O6uDjpt+jT7h/LT/enNZ4hHcN7ac5OPl+Gf8WJUln3NKpziVJXY2LGXJl48llfJzXpfg+HTJhe8XQ/pKDSay5alUmuTK0l2TgI2U8PhIOkiqmw+LqR35Stfp8WT25x/OBBIcrT780xUiouE2cdnsZH+M/Q/v70O49tPtP+/KcNN4jD51itfqYbi3j4/I4v5x+b1WIuA9JUQ/Tw8/KwcpcX/bGgvVz3x7a08rqMdxQxnWXJH9U9bhCk4SLZIz9Lty5ZymfKmMSR/wzQ/vkFCd5iit7Nx2PWlQqW0jmTss6PEnSBpZMdS5N6mrsHydjrs7jNleLLsGJn/stba0KR88hEzYqHetOnnNrrpgK7Z2Y6QcSoFq97ikqUZfKauL9zTJWT2ut9VJckELyxHuAbXUFjdu8j75VxkSRRKS+P5W4fEyxfo1ko4ftJE4966ZM5/qyNxbRTxxvfQzRZ/QX8XoalvcUiVeIx2A/xiVQTdvWeNRaCXLgOXl9kqQzbslU51xSR9WHE0YtTtD5ZExC8eMU27elCVtMiy1pfI7XEpzUj3IwmVtz1Tv5RjUnJ9Rxoie54KrSmCKsq1KMSZ4yIxGiGlR7wPST5OJSFQePybFRnQL3pwoVePycTEZVaG79Gdt7U4ZMz5Igzpnry95YxDEwVfvFKn7d9LPVX7zOF02/R1/zt0L84bFT2e541NYlbL1tkqQzhH/M1011ziV19Yk5MA3E/rmy0fqYj30j4flVDu5JL0kIcQJvrblCL2GL9YJ5bRvjWo9bVMcC+3ObBLtGLCd/gW0kHoFEhtgbptutJITpcSpHtYtl/XuBx+klbLyG63Owsq4v58Yi1rfl6dhWf3Gcrfd67msw9bnt8YAJmySdc0unOtmHk01GleAoB8uYVOSTcUyB5emeljhhLm3PGe+2yCETNtYTzT333JorRFUqOyrtOLG6SsQY1uNYr5d60vSTihCxqKY+qlyugs1VjWKKtDVty20qUOzDujcwDnUydUP1e+B+vSnRVuJaW9eXc2NBn8XFEBeqeOvYSIpjava5KX6pug3u+5Xq9qbjEebWNrJWb11fSZJOuZjqjOmelkjqooISOGmwqJ3Pwcpx9s+VjfiYj6jmURWIq+j26ZAJG0kLVcaeWHOVK2UhEtmstcaJBfLE6pM7x01lKTClGCdzqmDgK57qx6o/rDVXhMAU3vuq27miw/uD2yT37ymXEw9ikUzxwa8kHRn7XJuDZeyHPG2YrevLubHgfqxhQ11BpkoY/RTYl4sfqLDVU7TE674mcdr2eIS5Y6HaPTedKkk6xd48tM+W8UQQJ5YPrewxJlQsmP5nGffhBBiL/LlCLu4bOGGx7bdTnJ/1gmvWHBGPasTPy5WVgl3itXy5rB5z/fr2ISpU2a1lfD3x2hibt63scRnbW2sJSZ5fP/3+8TKOW+7ft5bLlSOSpO+V8VsC+BqjW6Y4H0cRiQUXi9QXF8QUK0kA21k4f7HaDhIz9nlgGacs44KTa8rqRQLEqIzeXNrfetFLTkEFrHehydK+7I0FiPMfFa6KrY+fqjH/yamxL8km7+fYNx6bZJb3/VOn2/RBbdPxCIwHyWQLF1bk/2xJkjSLkxcn0B9Nv1+NOImTDJwUU2i9KezHlvFz0Von9UBCVX/G2KPLWP2skSzxWW4ZiQPVPKpWVNJyQhiIsz3WgPF68ue1sQ+xXgWM5+ldVDD3VVTH0RuL+Ny0fHxMeeYY++a+qCuRF8r4DRs9m4xHoCqXK92B13G1/q1JknRibyz9RGQJPnh4WwnLcUTVqDV1uQtUnvKif5CY9BLW49p0LHrqdW27RqUxX4EbuCCCKqgkSToBpi83qXpwEiZx2yfWdPWmELftxqHdloOTo3JllWsTm45FC/2Up053hWlbplBbqLz1po4lSdIanETvyMFjIGHpVVV24btlXD8VbZdJAMeWrzCu1VdVbsOmY1Hjs+rqfvr66uatI1HrrcNkXWB8y4UkSTohFqC/OwePgcTmGzl4Dnyt9CtorPeKj7vYpk3H4lA+mAMTvi7sJTkoSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZKuRv8DIZNUUBhawsgAAAAASUVORK5CYII=>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAaCAYAAACO5M0mAAAAlklEQVR4XmNgGHqgAIgfYcGqyIqQQTQQ/wdiJXQJZMALxIcZIArxAj8GiKLn6BLoYA8DRGErugQ6AJkEUuiJLoEOQIpAmBtdAhnIMCAU4gVVDBBFIF/jBVsZIAonoUugg99A/AmI9dElkAELA8S0+UDMiCYHBpxAPAuInzJAFN4B4rlAnIysCATUGBA+RcYNSGpGAZUAAISlJVYbIUzwAAAAAElFTkSuQmCC>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGIAAAAZCAYAAADKQPsMAAADLklEQVR4Xu2Yz6tNURTHlzBQfqSEV+rFgBgwECJFMlEYmPqRTJShCcVA5B+QpBfd3kAiUykZ3BFiYCQDJhRKIYpCfqyvddZ9+3zv3ufue9/tKu1Pre49a61zzj5r7b32D5FCoVAoFPI4qPJK5Xclb6rrHaGTcqrSfxfzwy+uz4ZOxDGpP/tddR3qVna8Rw++0dsB4W/uxRyVkyp72KBsVfmhcl5lTGVc5bLKvdApBhryhZXEXJW2mO+MuinJLDH/K2xQLorZFrBhBOxV+Ua6jyoHSBfDE/ez+o0lArowyZBHNY8EcHzMSmKFylsx31yWiPnvZ4NyQsyG3jNqHqpcJx1673PSxbikslFlUvIT8UBlZs0jAgKcClYIGpqTsJDjYvcsZINyS4aTCIzOTWLP2ka2FLEArq/0GMU55CSiLzzAsWCF+GjolbCQp5JuEPQY3oMyW+Wlyl2VtWRrYpnYuxH4ENRy6NeRPkVTIvDsXqW+i9xyA5+chIXAn0cQAvhJ5Rnpc5mv8lWlxYZMMAKbEhELbIycRLwQm6BfV/8biQWL8fKVkzBnkZg/euyEWF3+UOmWBn65IFAYQafZ0CdeNlKJwNyVQ04iwkUNOl6y8w1rfjjDCuWo2D3zSO+rpVzuiPkfYcOA7JLmRMQCG6MpETF8cRKtKFjGwdirLt4W84stQwHmAsYnY+awmB7L4Rzg+1mspA0Dn5T/VSJWswG0xYy99gXwwVDjxoN9KptZKbahec9KmUpqbiKcq2JzA+aI6eAlcwPp0RmhR5XIwRMRK2XQQxYHOk9ELIadADeBgMGvJd0JwzVsjG/kLrBB+SXxe3LBHIG5Aj14UPB+LsdeskLwfakO028iEAvosCOv4QG+xgbCyxdnclWlRw9ndorZYiXPGwlQbnhjlcshseegHf1yTro3b9j53gyu/ZgC78AoYhC3VCLw7Bbp0HmwcOkwLlPBCIWPGnh3mJLlfoOyPWLnowQPIOYQNI5HWb9sEdu5PpGM3WsAlpU41rghdg52v27+2y6cl2HpGYIKgvb7uZmfnbUDH9y7u9K7PUzyf88aVhQKhUKhUCgUCoVp8wcv4wItPHqLYgAAAABJRU5ErkJggg==>

[image12]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGIAAAAZCAYAAADKQPsMAAADTUlEQVR4Xu2Yz6tNURTHl1DKr5RCKTGgKJIkIpKJAQMz+ZFMyNCAAQORf0BGL3oZSGRgIiWDN0IMjKT8GFAohSgK+bG+d+11777fu885+953uxP7U6v3zlrr7rPPWnuv/UOkUCgUCoU8Dqi8Ufkb5F143h47KaeC/qeYH/7i+WzsRByT7rY/hOdYt7ztPXrwjd4PCH9zLltUvrEy8EA67e8lWxI4VjXmzFKZEPOd0m2qZJqY/yU2KBfFbHPZMAJ2q/wg3WeV/aRrAnFIxW6t9Lb3XOVc9JwEjT1mJbFM5b2Yby4LxPz3sUE5KWbbzIYR8FDlGunOq7wgXROYDalEoG0eZIgB+3WBAFcFKwYdzUlYzHGx38xjg3JThpMIjMoNYm1tJVsV8N1FunVBj1mcA0b3K5XX0htgtMMDdlHQpWLRwgNc6RDw2dCUsJin0tshB/rfrOyD6WJBuKuymmx1LBZ7NwIf44FaQ/oUGOk3pNOHOBGzJZ0IlHbodpK+TW658cabEhYDf55B6PwXlWekz2WOyneVcTZkghlYlwieKSm+Rv9zIrzCcEw9ESjJSVLBYqoar2O+mD9G7JhYXf4UdAsjv1wQKMyg02zoEwS6LhGVgQqcUFkVPXMivMRxrDwRV0jfYljrwxlWKEfEfoOpGuO7pVzuiPkfZsOAoDTUJaJuRiCYGFgxnAiUtrpEJBONbRyMTXXxtphfahsKsBYwvhgzh8T06FgO8EUpQEkbBj5iB0nEUbGtaQwnwtvhb69NxISYselcAB+8jDsP9qhsZKXyS+UjK6WT1NxEOJfF1gasEZPBS+Z60vtIRpWoAjHwIKcESZwRPcf4Vj65S/QA1+GZHJfehPmBhvGD3AU2KH8k/ZtcsEZgrcDIGxS8n8uxl6wYfF/TgEH8OIapb/REI1FdeICvsoHw8sWzYUXQY4QzO8RsqZIHvXcS5YYPVrkcFGsH/egXnAH48PZIbEvqYORiVuMdmEVVpBKBEzXHDG3jHW2WSCcYsfBVg+8ummSp/0DZlrDzVYIHEGsIRjbPsn7ZJHan80RlKtnquCd2DXFd7B7sfre51S/cl70lvePfF9+fxevLzKC7pfIyyH/DSlYUCoVCoVAoFAqFSfMP/RwMLFFZNo8AAAAASUVORK5CYII=>

[image13]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFUAAAAZCAYAAABAb2JNAAADBElEQVR4Xu2YTahNURTHl6QIr0QkigyIgY9koBiQmXyUgYGUUhjIzEdMlIxQEhMpyUwyk5LBjaK8gYkoJZGPIpSikFj/t/a6d5119r7nnHvPm2j/6t89e6217917nX32XucSZTKZTGa8WM96w/ob9Da0VWr/ph0cx1hbvLEPk72hJS6w/pCMFZ8jRXdfHlFvns+dT1lGvRgI7UoQ+N0bAxtYD0wbSbQ/0CSpE0kGjolMcL5Bucu6wZoU2vjEuGZ2I9Igbodp4/qnaQPk5Yppn6RyvygIGvXGwBzWbdNeydpLsuqaJhUgsU+CcD0sGMNaZ/vAOupsnlUkfacYG65hm2bar1iLuxHiQ0xqVY+xiCRol3cEZlF6gIMkVcFKvcP6SMWJNWEpFZOgXGP9djbPS5K+HthOh+s1oQ0hD8rnYEuCL0DADGPDJLFPgdkkg48xTFItl1i/WGe8o4LjFJ8cFkHMbsFjHYuB7XW4xo3HHv2u5x4DZ0+sbxc8Kj7gPmuFs8VoK6kKDpgfrKvekeAmlccONKl+BVti8wawpc4XBTGfvNGCgJjq0HZSwRKS793pHRE6FB+rJnWudxgOkMTYAxNPa9X8z5P49WAskdpPq+6U0lZScWBpabPN+fpxj+IJqLNSwQvWddN+RtIvNX/dw6d6h2UrSdBqZ09VAp42kqpl1mPWRuerAgfSMEldSBLXYT1lHQxt7JkxcBPOeqOnQ/FB1QV9U5VBFTgMcfLf8o4G7CcZg695UVcOOi/009Pfcpm1x7T3mesC+ILU21IdBkmqHkZNT/oYKHMwBlu5AGwLKHssqKttXTyfpO8CY5sXbLbEww07wtpsbAAHXYnpJF9g3xaagB9rmtQTJC8ObfKeymPAuPAKrmiVYFfvutC2Lw5fWadMG+jrr1fhpmGT9QGQ1qVVYP9FPCZj/yPoUPUeNh7g5qLGxRjwiOLzUCFCVuVD1kVnR1n0JQj9DhfdtCnYY8LTkPlfWU6ymupoe+iTqWA3Ff9a7KdzoU8mk8lkMplh+AfoMuZ88f8RHwAAAABJRU5ErkJggg==>

[image14]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADcAAAAXCAYAAACvd9dwAAACRUlEQVR4Xu2Wv0tWURjHv1ENkWQgDRIiQeYfkBStGRFIi1NDu0SBQ0O2FU2SS0FLBOHkUARuKQ1tiQ4thRE6FIggiBTkIPTj+b7Pvb7nfjvnvfd9pQa5H/jCPc9zz4/n/HjOAWpqavYbx03nTAfUUcJh00lTvzoyTqjBOIhIPwOmL6Yj6tgDt00/TNfhnX41TRX+SLNkmoAHRu2YRgt/AL8j2ir8ITyEN9Srjjbphnd2SOy09YlNuWK6pUZ43XBVNLCRwNeScXiFQXVU5DG8vsKVfKlGYdr0QI3GtqkrKLP9q0G5La7BG3iHyD4ugduKg1E2TatqFBjcT/zdp64cJ6rj4HJ4Xt6blrPvKrBjSuG5/qVG4TSaW+0bvM85+BkOyYO7ZHptulx0twdnbda0po4IHFgquNh2VS6ieJ7uFbwO26cvT4JPUZJQUhyFz+JzdSTYa3Dc1nfhSSIPkNk2ZBg+rhxOfmoiojyB7/9JdZTQaluWBTcPDyxkBV6PeaAV/IfnuiWvTBvo/N77iHhC+W5aV6PAAWoyIYumt9k3zx//+7DrdVI7ptEgMyOTR9XEkWIM8RWijddESI+UU8HdMT3LvplRU8ExuRRgYwyqk7Qf4xTSwV0Iynxi0XYjsLHM+soM/IInnLybpmNNd+MOZF2+iP45b0wv4K8Vwln/3HQ3OAsf0EJgG8psYYB8imld5gJmb8KdxkzJRPTfOG96ZPoED6QqHOx9eNDUmaJ7F64cJ5Eqe9btT3ioeY9UETNhTU1NZ/wBzPKT9TDLrBgAAAAASUVORK5CYII=>

[image15]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAYCAYAAAAlBadpAAAAu0lEQVR4XmNgGAUjEagB8X8gfgSl56NK4wY8DBANMPAejY8XRDNAFDND+aeBeBpCGj9QZIBohuEsIGZEUcHA8BCII9DE4OAjA0LzXyD2Q5VmKARiVjQxBj4gbkXiuzBADDiAJIYTvGVADRxY4MGcCOJ3M0BcgwFWAXEqlM0PxL+AWBMhzbAWiFmA+DeSGArgAOIAIJZEl4CCHCAuRxckFoBsBVkQjy5BDACFiwYQi6FLEANAgYYRTSMNAACJtCInd89R7QAAAABJRU5ErkJggg==>