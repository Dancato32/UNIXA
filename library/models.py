from django.db import models

SUBJECTS = [
    ('mathematics', 'Mathematics'),
    ('physics', 'Physics'),
    ('chemistry', 'Chemistry'),
    ('biology', 'Biology'),
    ('economics', 'Economics'),
    ('world_history', 'World History'),
    ('english', 'English Language'),
    ('literature', 'Literature'),
    ('art_design', 'Art & Design'),
    ('music_theory', 'Music Theory'),
    ('programming', 'Programming'),
    ('geography', 'Geography'),
]

# Levelled curriculum: subject -> {level_name: [topics]}
SUBJECT_LEVELS = {
    'mathematics': {
        'Primary (Basic 1-6)': [
            'Counting & Number Recognition', 'Addition & Subtraction',
            'Multiplication & Division', 'Fractions - Halves, Quarters & Thirds',
            'Place Value & Number Ordering', 'Basic Shapes & Geometry',
            'Measurement - Length, Mass & Capacity', 'Time - Reading Clocks & Calendars',
            'Money & Simple Transactions', 'Patterns & Sequences',
            'Introduction to Data & Graphs',
        ],
        'JHS (Basic 7-9)': [
            'Number & Numeration', 'Number Bases & Conversions', 'Directed Numbers',
            'Fractions, Decimals & Percentages', 'Ratio & Proportion',
            'Algebraic Expressions', 'Linear Equations & Inequalities', 'Simultaneous Equations',
            'Sets & Logic', 'Coordinate Geometry', 'Angles & Triangles',
            'Circle Theorems', 'Mensuration', 'Statistics & Probability',
            'Commercial Arithmetic',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Indices & Logarithms', 'Quadratic Equations', 'Sequences & Series',
            'Trigonometry', 'Vectors & Matrices', 'Surds & Radicals',
            'Polynomial Functions', 'Binomial Theorem', 'Permutations & Combinations',
            'Linear Programming', 'Bearing & Navigation', 'Loci & Transformations',
            'Geometric Constructions', 'Probability Distributions', 'Regression & Correlation',
            'Financial Mathematics - Interest & Annuities', 'Modular Arithmetic',
            'Inequalities & Absolute Values', 'Functions & Mappings',
            'Exponential & Logarithmic Functions',
        ],
        'University / Advanced': [
            'Complex Numbers', 'Calculus (Differentiation)', 'Calculus (Integration)',
            'Differential Equations (Intro)', 'Numerical Methods', 'Matrices & Determinants',
            'Graph Theory Basics', 'Rational Functions & Partial Fractions',
            'Hypothesis Testing', 'Linear Algebra', 'Multivariable Calculus',
            'Real Analysis Intro', 'Abstract Algebra Intro', 'Discrete Mathematics',
            'Mathematical Proof Techniques',
        ],
    },
    'physics': {
        'Primary (Basic 1-6)': [
            'Push & Pull Forces', 'Floating & Sinking', 'Light & Shadow',
            'Sound - Loud & Soft', 'Hot & Cold - Temperature Basics',
            'Simple Machines in Daily Life', 'Magnets & Magnetism',
            'Electricity - Batteries & Bulbs', 'The Solar System', 'States of Matter Basics',
        ],
        'JHS (Basic 7-9)': [
            'Measurements & Units', 'Scalars & Vectors', 'Motion (Kinematics)',
            'Pressure & Fluids', 'Heat & Thermodynamics', 'Waves & Sound',
            'Light & Optics', 'Electricity & Magnetism', 'Simple Machines',
            'Atomic Structure Basics', 'Environmental Physics',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            "Newton's Laws of Motion", 'Work, Energy & Power', 'Electromagnetism',
            'Atomic & Nuclear Physics', 'Electronics', 'Projectile Motion',
            'Circular Motion & Centripetal Force', 'Gravitational Fields',
            'Momentum & Impulse', 'Oscillations & Simple Harmonic Motion',
            'Resonance & Standing Waves', 'Electromagnetic Spectrum',
            'Photoelectric Effect', 'Radioactive Decay & Half-Life',
            'Electric Fields & Potential', 'Capacitors & Capacitance',
            'Semiconductors & Diodes', 'Gas Laws', 'Thermal Expansion',
            'Diffraction & Interference',
        ],
        'University / Advanced': [
            'Rotational Motion & Torque', 'Nuclear Fission & Fusion',
            'Magnetic Force on Conductors', 'Transformers & Power Transmission',
            'Logic Gates & Digital Electronics', 'Optical Instruments',
            'Kinetic Theory of Gases', "Bernoulli's Principle",
            'Surface Tension & Viscosity', 'Special Relativity (Intro)',
            'Quantum Mechanics Intro', 'Thermodynamics Laws',
            'Electrostatics & Gauss Law', 'Electromagnetic Waves',
            'Particle Physics Intro',
        ],
    },
    'chemistry': {
        'Primary (Basic 1-6)': [
            'Materials Around Us', 'Solids, Liquids & Gases', 'Mixing & Separating Materials',
            'Changes - Melting, Freezing & Evaporation', 'Everyday Chemical Changes',
            'Water & Its Uses', 'Air & Its Properties', 'Rocks & Soils',
        ],
        'JHS (Basic 7-9)': [
            'Atomic Structure', 'Periodic Table', 'Chemical Bonding',
            'States of Matter', 'Acids, Bases & Salts', 'Metals & Non-Metals',
            'Stoichiometry & Mole Concept', 'Environmental Chemistry',
            'Water Treatment & Purification', 'Separation Techniques',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Redox Reactions', 'Electrochemistry', 'Organic Chemistry - Hydrocarbons',
            'Organic Chemistry - Functional Groups', 'Rates of Reaction', 'Equilibrium',
            'Isotopes & Radioactivity', 'Electron Configuration & Orbitals',
            'Intermolecular Forces', 'Thermochemistry & Enthalpy',
            'Titration & Volumetric Analysis', 'Qualitative Analysis',
            'Polymers & Plastics', 'Alcohols, Aldehydes & Ketones',
            'Carboxylic Acids & Esters', 'Industrial Chemistry - Haber & Contact Process',
            'Corrosion & Rust Prevention', 'Alloys & Their Properties',
            'Chromatography', 'Colligative Properties of Solutions',
        ],
        'University / Advanced': [
            'Entropy & Gibbs Free Energy', "Chemical Equilibrium - Le Chatelier's Principle",
            'Buffer Solutions & pH', 'Amines & Amides', 'Carbohydrates & Biochemistry',
            'Fats, Oils & Soaps', 'Nuclear Chemistry', 'Green Chemistry & Sustainability',
            'Spectroscopy Basics', 'Coordination Compounds',
            'Quantum Chemistry Intro', 'Reaction Mechanisms', 'Stereochemistry',
            'Electroanalytical Chemistry', 'Computational Chemistry Intro',
        ],
    },
    'biology': {
        'Primary (Basic 1-6)': [
            'Living & Non-Living Things', 'Plants - Parts & Functions',
            'Animals & Their Habitats', 'The Human Body - Basic Parts',
            'Food & Nutrition Basics', 'Health & Hygiene',
            'Life Cycles - Plants & Animals', 'Our Senses',
            'The Environment & Taking Care of It',
        ],
        'JHS (Basic 7-9)': [
            'Cell Structure & Function', 'Nutrition in Plants', 'Nutrition in Animals',
            'Respiration', 'Excretion', 'Transport in Plants', 'Transport in Animals',
            'Reproduction', 'Ecology', 'Diseases & Immunity',
            'Classification of Living Things',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Cell Division', 'Genetics & Heredity', 'Evolution & Natural Selection',
            'Hormones & Coordination', 'Enzymes & Metabolism', 'Photosynthesis in Depth',
            'Aerobic vs Anaerobic Respiration', 'DNA Structure & Replication',
            'Gene Mutations & Genetic Disorders', 'Viruses, Bacteria & Fungi',
            'Plant Hormones & Tropisms', 'Nervous System & Reflex Actions',
            'Sense Organs', 'Homeostasis', 'Osmoregulation & Kidney Function',
            'Blood Groups & Transfusion', 'Sexually Transmitted Infections',
            'Population Dynamics', 'Food Chains, Webs & Energy Flow',
            'Nutrient Cycles - Carbon, Nitrogen & Water',
        ],
        'University / Advanced': [
            'Protein Synthesis - Transcription & Translation',
            'Biotechnology & Genetic Engineering', 'Lymphatic System',
            'Biodiversity & Conservation', 'Adaptation & Natural Habitats',
            'Human Impact on the Environment', 'Stem Cells & Cloning',
            'Bioinformatics & Genomics', 'Immunology in Depth',
            'Developmental Biology', 'Neuroscience Intro',
            'Molecular Biology Techniques', 'Ecology & Ecosystem Modelling',
            'Evolutionary Genetics', 'Synthetic Biology',
        ],
    },
    'economics': {
        'Primary (Basic 1-6)': [
            'Needs & Wants', 'Goods & Services', 'Buying & Selling',
            'Saving Money', 'Jobs & Occupations', 'Community Resources',
        ],
        'JHS (Basic 7-9)': [
            'Introduction to Economics', 'Scarcity, Choice & Opportunity Cost',
            'Demand & Supply', 'Money & Banking', 'Agriculture & Industry',
            'Population & Labour', 'Economic Development',
            'Production Possibility Curve', 'Price Controls - Floors & Ceilings',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Elasticity', 'Market Structures', 'National Income',
            'Inflation & Unemployment', 'International Trade', 'Public Finance',
            'Consumer Theory & Utility', 'Theory of the Firm - Costs & Revenue',
            'Profit Maximisation', 'Monopoly & Monopolistic Competition',
            'Factor Markets - Land, Labour & Capital', 'Wage Determination & Trade Unions',
            'Fiscal Policy', 'Monetary Policy', 'Exchange Rates & Balance of Payments',
            'Economic Integration & Trade Blocs', 'Poverty & Income Inequality',
            'Subsidies & Taxation Effects', 'Economic History of West Africa',
            'Cost-Benefit Analysis',
        ],
        'University / Advanced': [
            'Oligopoly & Game Theory', 'Globalisation & Multinational Corporations',
            'Development Economics - HDI & Indicators', 'Foreign Aid & Debt',
            'Environmental Economics', 'Behavioural Economics',
            'Stock Markets & Financial Instruments', 'Entrepreneurship & Business Finance',
            'Econometrics Intro', 'Macroeconomic Models', 'International Finance',
            'Labour Economics', 'Health Economics', 'Public Choice Theory',
            'Advanced Microeconomics',
        ],
    },
    'world_history': {
        'Primary (Basic 1-6)': [
            'My Family & Community History', 'Famous People in History',
            'How People Lived Long Ago', 'Inventions That Changed the World',
            'Our Country - A Brief History', 'Celebrations & Their Origins',
        ],
        'JHS (Basic 7-9)': [
            'Ancient Civilizations', 'Ancient Egypt & the Nile Civilizations',
            'Ancient Greece - Democracy & Philosophy', 'The Roman Empire',
            'The Middle Ages', 'The Islamic Golden Age',
            'The Age of Exploration', 'The Slave Trade & Abolition',
            'Colonialism & Imperialism', 'African History & Independence',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'The Renaissance', 'The Protestant Reformation', 'The Scientific Revolution',
            'The French Revolution', 'The American Revolution & Independence',
            'The Industrial Revolution', 'Nationalism & the Unification of Nations',
            'World War I', 'The Russian Revolution', 'The Great Depression',
            'World War II', 'The Cold War', 'Decolonisation in Asia & Africa',
            'The United Nations', 'Globalization',
            'The Civil Rights Movement', 'The Arab-Israeli Conflict',
        ],
        'University / Advanced': [
            'Prehistoric Humans & Early Societies', 'The Byzantine Empire',
            'The Mongol Empire', 'The Crusades',
            'The Rise of China', 'Terrorism & the Post-9/11 World',
            'Climate Change as a Historical Force', 'The Digital Revolution',
            'Human Rights & International Law', 'The African Union & Regional Integration',
            'Historiography & Historical Methods', 'Comparative History',
            'Post-Colonial Theory', 'Memory, Identity & History',
            'Global History & World Systems Theory',
        ],
    },
    'english': {
        'Primary (Basic 1-6)': [
            'Alphabet & Phonics', 'Sight Words & Vocabulary Building',
            'Reading Simple Sentences', 'Writing Sentences',
            'Nouns, Verbs & Adjectives', 'Punctuation - Full Stop & Comma',
            'Simple Story Writing', 'Listening & Speaking Skills',
            'Rhymes & Simple Poems',
        ],
        'JHS (Basic 7-9)': [
            'Comprehension', 'Summary Writing', 'Letter Writing',
            'Grammar - Parts of Speech', 'Grammar - Tenses & Concord',
            'Grammar - Sentence Structure', 'Vocabulary & Idioms',
            'Oral English & Phonetics', 'Punctuation & Spelling',
            'Figures of Speech', 'Report Writing',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Essay Writing - Narrative', 'Essay Writing - Argumentative',
            'Essay Writing - Expository', 'Descriptive Writing',
            'Persuasive Writing', 'Speech Writing & Delivery',
            'Minutes & Formal Meeting Records', 'Debate Writing & Structure',
            'Grammar - Clauses & Phrases', 'Grammar - Active & Passive Voice',
            'Grammar - Direct & Indirect Speech', 'Grammar - Conditionals',
            'Grammar - Prepositions & Conjunctions', 'Word Formation - Prefixes & Suffixes',
            'Synonyms, Antonyms & Homonyms', 'Proverbs & Their Meanings',
            'Register & Tone in Writing', 'Stress & Intonation Patterns',
            'Vowel & Consonant Sounds', 'Reading for Inference & Deduction',
        ],
        'University / Advanced': [
            'Critical Reading & Evaluation', 'Academic Essay Writing',
            'Research Writing & Citation', 'Editing & Proofreading Skills',
            'Note-Taking & Summarising from Audio', 'Syllabification & Word Stress',
            'Dialogue Writing', 'Creative Writing - Short Stories',
            'Newspaper & Magazine Articles', 'Digital Communication & Email Writing',
            'Discourse Analysis', 'Stylistics', 'Linguistics Intro',
            'Technical Writing', 'Grant & Proposal Writing',
        ],
    },
    'literature': {
        'Primary (Basic 1-6)': [
            'Nursery Rhymes & Simple Poems', 'Fairy Tales & Fables',
            'Picture Books & Storytelling', 'Simple Plays & Role Play',
            'Folk Tales from Africa', 'Heroes & Heroines in Stories',
        ],
        'JHS (Basic 7-9)': [
            'Introduction to Literature', 'Poetry - Analysis & Devices',
            'Prose - Narrative Techniques', 'Drama - Structure & Elements',
            'African Literature', 'Oral Literature & Folklore',
            'Themes & Characterization', 'Setting & Symbolism',
            'West African Oral Traditions',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Shakespeare', 'The Novel - History & Development',
            'Short Story - Form & Technique', 'Tragedy & Comedy in Drama',
            'Epic Poetry & Heroic Literature', 'Satire & Irony in Literature',
            'Postcolonial Literature', 'War Literature',
            'Chinua Achebe & Things Fall Apart', 'Wole Soyinka & Nigerian Drama',
            "Ngugi wa Thiong'o & African Identity", 'Caribbean Literature',
            'Feminist Literature & Gender Themes', 'The Bildungsroman',
            'Writing a Literary Essay',
        ],
        'University / Advanced': [
            'Dystopian Fiction', 'Magical Realism',
            'Stream of Consciousness Narrative', 'Intertextuality & Allusion',
            'Literary Criticism - Schools of Thought', 'American Literature - Key Movements',
            'Modernism & Postmodernism in Literature', 'Comparative Literature',
            'Literature & Society', "Children's Literature",
            'Narratology', 'Ecocriticism', 'Psychoanalytic Literary Theory',
            'Marxist Literary Criticism', 'Deconstructionism in Literature',
        ],
    },
    'art_design': {
        'Primary (Basic 1-6)': [
            'Drawing with Shapes', 'Colouring & Colour Mixing',
            'Making Patterns', 'Clay Modelling Basics',
            'Collage & Cut-Outs', 'Drawing Animals & People',
            'Printing with Objects', 'Art from Nature',
        ],
        'JHS (Basic 7-9)': [
            'Elements of Art', 'Principles of Design', 'Drawing & Sketching',
            'Colour Theory', 'Painting Techniques', 'Sculpture & 3D Art',
            'Art History', 'Photography Basics', 'African Traditional Art & Symbolism',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Graphic Design', 'Perspective Drawing - 1 & 2 Point',
            'Life Drawing & Figure Studies', 'Still Life Drawing',
            'Landscape Art', 'Portrait Art', 'Printmaking Techniques',
            'Textile & Fabric Design', 'Ceramics & Pottery',
            'Mixed Media Art', 'Typography & Lettering',
            'Logo Design & Branding', 'Poster Design',
            'Art Movements - Impressionism to Abstract',
            'Contemporary African Art', 'Art Critique & Appreciation',
        ],
        'University / Advanced': [
            'Digital Art & Illustration', 'Packaging Design',
            'UI & UX Design Basics', 'Animation Principles',
            'Film & Video Art', 'Street Art & Muralism',
            'Installation Art', 'Portfolio Development',
            'Art & Culture in Society', 'Curatorial Studies',
            'Art Theory & Philosophy', 'Sustainable Design',
            'Branding & Visual Identity', 'Motion Graphics',
            'Architectural Design Basics',
        ],
    },
    'music_theory': {
        'Primary (Basic 1-6)': [
            'Singing & Voice', 'Clapping Rhythms', 'High & Low Sounds',
            'Fast & Slow Music', 'Simple Percussion Instruments',
            'African Drumming Basics', 'Songs & Nursery Rhymes',
            'Listening & Describing Music',
        ],
        'JHS (Basic 7-9)': [
            'Musical Notation', 'Rhythm & Meter', 'Scales & Keys',
            'Intervals & Chords', 'Musical Forms', 'African Music',
            'Music History', 'Instruments & Orchestration',
            'Dynamics & Articulation',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Harmony & Counterpoint', 'Sight-Reading & Ear Training',
            'Melody Writing & Composition', 'Chord Progressions & Cadences',
            'Modes & Modal Scales', 'Pentatonic & Blues Scales',
            'Time Signatures & Polyrhythm', 'Texture in Music - Monophony to Polyphony',
            'Song Structure - Verse, Chorus & Bridge',
            'Music & Emotion - Expressive Techniques',
            'World Music Traditions', 'Gospel & Highlife Music',
            'Hip-Hop & Afrobeats - Structure & Culture',
            'Conducting & Score Reading', 'Acoustics & the Physics of Sound',
        ],
        'University / Advanced': [
            'Modulation & Key Changes', 'Jazz Theory & Improvisation',
            'Electronic Music Production Basics', 'Music Technology & DAWs',
            'Chamber Music & Ensemble Playing', 'Opera & Vocal Music',
            'Film Scoring & Music for Media', 'Music Copyright & the Industry',
            'Music Therapy & Wellbeing', 'Ethnomusicology',
            'Advanced Counterpoint', 'Orchestration & Arranging',
            'Music Cognition & Psychology', 'Contemporary Composition',
            'Music Business & Management',
        ],
    },
    'programming': {
        'Primary (Basic 1-6)': [
            'What is a Computer?', 'Using a Mouse & Keyboard',
            'Introduction to Scratch', 'Making Simple Animations in Scratch',
            'Sequences & Instructions', 'Loops in Scratch',
            'Simple Games in Scratch', 'Internet Safety Basics',
        ],
        'JHS (Basic 7-9)': [
            'Introduction to Programming', 'Variables & Data Types',
            'Control Flow', 'Functions & Scope', 'Arrays & Lists',
            'File Handling', 'Debugging & Testing',
            'Web Development Basics', 'Databases & SQL',
            'Algorithms & Complexity',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Object-Oriented Programming', 'Data Structures',
            'Recursion', 'Sorting Algorithms', 'Searching Algorithms',
            'Linked Lists', 'Stacks & Queues', 'Regular Expressions',
            'Error Handling & Exceptions', 'Modules & Packages',
            'Version Control with Git', 'APIs & HTTP Requests',
            'JSON & Data Formats', 'Frontend - HTML & CSS',
            'Frontend - JavaScript Basics', 'Web Scraping',
            'Authentication & Security',
        ],
        'University / Advanced': [
            'Trees & Binary Search Trees', 'Hash Tables & Dictionaries',
            'Graphs & Graph Algorithms', 'Dynamic Programming',
            'Greedy Algorithms', 'React & Component-Based UI',
            'Backend Development with Django/Flask',
            'Cloud Computing Basics', 'Machine Learning Introduction',
            'Ethical Hacking & Cybersecurity Basics',
            'Operating Systems Concepts', 'Computer Networks',
            'Compiler Design Intro', 'Distributed Systems',
            'Artificial Intelligence Fundamentals',
        ],
    },
    'geography': {
        'Primary (Basic 1-6)': [
            'My School & Neighbourhood', 'Simple Maps & Directions',
            'Land & Water Around Us', 'Weather in Our Area',
            'Plants & Animals in Our Environment',
            'People & Their Jobs', 'Our Country on a Map',
        ],
        'JHS (Basic 7-9)': [
            'Map Reading & Scale', 'Latitude & Longitude',
            'Rocks & Minerals', 'Weathering & Erosion',
            'Rivers & Drainage', 'Climate & Weather',
            'Vegetation Zones', 'Population Geography',
            'Agriculture & Land Use', 'West Africa Geography',
            'Environmental Issues',
        ],
        'SHS (Forms 1-3 / WAEC)': [
            'Industry & Trade', 'Plate Tectonics & Earthquakes',
            'Volcanoes & Volcanic Landforms', 'Coastal Landforms & Processes',
            'Desertification & Arid Environments', 'Tropical Rainforests',
            'Savanna & Grassland Ecosystems', 'Soil Formation & Types',
            'Hydrological Cycle & Water Resources', 'Ocean Currents & Climate',
            'Global Warming & Climate Change', 'Urbanisation & City Growth',
            'Rural-Urban Migration', 'Transport Networks & Development',
            'Food Security & Famine', 'Natural Hazards & Disaster Management',
            'Africa - Physical & Human Geography',
        ],
        'University / Advanced': [
            'Glaciation & Ice Landforms', 'El Nino & La Nina',
            'Renewable Energy & Sustainability', 'Tourism Geography',
            'Health Geography & Disease Distribution', 'Water Scarcity & Management',
            'Remote Sensing & GIS', 'Political Geography & Borders',
            'Economic Geography - Global Trade Patterns',
            'Urban Planning & Smart Cities', 'Geopolitics',
            'Climate Modelling & Prediction', 'Biogeography',
            'Cultural Geography', 'Development Geography',
        ],
    },
}

# Flat list for backward compat (used by topic_page slug matching)
SUBJECT_TOPICS = {
    subj: [t for topics in levels.values() for t in topics]
    for subj, levels in SUBJECT_LEVELS.items()
}


class SubjectBook(models.Model):
    """An ebook/PDF uploaded by admin for a subject."""
    subject = models.CharField(max_length=50, choices=SUBJECTS)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True, default='')
    file = models.FileField(upload_to='library/books/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subject', 'title']

    def __str__(self):
        return f"{self.get_subject_display()} — {self.title}"


# Keep old Resource model so existing migration does not break
class Resource(models.Model):
    subject = models.CharField(max_length=50, choices=SUBJECTS)
    topic = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    content = models.TextField()
    source = models.CharField(max_length=255, blank=True, default='Nexa Library')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subject', 'topic', 'title']

    def __str__(self):
        return f"{self.get_subject_display()} — {self.title}"
