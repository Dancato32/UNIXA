import re

# ── 20 new subjects to add ──────────────────────────────────────────────────

NEW_SUBJECTS = """
    ('accounting', 'Accounting'),
    ('business_studies', 'Business Studies'),
    ('statistics', 'Statistics'),
    ('further_maths', 'Further Mathematics'),
    ('civic_education', 'Civic Education'),
    ('religious_studies', 'Religious Studies'),
    ('french', 'French Language'),
    ('spanish', 'Spanish Language'),
    ('arabic', 'Arabic Language'),
    ('health_science', 'Health Science'),
    ('physical_education', 'Physical Education'),
    ('agriculture', 'Agriculture'),
    ('food_nutrition', 'Food & Nutrition'),
    ('ict', 'ICT & Digital Literacy'),
    ('psychology', 'Psychology'),
    ('sociology', 'Sociology'),
    ('philosophy', 'Philosophy'),
    ('law', 'Law & Legal Studies'),
    ('environmental_science', 'Environmental Science'),
    ('astronomy', 'Astronomy & Space Science'),
"""

NEW_META = """
    'accounting':          {'icon': '💰', 'color': '#10b981', 'desc': 'Financial Statements, Bookkeeping & Auditing'},
    'business_studies':    {'icon': '💼', 'color': '#f59e0b', 'desc': 'Management, Marketing, Entrepreneurship'},
    'statistics':          {'icon': '📊', 'color': '#3b82f6', 'desc': 'Data Analysis, Probability & Inference'},
    'further_maths':       {'icon': '∞',  'color': '#8b5cf6', 'desc': 'Complex Numbers, Calculus & Advanced Algebra'},
    'civic_education':     {'icon': '🏛', 'color': '#ef4444', 'desc': 'Government, Rights, Democracy & Citizenship'},
    'religious_studies':   {'icon': '✝', 'color': '#f97316', 'desc': 'World Religions, Ethics & Sacred Texts'},
    'french':              {'icon': '🇫🇷', 'color': '#06b6d4', 'desc': 'Grammar, Vocabulary, Reading & Speaking'},
    'spanish':             {'icon': '🇪🇸', 'color': '#ec4899', 'desc': 'Grammar, Vocabulary, Reading & Speaking'},
    'arabic':              {'icon': '🌙', 'color': '#a855f7', 'desc': 'Script, Grammar, Vocabulary & Quran Studies'},
    'health_science':      {'icon': '🏥', 'color': '#14b8a6', 'desc': 'Human Health, Disease, First Aid & Wellness'},
    'physical_education':  {'icon': '⚽', 'color': '#22c55e', 'desc': 'Sports, Fitness, Anatomy & Health'},
    'agriculture':         {'icon': '🌾', 'color': '#84cc16', 'desc': 'Crop Science, Animal Husbandry & Agribusiness'},
    'food_nutrition':      {'icon': '🍎', 'color': '#f43f5e', 'desc': 'Nutrients, Cooking, Diet & Food Safety'},
    'ict':                 {'icon': '💻', 'color': '#0ea5e9', 'desc': 'Hardware, Software, Internet & Digital Skills'},
    'psychology':          {'icon': '🧠', 'color': '#d946ef', 'desc': 'Mind, Behaviour, Development & Mental Health'},
    'sociology':           {'icon': '👥', 'color': '#fb923c', 'desc': 'Society, Culture, Institutions & Social Change'},
    'philosophy':          {'icon': '🤔', 'color': '#64748b', 'desc': 'Logic, Ethics, Metaphysics & Critical Thinking'},
    'law':                 {'icon': '⚖', 'color': '#dc2626', 'desc': 'Constitutional, Criminal, Contract & Human Rights Law'},
    'environmental_science':{'icon': '🌿', 'color': '#16a34a', 'desc': 'Ecosystems, Pollution, Climate & Sustainability'},
    'astronomy':           {'icon': '🔭', 'color': '#7c3aed', 'desc': 'Solar System, Stars, Galaxies & Space Exploration'},
"""

NEW_LEVELS = {
    'accounting': {
        'Primary (Basic 1-6)': [
            'What is Money?', 'Saving & Spending', 'Simple Budgets',
            'Buying & Selling Basics', 'Receipts & Bills',
        ],
        'JHS (Basic 7-9)': [
            'Introduction to Accounting', 'Source Documents', 'Double Entry Bookkeeping',
            'Cash Book', 'Petty Cash Book', 'Trial Balance',
            'Trading Account', 'Profit & Loss Account', 'Balance Sheet',
            'Bank Reconciliation',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Accounting Concepts & Conventions', 'Ledger Accounts', 'Journal Entries',
            'Control Accounts', 'Depreciation Methods', 'Accruals & Prepayments',
            'Partnership Accounts', 'Company Accounts', 'Manufacturing Accounts',
            'Incomplete Records', 'Ratio Analysis', 'Cash Flow Statements',
            'Budgeting & Variance Analysis', 'Inventory Valuation', 'VAT & Taxation Basics',
        ],
        'University / Advanced': [
            'Financial Reporting Standards (IFRS)', 'Auditing Principles',
            'Cost Accounting', 'Management Accounting', 'Activity-Based Costing',
            'Capital Budgeting', 'Working Capital Management', 'Financial Statement Analysis',
            'Corporate Governance', 'Forensic Accounting',
        ],
    },
    'business_studies': {
        'Primary (Basic 1-6)': [
            'What is a Business?', 'Needs & Wants', 'Buying & Selling',
            'Jobs in the Community', 'Simple Advertising',
        ],
        'JHS (Basic 7-9)': [
            'Types of Business Organisations', 'Business Ownership', 'Production & Distribution',
            'Marketing Basics', 'Consumer Rights', 'Communication in Business',
            'Banking & Finance Basics', 'Insurance Basics', 'Transport & Trade',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Business Environment', 'Sole Trader & Partnership', 'Limited Companies',
            'Cooperatives & NGOs', 'Management Functions', 'Human Resource Management',
            'Marketing Mix - 4Ps', 'Market Research', 'Pricing Strategies',
            'Business Finance & Capital', 'Stock Exchange', 'International Trade',
            'Entrepreneurship & Innovation', 'Business Ethics', 'E-Commerce',
        ],
        'University / Advanced': [
            'Strategic Management', 'Operations Management', 'Supply Chain Management',
            'Corporate Finance', 'Business Law', 'Organisational Behaviour',
            'Leadership & Motivation Theories', 'Change Management',
            'Business Analytics', 'Global Business Strategy',
        ],
    },
    'statistics': {
        'Primary (Basic 1-6)': [
            'Counting & Tallying', 'Bar Charts & Pictograms', 'Reading Tables',
            'Simple Averages', 'Sorting & Classifying Data',
        ],
        'JHS (Basic 7-9)': [
            'Data Collection Methods', 'Frequency Tables', 'Mean, Median & Mode',
            'Range & Spread', 'Pie Charts', 'Line Graphs', 'Scatter Plots',
            'Basic Probability', 'Sampling Basics',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Measures of Central Tendency', 'Measures of Dispersion', 'Variance & Standard Deviation',
            'Probability Rules', 'Permutations & Combinations', 'Binomial Distribution',
            'Normal Distribution', 'Confidence Intervals', 'Hypothesis Testing',
            'Chi-Square Test', 'Correlation & Regression', 'Time Series Analysis',
            'Index Numbers', 'Sampling Techniques', 'Statistical Inference',
        ],
        'University / Advanced': [
            'Bayesian Statistics', 'Multivariate Analysis', 'ANOVA',
            'Non-Parametric Tests', 'Survival Analysis', 'Stochastic Processes',
            'Statistical Computing with R/Python', 'Machine Learning Statistics',
            'Experimental Design', 'Biostatistics',
        ],
    },
    'further_maths': {
        'Primary (Basic 1-6)': [
            'Advanced Counting Patterns', 'Introduction to Negative Numbers',
            'Basic Algebra Puzzles', 'Geometry Challenges',
        ],
        'JHS (Basic 7-9)': [
            'Surds & Indices', 'Quadratic Equations', 'Simultaneous Equations',
            'Functions & Graphs', 'Trigonometry Basics', 'Vectors Introduction',
            'Matrices Introduction', 'Sequences & Series',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Complex Numbers', 'Polynomial Division', 'Partial Fractions',
            'Binomial Theorem', 'Proof by Induction', 'Differential Calculus',
            'Integral Calculus', 'Differential Equations', 'Vectors in 3D',
            'Matrices & Transformations', 'Linear Programming', 'Conic Sections',
            'Hyperbolic Functions', 'Numerical Methods', 'Probability Distributions',
        ],
        'University / Advanced': [
            'Real Analysis', 'Complex Analysis', 'Abstract Algebra',
            'Linear Algebra', 'Topology Intro', 'Fourier Series',
            'Laplace Transforms', 'Partial Differential Equations',
            'Multivariable Calculus', 'Number Theory',
        ],
    },
    'civic_education': {
        'Primary (Basic 1-6)': [
            'My Family & Community', 'Rules & Why We Need Them',
            'Being a Good Citizen', 'Our Country & Its Flag',
            'Leaders in Our Community',
        ],
        'JHS (Basic 7-9)': [
            'Democracy & Governance', 'Human Rights & Responsibilities',
            'The Constitution', 'Branches of Government', 'Elections & Voting',
            'Rule of Law', 'Citizenship & National Identity',
            'Community Development', 'Conflict Resolution',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Constitutional Democracy', 'The Legislature', 'The Executive',
            'The Judiciary', 'Political Parties & Elections', 'Civil Society & NGOs',
            'Fundamental Human Rights', 'Gender Equality & Social Justice',
            'Corruption & Anti-Corruption', 'National Security',
            'International Relations & Diplomacy', 'African Union & ECOWAS',
            'Environmental Citizenship', 'Media & Democracy', 'Civic Participation',
        ],
        'University / Advanced': [
            'Political Theory', 'Comparative Government', 'Public Administration',
            'International Law', 'Human Rights Law', 'Electoral Systems',
            'Federalism & Decentralisation', 'Civil Society & Democracy',
            'Political Economy', 'Global Governance',
        ],
    },
    'religious_studies': {
        'Primary (Basic 1-6)': [
            'Stories from the Bible', 'Stories from the Quran',
            'Prayer & Worship', 'Festivals & Celebrations',
            'Being Kind & Honest', 'Creation Stories',
        ],
        'JHS (Basic 7-9)': [
            'Christianity - Core Beliefs', 'Islam - Core Beliefs',
            'African Traditional Religion', 'The Bible - Old Testament',
            'The Bible - New Testament', 'The Quran & Hadith',
            'Prayer & Worship Practices', 'Religious Festivals',
            'Moral Values in Religion',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'World Religions Overview', 'Christianity - History & Denominations',
            'Islam - History & Pillars', 'Hinduism & Buddhism',
            'African Traditional Religion in Depth', 'Sacred Texts Comparison',
            'Religion & Ethics', 'Religion & Society',
            'Religion & Politics', 'Interfaith Dialogue',
            'Religion & Science', 'Death, Afterlife & Eschatology',
            'Religious Art & Architecture', 'Mysticism & Spirituality',
            'New Religious Movements',
        ],
        'University / Advanced': [
            'Theology & Philosophy of Religion', 'Comparative Religion',
            'Religious Ethics', 'Sociology of Religion',
            'Psychology of Religion', 'Liberation Theology',
            'Feminist Theology', 'Religion & Globalisation',
            'Secularism & Post-Secularism', 'Religious Extremism & Radicalisation',
        ],
    },
    'french': {
        'Primary (Basic 1-6)': [
            'Alphabet & Pronunciation', 'Numbers 1-100', 'Colours & Shapes',
            'Greetings & Introductions', 'Family Members', 'Days & Months',
            'Simple Sentences - Je suis, Je veux', 'Animals & Food',
        ],
        'JHS (Basic 7-9)': [
            'Present Tense - Regular Verbs', 'Present Tense - Irregular Verbs',
            'Articles - le, la, les, un, une', 'Adjectives & Agreement',
            'Asking Questions', 'Negation - ne...pas', 'School & Daily Routine',
            'Food & Shopping Vocabulary', 'Past Tense - Passe Compose',
            'Future Tense Basics',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Imperfect Tense', 'Future Tense', 'Conditional Tense',
            'Subjunctive Mood', 'Reflexive Verbs', 'Pronouns - Direct & Indirect',
            'Relative Pronouns', 'Prepositions & Conjunctions',
            'Reading Comprehension', 'Essay Writing in French',
            'Letter Writing in French', 'Oral Expression & Conversation',
            'French Culture & Francophone Countries', 'Vocabulary - Health & Environment',
            'Vocabulary - Work & Technology',
        ],
        'University / Advanced': [
            'Advanced Grammar & Syntax', 'French Literature - Classic Texts',
            'French Cinema & Media', 'Translation & Interpretation',
            'Business French', 'French Linguistics',
            'Francophone African Literature', 'Advanced Oral Communication',
            'Academic Writing in French', 'French Phonetics',
        ],
    },
    'spanish': {
        'Primary (Basic 1-6)': [
            'Alphabet & Pronunciation', 'Numbers & Counting', 'Colours & Shapes',
            'Greetings - Hola, Buenos dias', 'Family - la familia',
            'Days, Months & Seasons', 'Simple Sentences - Soy, Tengo',
        ],
        'JHS (Basic 7-9)': [
            'Present Tense - Regular Verbs', 'Ser vs Estar', 'Articles & Gender',
            'Adjectives & Agreement', 'Asking Questions', 'Negation',
            'School & Daily Life Vocabulary', 'Food & Shopping',
            'Past Tense - Preterite', 'Future Tense Basics',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Imperfect Tense', 'Future & Conditional', 'Subjunctive Mood',
            'Reflexive Verbs', 'Direct & Indirect Object Pronouns',
            'Relative Clauses', 'Reading Comprehension',
            'Essay Writing in Spanish', 'Letter Writing',
            'Oral Expression', 'Spanish Culture & Latin America',
            'Vocabulary - Health & Environment', 'Vocabulary - Work & Technology',
            'Por vs Para', 'Passive Voice',
        ],
        'University / Advanced': [
            'Advanced Grammar', 'Spanish Literature', 'Translation',
            'Business Spanish', 'Spanish Linguistics',
            'Latin American Literature', 'Advanced Oral Communication',
            'Academic Writing in Spanish', 'Spanish Phonetics', 'Media Spanish',
        ],
    },
    'arabic': {
        'Primary (Basic 1-6)': [
            'Arabic Alphabet - Letters & Sounds', 'Short Vowels - Harakat',
            'Joining Letters', 'Numbers in Arabic', 'Simple Greetings',
            'Basic Quran Recitation', 'Common Words & Phrases',
        ],
        'JHS (Basic 7-9)': [
            'Reading & Writing Arabic Script', 'Nouns & Gender',
            'Definite & Indefinite Articles', 'Simple Sentences',
            'Basic Verb Conjugation', 'Quran Vocabulary',
            'Islamic Phrases & Duas', 'Days, Months & Numbers',
            'Family & Daily Life Vocabulary',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Verb Patterns - Awzan', 'Tenses - Past, Present & Future',
            'Pronouns & Possessives', 'Adjectives & Agreement',
            'Prepositions & Conjunctions', 'Reading Comprehension',
            'Essay Writing in Arabic', 'Quranic Arabic - Surah Analysis',
            'Islamic History in Arabic', 'Arabic Literature Basics',
            'Oral Communication', 'Vocabu